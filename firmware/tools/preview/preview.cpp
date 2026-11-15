// Renders every face and settings screen with the firmware's own drawing code (firmware/mic_display/ui.h),
// compiled on the PC. Writes one 466 x 466 PPM per screen into the folder given as the first argument, plus
// list.txt (file name and caption per line). firmware/tools/previews.py builds this, runs it and makes the PNGs.
#include <stdio.h>
#include <stdlib.h>
#include "../../mic_display/ui.h"

using namespace md;

static FILE *listFile;
static const char *outDir;

static void shot(const char *file, const char *caption, uint32_t now) {
  render(now);
  char path[512];
  snprintf(path, sizeof path, "%s/%s.ppm", outDir, file);
  FILE *f = fopen(path, "wb");
  fprintf(f, "P6\n%d %d\n255\n", W, H);
  for (int i = 0; i < W * H; i++) {   // RGB565 -> RGB888 the way the panel shows it (top bits repeated)
    uint16_t p = fb[i];
    uint8_t r = (p >> 11) & 31, g = (p >> 5) & 63, b = p & 31;
    uint8_t px[3] = {(uint8_t)(r << 3 | r >> 2), (uint8_t)(g << 2 | g >> 4), (uint8_t)(b << 3 | b >> 2)};
    fwrite(px, 1, 3, f);
  }
  fclose(f);
  fprintf(listFile, "%s\t%s\n", file, caption);
}

static void feed(const char *line, uint32_t now) { char b[600]; snprintf(b, sizeof b, "%s", line); onLine(b, now); }

// A believable moment of speech: the same values the companion page's demo signal produces.
static void speech(uint32_t now) {
  feed("S,-142,-38,0,0,48000,Yeti Stereo Microphone", now - 3000);   // starts the no-signal clock
  feed("S,-142,-38,0,0,48000,Yeti Stereo Microphone", now - 1500);
  feed("S,-142,-38,0,0,48000,Yeti Stereo Microphone", now - 400);
  feed("S,-137,-52,0,0,48000,Yeti Stereo Microphone", now - 20);
  feed("F,32,22,31,44,58,66,71,74,72,69,70,73,76,74,68,63,61,64,66,60,54,49,47,44,40,36,33,29,25,21,17,12,8", now - 10);
  feed("L,-184,-201,1694,2712", now - 10);
  feed("T,1794750720,120", now - 10);   // 2026-11-15 13:52:00 UTC, shown as 15:52 at UTC+2 (Finland in winter)
}
static void pcApp(uint32_t now) {
  feed("H,PC app,2", now);
  feed("P,0,62,0,3,Yeti Stereo Microphone,Webcam C920,Realtek Mic Array", now);
  feed("O,0,38,1,2,Realtek Speakers,Headphones (Yeti Stereo Microphone)", now);
}
static void pageOnly(uint32_t now) {   // the companion page answers only what a browser can: its own input choice
  feed("H,Companion page,2", now);
  feed("P,-,-,0,3,Yeti Stereo Microphone,Webcam C920,Realtek Mic Array", now);
}
static void reset() {
  pin = PcSide(); pout = PcSide(); clientAt = 0; client[0] = 0;
  lastFrame = 0; loudAt = 0; heldPeak = MIN_DB; clip = 0; clipCount = 0; level = MIN_DB; nBands = 0; bandsAt = 0;
  loudnessAt = 0; clockValid = false; inSettings = false; pressed = Z_NONE; resetDoneAt = 0;
  set = Settings();
}

int main(int argc, char **argv) {
  if (argc < 2) { fprintf(stderr, "usage: preview <out dir>\n"); return 1; }
  outDir = argv[1];
  fb = (uint16_t *)malloc(W * H * 2);
  char lp[512];
  snprintf(lp, sizeof lp, "%s/list.txt", outDir);
  listFile = fopen(lp, "w");
  const uint32_t T = 600000;   // ten minutes after start-up

  // ---- faces (swipe left/right on the main screen); page dots show for 3 s after a swipe
  reset(); speech(T); clipCount = 2;
  heldPeak = -3.8f; clip = 0;
  for (int f = 0; f < FACE_COUNT; f++) {
    set.face = f; faceShownAt = T;
    static const char *const FILES[] = {"f1_dial", "f2_bars", "f3_loudness", "f4_talk_time", "f5_clock"};
    static const char *const CAPS[] = {"Face 1 · Needle dial", "Face 2 · Frequency bars", "Face 3 · Loudness", "Face 4 · Talk time", "Face 5 · Clock"};
    shot(FILES[f], CAPS[f], T);
  }
  set.face = FACE_DIAL; faceShownAt = 0;
  feed("S,-31,-2,1,0,48000,Yeti Stereo Microphone", T); clipCount = 3;
  shot("f1_dial_clipping", "Needle dial · clipping, dots hidden", T);
  reset();
  shot("f0_waiting_for_pc", "Any face · no PC sending", T);

  // ---- settings app: tap a face to open; swipe left/right between settings; Done / swipe down / 10 s closes
  static const char *const SF[IT_COUNT] = {"s01_mic_mute", "s02_input_device", "s03_input_volume", "s04_output_device", "s05_pc_volume",
                                           "s06_output_mute", "s07_brightness", "s08_screen_sleep", "s09_peak_hold", "s10_reset", "s11_about"};
  for (int it = 0; it < IT_COUNT; it++) {
    bool pc = it <= IT_OUT_MUTE || it == IT_ABOUT;
    char file[64], cap[96];
    reset(); speech(T); pcApp(T); clipCount = 4; heldPeak = -3.2f;
    inSettings = true; item = it;
    snprintf(file, sizeof file, "%s%s", SF[it], pc ? "_pc_app" : "");
    snprintf(cap, sizeof cap, "%d · %s%s", it + 1, TITLE[it], pc ? " · PC app connected" : "");
    shot(file, cap, T);
    if (it == IT_MIC_MUTE || it == IT_OUT_MUTE) {
      (it == IT_MIC_MUTE ? pin : pout).mute = 1;
      snprintf(file, sizeof file, "%s_pc_app_muted", SF[it]);
      snprintf(cap, sizeof cap, "%d · %s · muted", it + 1, TITLE[it]);
      shot(file, cap, T);
    }
    if (pc) {
      reset(); speech(T); pageOnly(T);
      inSettings = true; item = it;
      snprintf(file, sizeof file, "%s_no_pc_app", SF[it]);
      snprintf(cap, sizeof cap, "%d · %s · companion page only", it + 1, TITLE[it]);
      shot(file, cap, T);
    }
    if (it == IT_RESET) {
      resetDoneAt = T - 300; heldPeak = MIN_DB; clipCount = 0;
      shot("s10_reset_cleared", "10 · Reset · just cleared", T);
    }
  }
  fclose(listFile);
  return 0;
}
