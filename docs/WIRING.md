# Wiring

## Upgraded build (Waveshare 1.75" AMOLED board)
Nothing to wire: board and screen are one piece. One USB-C cable to the PC powers it and carries the data.

## Basic build (XIAO ESP32C3 + 1.28" round GC9A01)
Board pins are named D0–D10, 3V3, GND, 5V. Display pins are usually labelled VCC, GND, SCL, SDA, DC, CS, RST (some modules also have BL). Every wire is under 10 cm.

| Display pin | Board pin | What it is |
|-------------|-----------|------------|
| VCC | 3V3 | power for the display |
| GND | GND | ground |
| SCL | D8 | SPI clock |
| SDA | D10 | SPI data (MOSI) |
| CS | D3 | chip select |
| DC | D2 | data / command |
| RST | D0 | reset |
| BL (only if the module has it) | 3V3 | backlight always on |

Power: only the USB-C cable to the PC (5 V in, the board's 3.3 V feeds the display).

Arduino IDE settings for upload: board "XIAO_ESP32C3", "USB CDC On Boot: Enabled" (so the page can talk over the USB cable).
