"""Render docs/previews/settings/: every watch face and settings screen, drawn by the firmware's own code.

firmware/mic_display/ui.h holds all the drawing; firmware/tools/preview/preview.cpp feeds it example
lines (the same lines the PC sends) and writes one picture per screen. This script compiles that on the PC
with Zig's C++ compiler, runs it, and saves:
  - one 466 x 466 PNG per screen (exactly the pixels the board draws; outside the round glass transparent),
  - contact_sheet.png: all screens in order, each with the printed shell's lip shaded (the shell covers the
    glass outside a 424 px circle), captioned.

Needs Python 3 with Pillow and ziglang (pip install pillow ziglang). Run from the repository folder:
  python firmware/tools/previews.py [font folder, default firmware/tools/fonts (Inter, used for the captions)]
Old PNGs in the folder are removed first, so a renamed screen leaves no stale picture behind.
"""
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, "docs", "previews", "settings")
SIZE, SAFE_R = 466, 212


def main():
    font_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "fonts")
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".png"):
            os.remove(os.path.join(OUT, f))
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "preview.exe")
        subprocess.run([sys.executable, "-m", "ziglang", "c++", "-std=c++17", "-O2", "-Wall", "-Wno-unused-function",
                        "-o", exe, os.path.join(HERE, "preview", "preview.cpp")], check=True)
        subprocess.run([exe, tmp], check=True)
        shots = [line.rstrip("\n").split("\t") for line in open(os.path.join(tmp, "list.txt"), encoding="utf-8") if line.strip()]
        mask = Image.new("L", (SIZE, SIZE), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, SIZE - 1, SIZE - 1), fill=255)
        images = []
        for file, caption in shots:
            img = Image.open(os.path.join(tmp, file + ".ppm")).convert("RGBA")
            img.putalpha(mask)
            img.save(os.path.join(OUT, file + ".png"), optimize=True)
            images.append((file, caption, img))
    sheet(images, font_dir)
    print(f"wrote {len(images)} screens and contact_sheet.png to {OUT}")


def sheet(images, font_dir):
    cols, pad, cap_h = 4, 36, 56
    tile = SIZE + 40
    rows = (len(images) + cols - 1) // cols
    W = cols * tile + (cols + 1) * pad
    H = rows * (tile + cap_h) + (rows + 1) * pad + 70
    out = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(out)
    try:
        f_cap = ImageFont.truetype(os.path.join(font_dir, "Inter-Medium.ttf"), 22)
        f_head = ImageFont.truetype(os.path.join(font_dir, "Inter-SemiBold.ttf"), 30)
    except OSError:
        f_cap = f_head = ImageFont.load_default()
    d.text((pad, pad - 6), "Mic display: watch faces and settings app, as drawn by the firmware (shell lip shaded)", font=f_head, fill=(255, 255, 255))
    # the printed shell: a lip over the glass outside the 424 px window
    lip = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lip)
    ld.ellipse((0, 0, tile - 1, tile - 1), fill=(44, 44, 46, 255))
    o = tile // 2 - SAFE_R
    hole = Image.new("L", (tile, tile), 0)
    ImageDraw.Draw(hole).ellipse((o, o, tile - o - 1, tile - o - 1), fill=255)
    for i, (file, caption, img) in enumerate(images):
        r, c = divmod(i, cols)
        x = pad + c * (tile + pad)
        y = 70 + pad + r * (tile + cap_h + pad)
        out.paste(lip, (x, y), lip)
        screen = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
        screen.paste(img, (20, 20), img)
        window = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
        window.paste(screen, (0, 0), hole)
        out.paste(window, (x, y), window)
        d.text((x + tile / 2, y + tile + 14), caption, font=f_cap, fill=(142, 142, 147), anchor="mt")
    out.save(os.path.join(OUT, "contact_sheet.png"), optimize=True)


if __name__ == "__main__":
    main()
