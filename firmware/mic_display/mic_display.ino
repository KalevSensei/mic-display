// Mic-stand audio display: Seeed XIAO ESP32C3 + 1.28" round GC9A01 LCD (240 x 240).
// Draws the same dial as companion/index.html from the lines the page sends over USB, and reads the
// Blue Yeti's mute light with an LDR (steady = mic on, blinking = muted).
//
// Arduino IDE: board "XIAO_ESP32C3", USB CDC On Boot: Enabled.
// Library: "GFX Library for Arduino" (moononournation, Arduino_GFX).
// Wiring: docs/WIRING.md.
//
// Protocol, page -> display, one line per frame (20 per second):
//   S,<level dB x10>,<peak dB x10>,<clip 0|1>,<rec 0|1|2>,<sample rate Hz>,<device name>\n
// Protocol, display -> page, every 200 ms:
//   M,<0 no reading | 1 mic on | 2 muted>,<raw light 0-4095>\n

#include <Arduino_GFX_Library.h>
#include <math.h>

// ---- pins (XIAO ESP32C3 labels) ----
#define PIN_SCK  D8
#define PIN_MOSI D10
#define PIN_CS   D3
#define PIN_DC   D2
#define PIN_RST  D0
#define PIN_LDR  D1

Arduino_DataBus *bus = new Arduino_ESP32SPI(PIN_DC, PIN_CS, PIN_SCK, PIN_MOSI, GFX_NOT_DEFINED);
Arduino_GFX *panel = new Arduino_GC9A01(bus, PIN_RST, 0 /* rotation */, true /* IPS */);
Arduino_Canvas *gfx = new Arduino_Canvas(240, 240, panel);   // draw off-screen, push once: no flicker

// ---- dial design, identical to the companion page ----
const float MIN_DB = -60, MAX_DB = 0, A0 = 150, A1 = 390;
const int C = 120;
uint16_t rgb(uint8_t r, uint8_t g, uint8_t b) { return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3); }
const uint16_t BG = 0x0000, TEXT = rgb(0xf2, 0xf4, 0xf7), DIM = rgb(0x7d, 0x87, 0x94), NEEDLE = 0xFFFF;
const uint16_t GREEN = rgb(0x2e, 0xcc, 0x71), AMBER = rgb(0xf5, 0xb3, 0x01), RED = rgb(0xff, 0x3b, 0x30);
const uint16_t GREEN_D = rgb(0x16, 0x50, 0x2f), AMBER_D = rgb(0x5a, 0x43, 0x00), RED_D = rgb(0x5c, 0x16, 0x12);

float dbToDeg(float db) {
  float t = (constrain(db, MIN_DB, MAX_DB) - MIN_DB) / (MAX_DB - MIN_DB);
  return A0 + t * (A1 - A0);
}
// Arduino_GFX arcs run 0..360 degrees, clockwise from 3 o'clock (same as the canvas page); split across 360.
void arcDeg(float from, float to, int r1, int r2, uint16_t col) {
  if (to <= from) return;
  if (to <= 360) { gfx->fillArc(C, C, r1, r2, from, to, col); return; }
  if (from < 360) gfx->fillArc(C, C, r1, r2, from, 360, col);
  gfx->fillArc(C, C, r1, r2, max(from, 360.0f) - 360, to - 360, col);
}
void zone(float fromDb, float toDb, uint16_t col) { arcDeg(dbToDeg(fromDb), dbToDeg(toDb), 105, 95, col); }
void centered(const char *s, int y, uint8_t size, uint16_t col) {
  int16_t x1, y1; uint16_t w, h;
  gfx->setTextSize(size); gfx->getTextBounds(s, 0, 0, &x1, &y1, &w, &h);
  gfx->setTextColor(col); gfx->setCursor(C - w / 2, y - h / 2); gfx->print(s);
}

// ---- state from the page ----
float level = MIN_DB, peak = MIN_DB;
int clip = 0, rec = 0;
long rate = 0;
char name[24] = "";
uint32_t lastFrame = 0;   // millis() of the last S line
int mute = 0;              // from the light sensor

void draw() {
  gfx->fillScreen(BG);
  bool live = lastFrame && millis() - lastFrame < 2000;
  if (clip && live) for (int r = 113; r <= 118; r++) gfx->drawCircle(C, C, r, RED);
  if (!live) { centered("waiting for PC", C, 2, DIM); gfx->flush(); return; }

  zone(-60, -18, GREEN_D); zone(-18, -6, AMBER_D); zone(-6, 0, RED_D);
  if (level > -60) zone(-60, min(level, -18.0f), GREEN);
  if (level > -18) zone(-18, min(level, -6.0f), AMBER);
  if (level > -6) zone(-6, min(level, 0.0f), RED);

  const int ticks[] = {-60, -48, -36, -24, -18, -12, -6, 0};
  for (int db : ticks) {
    float a = dbToDeg(db) * DEG_TO_RAD;
    gfx->drawLine(C + cos(a) * 88, C + sin(a) * 88, C + cos(a) * 81, C + sin(a) * 81, DIM);
    if (db != -18) { char t[5]; snprintf(t, sizeof t, "%d", db); gfx->setTextSize(1); gfx->setTextColor(DIM);
      int16_t x1, y1; uint16_t w, h; gfx->getTextBounds(t, 0, 0, &x1, &y1, &w, &h);
      gfx->setCursor(C + cos(a) * 70 - w / 2, C + sin(a) * 70 - h / 2); gfx->print(t); }
  }
  if (peak > MIN_DB) { float a = dbToDeg(peak) * DEG_TO_RAD; gfx->fillCircle(C + cos(a) * 100, C + sin(a) * 100, 4, peak > -6 ? RED : TEXT); }

  float a = dbToDeg(level) * DEG_TO_RAD;
  for (int o = -1; o <= 1; o++)   // 3 px needle
    gfx->drawLine(C - cos(a) * 10 + o * sin(a), C - sin(a) * 10 - o * cos(a), C + cos(a) * 92 + o * sin(a), C + sin(a) * 92 - o * cos(a), NEEDLE);
  gfx->fillCircle(C, C, 6, NEEDLE);

  char t[12];
  if (level <= MIN_DB) strcpy(t, "-inf"); else snprintf(t, sizeof t, "%d", (int)lroundf(level));
  centered(t, C + 44, 3, TEXT);
  centered("dBFS", C + 64, 1, DIM);

  if (mute == 2) centered("MUTED", 52, 2, RED);
  else if (rec) centered(rec == 2 ? "LIVE" : "REC", 52, 2, RED);
  else if (mute == 1) centered("MIC ON", 52, 2, GREEN);

  if (rate) { snprintf(t, sizeof t, rate % 1000 ? "%.1f kHz" : "%.0f kHz", rate / 1000.0); centered(t, 196, 1, DIM); }
  centered(name, 211, 1, DIM);
  gfx->flush();
}

// ---- serial input ----
char line[96]; int len = 0;
void parseLine() {
  line[len] = 0; len = 0;
  if (line[0] != 'S' || line[1] != ',') return;
  char *p = line + 2; char *f[6]; int n = 0;
  f[n++] = p;
  while (*p && n < 6) { if (*p == ',') { *p = 0; f[n++] = p + 1; } p++; }
  if (n < 6) return;
  level = atoi(f[0]) / 10.0; peak = atoi(f[1]) / 10.0; clip = atoi(f[2]); rec = atoi(f[3]); rate = atol(f[4]);
  strncpy(name, f[5], sizeof name - 1); name[sizeof name - 1] = 0;
  lastFrame = millis();
}

// ---- mute light: steady bright = mic on, blinking = muted, steady dark = no reading ----
const int ON_LEVEL = 1200;    // raw reading that counts as "LED lit"; tune once on the real Yeti (M04)
const int MIN_SWING = 300;    // light swing that counts as blinking
int samples[75]; int si = 0;  // 75 x 20 ms = 1.5 s window
void readLight() {
  samples[si] = analogRead(PIN_LDR); si = (si + 1) % 75;
  int lo = 4095, hi = 0; long sum = 0;
  for (int v : samples) { lo = min(lo, v); hi = max(hi, v); sum += v; }
  int mid = (lo + hi) / 2, crossings = 0; bool above = samples[0] > mid;
  for (int i = 1; i < 75; i++) { bool b = samples[(si + i) % 75] > mid; if (b != above) { crossings++; above = b; } }
  if (hi - lo > MIN_SWING && crossings >= 2) mute = 2;
  else if (sum / 75 > ON_LEVEL) mute = 1;
  else mute = 0;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  gfx->begin(40000000);
  draw();
}

uint32_t lastLight = 0, lastReport = 0, lastDraw = 0;
void loop() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') parseLine();
    else if (ch != '\r' && len < (int)sizeof line - 1) line[len++] = ch;
  }
  uint32_t now = millis();
  if (now - lastLight >= 20) { lastLight = now; readLight(); }
  if (now - lastReport >= 200) { lastReport = now; Serial.printf("M,%d,%d\n", mute, samples[(si + 74) % 75]); }
  if (now - lastDraw >= 40) { lastDraw = now; draw(); }   // 25 frames a second
}
