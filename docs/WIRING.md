# Wiring

Board: Seeed XIAO ESP32C3 (pins named on the board as D0–D10, 3V3, GND, 5V). Display: 1.28" round GC9A01 module (pins usually labelled VCC, GND, SCL, SDA, DC, CS, RST; some modules also have BL). Every wire is short (under 10 cm) except the light-sensor pair, which runs to the cup over the Yeti's LED (about 30–40 cm).

## Display → board
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

## Light sensor (mute light) → board
A voltage divider: more light on the LDR gives a higher voltage on D1.

- LDR leg 1 → 3V3
- LDR leg 2 → D1, and also → one leg of the 10 kΩ resistor
- 10 kΩ resistor other leg → GND

Solder the 10 kΩ at the board end; only two wires (3V3 and D1) run up to the cup. Heat-shrink both LDR legs so they can never touch.

## Power
Only the USB-C cable to the PC. It powers the board (5 V in, 3.3 V out to the display and the sensor) and carries the data both ways.

## Notes
- D8 (GPIO8) and D9 (GPIO9) are boot pins; D9 is left free, and D8 is the board's own SPI clock, which is fine.
- Arduino IDE settings for upload: board "XIAO_ESP32C3", "USB CDC On Boot: Enabled" (so the page can talk over the USB cable).
