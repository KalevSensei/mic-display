// Mic-stand audio display: Waveshare ESP32-S3-Touch-AMOLED-1.75 (466 x 466 round AMOLED, CO5300 over QSPI,
// CST9217 capacitive touch on I2C).
// Shows only what the PC can read (owner, 2026-11-14: no light sensor). Main screen: eight watch faces; the page
// follows the finger left/right and settles with easing (dial, rings, big number, modular, frequency bars,
// loudness, talk time, clock). A tap opens the settings app (pages the same way; Done, a swipe down or 10 s
// without touch goes back).
// This file is the hardware: screen, touch, USB serial, flash, and the frame pipeline. Everything drawn and
// every gesture is in ui.h, which firmware/tools/previews.py also compiles on the PC to render
// docs/previews/settings/.
//
// Frame pipeline (2026-11-19, owner: "is it possible to make kmore responsive"). Until 0.2.0 the whole
// 466 x 466 picture was drawn into PSRAM and all 434 KB sent over QSPI on every redraw, at most 25 a second.
// Now, per frame:
//   1. ui.h eases the needle, peak, bars and the page towards their targets (md::animate),
//   2. this core (the Arduino loop, core 1) draws the screen in 8 bands of 60 rows, alternately into two
//      small buffers in internal RAM (no PSRAM),
//   3. each row gets a 32-bit hash; only rows whose hash changed since the last frame are sent, as full-width
//      runs that start on an even row and have an even height (the CO5300 window is set per run),
//   4. a task on the other core (core 0) sends band k over QSPI while this core draws band k+1.
// Frames run up to 60 a second while something moves (needle, page, settling), on news otherwise, and twice
// a second at rest (clock, timeouts). Every 5 s the board sends C,perf,<render_ms>,<push_ms>,<fps>,<rows>
// (docs/PROTOCOL.md), so the real numbers can be read on the PC.
// QSPI clock: 40 MHz, the default of Waveshare's GFX copy (ESP32QSPI_FREQUENCY in
// examples/arduino/libraries/GFX_Library_for_Arduino/src/databus/Arduino_ESP32QSPI.h), which their Arduino
// demos use. Not raised by default: the board's display pins (GPIO 4-7, 12, 38) are not the ESP32-S3's SPI2
// IO_MUX pins, so the signals go through the GPIO matrix, and Espressif only states that GPIO-matrix routing
// behaves like IO_MUX at 40 MHz or lower (ESP-IDF SPI master guide, ESP32-S3,
// https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/spi_master.html).
// To try 80 MHz on the real board, build with -DMD_QSPI_HZ=80000000 and watch for a garbled picture.
//
// Sources for the pins, the display and touch start-up and the toolchain (read 2026-11-15):
//   Waveshare wiki:   https://www.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-1.75
//   Waveshare demos:  https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75
//     examples/arduino/01_HelloWorld/01_HelloWorld.ino           display init (Arduino_ESP32QSPI + Arduino_CO5300)
//     examples/arduino/10_Touch_CST9217/10_Touch_CST9217.ino     touch init (SensorLib TouchDrvCST92xx, address 0x5A)
//     examples/arduino/06_LVGL_Widgets/06_LVGL_Widgets.ino       touch to screen mapping: 466 x 466, X and Y mirrored
//     examples/arduino/libraries/Mylibrary/pin_config.h           pins below
//     docs/getting-started.md, HARDWARE_REFERENCE.md              core 3.3.10, 16 MB flash, app3M_fat9M_16MB,
//                                                                 ESP32-S3R8 (8 MB octal PSRAM), no backlight pin
// The display needs no power-chip step: Waveshare's display demos never touch the AXP2101 (its default rails
// power the panel), so this sketch does not either.
//
// Build (docs/PLAN.md M03 has the beginner steps):
//   esp32 core 3.3.10 (Espressif), board "ESP32S3 Dev Module", Flash Size 16MB, Partition Scheme
//   "16M Flash (3MB APP/9.9MB FATFS)", PSRAM "OPI PSRAM", USB CDC On Boot "Enabled".
//   Libraries, both Waveshare's bundled copies from examples/arduino/libraries in Waveshare's repository:
//     "GFX Library for Arduino" 1.6.4 (moononournation; Waveshare's copy is patched for core 3.3.10)
//     "SensorLib" 0.3.1 (Lewis He; the CST9217 touch driver)
//   arduino-cli FQBN: esp32:esp32:esp32s3:FlashSize=16M,PartitionScheme=app3M_fat9M_16MB,PSRAM=opi,CDCOnBoot=cdc
//
// Protocol (115200 baud, one text line per message, both directions): docs/PROTOCOL.md. The S line from the
// PC is unchanged from the first firmware; everything else is additive.

#include <Arduino_GFX_Library.h>
#include <Wire.h>
#include <Preferences.h>
#include <esp_heap_caps.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>
#include "TouchDrvCSTXXX.hpp"
#include "ui.h"

#ifndef MD_QSPI_HZ
#define MD_QSPI_HZ 40000000
#endif

// ---- pins (Waveshare pin_config.h) ----
#define LCD_SDIO0 4
#define LCD_SDIO1 5
#define LCD_SDIO2 6
#define LCD_SDIO3 7
#define LCD_SCLK 38
#define LCD_CS 12
#define LCD_RESET 39
#define LCD_WIDTH 466
#define LCD_HEIGHT 466
#define IIC_SDA 15
#define IIC_SCL 14
#define TP_INT 11
#define TP_RESET 40

// ---- display init, as in Waveshare's 01_HelloWorld ----
Arduino_DataBus *bus = new Arduino_ESP32QSPI(LCD_CS, LCD_SCLK, LCD_SDIO0, LCD_SDIO1, LCD_SDIO2, LCD_SDIO3);
Arduino_CO5300 *panel = new Arduino_CO5300(bus, LCD_RESET, 0 /* rotation */, LCD_WIDTH, LCD_HEIGHT, 6, 0, 0, 0);

// ---- touch, as in Waveshare's 10_Touch_CST9217 ----
TouchDrvCST92xx touch;
bool touchOk = false;
volatile bool touchIrq = false;
void IRAM_ATTR onTouchIrq() { touchIrq = true; }

// ---- frame pipeline: two band buffers in internal RAM, a push task on core 0 ----
const int STRIP_H = 60;                                     // rows per band (even: runs start on even rows)
const int NSTRIP = (LCD_HEIGHT + STRIP_H - 1) / STRIP_H;    // 8
const int MAX_RUNS = 8;
uint16_t *band[2];
uint32_t rowHash[LCD_HEIGHT];
bool forceFull = true;                                      // first frame: send every row
struct Job { uint8_t kind, buf, n, bright; uint16_t y0; uint16_t ry[MAX_RUNS], rh[MAX_RUNS]; };   // kind 0 = rows, 1 = brightness
QueueHandle_t jobs;
SemaphoreHandle_t bufFree[2];
volatile uint32_t pushUs = 0, pushRows = 0;

void pushTask(void *) {   // the only user of the display bus once the loop runs
  Job j;
  for (;;) {
    xQueueReceive(jobs, &j, portMAX_DELAY);
    if (j.kind == 1) { panel->setBrightness(j.bright); continue; }
    uint32_t t0 = micros(), rows = 0;
    for (int i = 0; i < j.n; i++) {
      panel->draw16bitRGBBitmap(0, j.ry[i], band[j.buf] + (j.ry[i] - j.y0) * LCD_WIDTH, LCD_WIDTH, j.rh[i]);
      rows += j.rh[i];
    }
    pushUs += micros() - t0; pushRows += rows;
    xSemaphoreGive(bufFree[j.buf]);
  }
}

// ---- settings saved in flash (NVS), survive unplugging ----
Preferences prefs;
void loadSettings() {
  prefs.begin("micdisp", true);
  md::set.face = prefs.getUChar("face", md::FACE_DIAL);
  md::set.brightness = prefs.getUChar("bright", 80);
  md::set.sleepIdx = prefs.getUChar("sleep", 2);
  md::set.peakIdx = prefs.getUChar("peak", 1);
  prefs.end();
  if (md::set.face >= md::FACE_COUNT) md::set.face = md::FACE_DIAL;
  if (md::set.brightness < 10 || md::set.brightness > 100) md::set.brightness = 80;
  if (md::set.sleepIdx > 3) md::set.sleepIdx = 2;
  if (md::set.peakIdx > 2) md::set.peakIdx = 1;
}
void saveSettings() {   // only writes what changed (Preferences skips equal values)
  prefs.begin("micdisp", false);
  prefs.putUChar("face", md::set.face);
  prefs.putUChar("bright", md::set.brightness);
  prefs.putUChar("sleep", md::set.sleepIdx);
  prefs.putUChar("peak", md::set.peakIdx);
  prefs.end();
}
uint8_t panelLevel(uint8_t pct) { return pct ? (uint8_t)(pct * 255 / 100) : 0; }   // 0 = screen off (asleep); 10..100 % of 0..255
void setBrightness(uint8_t pct) {   // queued, so only the push task touches the display bus
  Job j = {};
  j.kind = 1; j.bright = panelLevel(pct);
  xQueueSend(jobs, &j, portMAX_DELAY);
}
void sendLine(const char *s) {   // board -> PC; dropped (never blocks) when no PC has the port open
  if (!Serial) return;
  size_t n = strlen(s);
  if (Serial.availableForWrite() < (int)n + 1) return;
  Serial.write((const uint8_t *)s, n);
  Serial.write('\n');
}
void halt(const char *l1, const char *l2) {   // something the firmware cannot run without: say so on the screen
  panel->setTextColor(RGB565_RED); panel->setTextSize(3);
  panel->setCursor(90, 210); panel->print(l1);
  panel->setCursor(90, 250); panel->print(l2);
  for (;;) delay(1000);
}

void setup() {
  Serial.setRxBufferSize(2048);   // lines wait here while a frame is drawn
  Serial.setTxTimeoutMs(0);
  Serial.begin(115200);
  if (!panel->begin(MD_QSPI_HZ)) Serial.println("display init failed");
  panel->fillScreen(RGB565_BLACK);
  loadSettings();
  panel->setBrightness(panelLevel(md::set.brightness));
  for (int b = 0; b < 2; b++) {
    band[b] = (uint16_t *)heap_caps_malloc(LCD_WIDTH * STRIP_H * 2, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
    if (!band[b]) halt("Not enough RAM", "for the frame.");
    bufFree[b] = xSemaphoreCreateBinary();
    xSemaphoreGive(bufFree[b]);
  }
  jobs = xQueueCreate(6, sizeof(Job));
  touch.setPins(TP_RESET, TP_INT);
  touchOk = touch.begin(Wire, CST92XX_SLAVE_ADDRESS, IIC_SDA, IIC_SCL);
  if (touchOk) {
    touch.setMaxCoordinates(LCD_WIDTH, LCD_HEIGHT);
    touch.setMirrorXY(true, true);
    pinMode(TP_INT, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(TP_INT), onTouchIrq, FALLING);
  } else Serial.println("touch init failed: the faces still work, the settings app cannot open");
  xTaskCreatePinnedToCore(pushTask, "push", 4096, nullptr, 2, nullptr, 0);   // core 0 is free: no Wi-Fi in use
  md::sendLine = sendLine;
  md::onBrightness = setBrightness;
  md::onSave = saveSettings;
  md::begin(millis());
}

// ---- touch: read while the controller signals or a finger is down. The CST9217 sends a last report with no
// finger when it is lifted (SensorLib's getPoint returns 0 for it, TouchDrvCST92xx.cpp "Release finger"): that
// ends the touch 25 ms later unless a point follows; without it, 120 ms with no report counts as lifted. ----
bool fingerDown = false, liftSeen = false;
uint32_t lastPoint = 0, lastPoll = 0, liftAt = 0;
void pollTouch(uint32_t now) {
  if (!touchOk) return;
  noInterrupts();
  bool irq = touchIrq;
  touchIrq = false;
  interrupts();
  if (irq || (fingerDown && now - lastPoll >= 10)) {
    lastPoll = now;
    int16_t x[2], y[2];
    if (touch.getPoint(x, y, 1)) {
      lastPoint = now; liftSeen = false;
      if (!fingerDown) { fingerDown = true; md::touchDown(x[0], y[0], now); }
      else md::touchMove(x[0], y[0], now);
    } else if (irq && fingerDown && !liftSeen) { liftSeen = true; liftAt = now; }
  }
  if (fingerDown && ((liftSeen && now - liftAt >= 25) || now - lastPoint > 120)) { fingerDown = false; liftSeen = false; md::touchUp(now); }
}

// ---- one frame ----
static inline uint32_t hashRow(const uint16_t *p) {   // FNV-1a over the row's 233 32-bit words
  const uint32_t *w = (const uint32_t *)p;
  uint32_t h = 2166136261u;
  for (int i = 0; i < LCD_WIDTH / 2; i++) h = (h ^ w[i]) * 16777619u;
  return h;
}
uint32_t renderUs = 0, frames = 0;
void drawFrame(uint32_t now) {
  uint32_t t = micros();
  md::animate(now);
  uint32_t busy = micros() - t;
  for (int s = 0; s < NSTRIP; s++) {
    int y0 = s * STRIP_H, y1 = y0 + STRIP_H > LCD_HEIGHT ? LCD_HEIGHT : y0 + STRIP_H, b = s & 1;
    xSemaphoreTake(bufFree[b], portMAX_DELAY);   // wait until core 0 has sent what was in this buffer
    t = micros();
    md::renderBand(now, y0, y1, band[b]);
    Job j = {};
    j.kind = 0; j.buf = b; j.y0 = y0;
    auto addRun = [&](int a, int e) {
      if (j.n > 0 && a - (j.ry[j.n - 1] + j.rh[j.n - 1]) <= 4) { j.rh[j.n - 1] = e - j.ry[j.n - 1]; return; }   // close runs merge
      if (j.n == MAX_RUNS) { j.rh[j.n - 1] = e - j.ry[j.n - 1]; return; }
      j.ry[j.n] = a; j.rh[j.n] = e - a; j.n++;
    };
    int start = -1;
    for (int y = y0; y < y1; y += 2) {   // row pairs: every run starts on an even row and has an even height
      const uint16_t *r = band[b] + (y - y0) * LCD_WIDTH;
      uint32_t h1 = hashRow(r), h2 = hashRow(r + LCD_WIDTH);
      bool changed = forceFull || h1 != rowHash[y] || h2 != rowHash[y + 1];
      rowHash[y] = h1; rowHash[y + 1] = h2;
      if (changed && start < 0) start = y;
      if (!changed && start >= 0) { addRun(start, y); start = -1; }
    }
    if (start >= 0) addRun(start, y1);
    busy += micros() - t;
    if (j.n) xQueueSend(jobs, &j, portMAX_DELAY); else xSemaphoreGive(bufFree[b]);
  }
  forceFull = false;
  renderUs += busy; frames++;
}

// ---- serial input, frames, the perf line ----
char lineBuf[600];
int len = 0;
uint32_t lastDraw = 0, perfAt = 0;
const uint32_t FRAME_MS = 16;   // at most about 60 frames a second, the panel's own refresh rate
void reportPerf(uint32_t now) {   // C,perf,<render ms per frame>,<push ms per frame>,<frames per second>,<rows sent per frame>
  float secs = (now - perfAt) / 1000.0f;
  uint32_t pu = pushUs, pr = pushRows;
  pushUs = 0; pushRows = 0;
  char t[80];
  if (frames) snprintf(t, sizeof t, "C,perf,%.1f,%.1f,%.1f,%lu", renderUs / 1000.0f / frames, pu / 1000.0f / frames, frames / secs,
                       (unsigned long)(pr / frames));
  else snprintf(t, sizeof t, "C,perf,-,-,0.0,0");
  sendLine(t);
  renderUs = 0; frames = 0; perfAt = now;
}
void loop() {
  uint32_t now = millis();
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') { lineBuf[len] = 0; md::onLine(lineBuf, now); len = 0; }
    else if (ch != '\r' && len < (int)sizeof lineBuf - 1) lineBuf[len++] = ch;
  }
  pollTouch(now);
  md::tick(now);
  if (now - perfAt >= 5000) reportPerf(now);
  if (md::asleep) { delay(5); return; }
  bool moving = md::animating(now);
  if (((md::dirty || moving) && now - lastDraw >= FRAME_MS) || now - lastDraw >= 500) {
    lastDraw = now; md::dirty = false;
    drawFrame(now);
  } else delay(1);
}
