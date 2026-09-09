"""Generate PNG app icons and a Play Store feature graphic."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "static" / "icons"
PLAY = ROOT / "play-store"

PURPLE = (124, 58, 237, 255)
GOLD = (253, 230, 138, 255)
WHITE = (255, 255, 255, 255)
INK = (15, 23, 42, 255)


def star_points(cx: float, cy: float, r_out: float, r_in: float, n: int = 5):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(-90 + i * (180 / n))
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def app_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = int(size * 0.22)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=PURPLE)
    cx = cy = size / 2
    draw.polygon(star_points(cx, cy + size * 0.02, size * 0.32, size * 0.14), fill=GOLD)
    return img


def feature_graphic() -> Image.Image:
    w, h = 1024, 500
    img = Image.new("RGBA", (w, h), PURPLE)
    draw = ImageDraw.Draw(img)
    draw.ellipse((-80, -120, 280, 240), fill=(167, 139, 250, 80))
    draw.ellipse((760, 220, 1180, 640), fill=(245, 158, 11, 50))
    icon = app_icon(220)
    img.paste(icon, (72, (h - 220) // 2), icon)
    try:
        title_font = ImageFont.truetype("segoeui.ttf", 72)
        sub_font = ImageFont.truetype("segoeui.ttf", 32)
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = title_font
    draw.text((340, 160), "Word Stars", font=title_font, fill=WHITE)
    draw.text((340, 250), "Kids word game — hear, say, spell.", font=sub_font, fill=GOLD)
    return img


def main() -> None:
    ICONS.mkdir(parents=True, exist_ok=True)
    PLAY.mkdir(parents=True, exist_ok=True)
    app_icon(192).save(ICONS / "icon-192.png")
    app_icon(512).save(ICONS / "icon-512.png")
    feature_graphic().save(PLAY / "feature-graphic.png")
    print("Wrote icons and feature graphic.")


if __name__ == "__main__":
    main()
