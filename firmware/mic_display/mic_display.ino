// Mic-stand audio display: Waveshare ESP32-S3-Touch-AMOLED-1.75 (466 x 466 round AMOLED, CO5300 over QSPI,
// CST9217 capacitive touch on I2C).
// Shows only what the PC can read (owner, 2026-11-14: no light sensor). Main screen: five watch faces (swipe
// left/right): needle dial, frequency bars, loudness, talk time, clock. A tap opens the settings app (swipe
// left/right between settings; Done, a swipe down or 10 s without touch goes back).
// This file is the hardware: screen, touch, USB serial, flash. Everything drawn and every gesture is in ui.h,
// which firmware/tools/previews.py also compiles on the PC to render docs/previews/settings/.
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
#include "TouchDrvCSTXXX.hpp"
#include "ui.h"

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
void setBrightness(uint8_t pct) {   // 0 = screen off (asleep); 10..100 % of the panel's 0..255
  panel->setBrightness(pct ? (uint8_t)(pct * 255 / 100) : 0);
}
void sendLine(const char *s) {   // board -> PC; dropped (never blocks) when no PC has the port open
  if (!Serial) return;
  size_t n = strlen(s);
  if (Serial.availableForWrite() < (int)n + 1) return;
  Serial.write((const uint8_t *)s, n);
  Serial.write('\n');
}

void setup() {
  Serial.setRxBufferSize(2048);   // a frame push takes ~30 ms; lines wait here meanwhile
  Serial.setTxTimeoutMs(0);
  Serial.begin(115200);
  if (!panel->begin()) Serial.println("display init failed");
  panel->fillScreen(RGB565_BLACK);
  loadSettings();
  setBrightness(md::set.brightness);
  md::fb = (uint16_t *)heap_caps_malloc(md::W * md::H * 2, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
  if (!md::fb) {   // PSRAM switched off in the build settings: say so on the screen
    panel->setTextColor(RGB565_RED); panel->setTextSize(3);
    panel->setCursor(90, 200); panel->print("PSRAM is off.");
    panel->setCursor(90, 240); panel->print("Build with");
    panel->setCursor(90, 280); panel->print("OPI PSRAM.");
    for (;;) delay(1000);
  }
  touch.setPins(TP_RESET, TP_INT);
  touchOk = touch.begin(Wire, CST92XX_SLAVE_ADDRESS, IIC_SDA, IIC_SCL);
  if (touchOk) {
    touch.setMaxCoordinates(LCD_WIDTH, LCD_HEIGHT);
    touch.setMirrorXY(true, true);
    pinMode(TP_INT, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(TP_INT), onTouchIrq, FALLING);
  } else Serial.println("touch init failed: the faces still work, the settings app cannot open");
  md::sendLine = sendLine;
  md::onBrightness = setBrightness;
  md::onSave = saveSettings;
  md::begin(millis());
  md::render(millis());
  panel->draw16bitRGBBitmap(0, 0, md::fb, md::W, md::H);
}

// ---- touch: read while the controller signals or a finger is down; up = no report for 120 ms ----
bool fingerDown = false;
uint32_t lastPoint = 0, lastPoll = 0;
void pollTouch(uint32_t now) {
  if (!touchOk) return;
  noInterrupts();
  bool irq = touchIrq;
  touchIrq = false;
  interrupts();
  if (irq || (fingerDown && now - lastPoll >= 15)) {
    lastPoll = now;
    int16_t x[2], y[2];
    if (touch.getPoint(x, y, 1)) {
      lastPoint = now;
      if (!fingerDown) { fingerDown = true; md::touchDown(x[0], y[0], now); }
      else md::touchMove(x[0], y[0], now);
    }
  }
  if (fingerDown && now - lastPoint > 120) { fingerDown = false; md::touchUp(now); }
}

// ---- serial input ----
char lineBuf[600];
int len = 0;
uint32_t lastDraw = 0;
void loop() {
  uint32_t now = millis();
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') { lineBuf[len] = 0; md::onLine(lineBuf, now); len = 0; }
    else if (ch != '\r' && len < (int)sizeof lineBuf - 1) lineBuf[len++] = ch;
  }
  pollTouch(now);
  md::tick(now);
  if (md::asleep) { delay(5); return; }
  // redraw on news (at most 25 a second), and twice a second otherwise for timeouts and the clock
  if ((md::dirty && now - lastDraw >= 40) || now - lastDraw >= 500) {
    lastDraw = now; md::dirty = false;
    md::render(now);
    panel->draw16bitRGBBitmap(0, 0, md::fb, md::W, md::H);
  }
}
