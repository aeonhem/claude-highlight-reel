"""Highlight reel thumbnail maker (1280x720 YouTube thumbnail).

Style: action shot, white text with a low-contrast blue outline and soft
blue glow, calm vibe, curiosity-driven copy about the game.

Usage:
  python make_thumbnail.py STILL.jpg OUT.png "LINE ONE|LINE TWO"
      [--crop x0,y0,x1,y1] [--side left|right] [--tag "MW4"]

  STILL   a 1920x1080 frame from the capture (Resolve still or ffmpeg grab)
  --crop  region of the 1920x1080 frame to use (16:9 box). Use it to zoom
          past the minimap/HUD and onto the action. Default: centre 80%.
  --side  which side the text sits on (pick the emptier side of the shot).
  --tag   small pill in the corner; "" to hide.

Needs Python 3 + Pillow (pip install pillow).
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1280, 720
WHITE = (255, 255, 255)
OUTLINE_BLUE = (52, 84, 122)   # low-contrast blue outline
GLOW_BLUE = (90, 140, 200)     # soft glow behind the text
SHADE_BLUE = (8, 18, 34)       # gradient tint behind the text

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\seguibl.ttf",      # Segoe UI Black
    r"C:\Windows\Fonts\bahnschrift.ttf",  # Bahnschrift (variable)
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def background(still, crop):
    img = Image.open(still).convert("RGB")
    if crop:
        img = img.crop(crop)
    else:
        w, h = img.size
        img = img.crop((w * 0.1, h * 0.1, w * 0.9, h * 0.9))
    img = img.resize((W, H), Image.LANCZOS)
    # Calm grade: slightly lower saturation, cool lift, gentle contrast.
    img = ImageEnhance.Color(img).enhance(0.85)
    img = ImageEnhance.Contrast(img).enhance(1.08)
    cool = Image.new("RGB", (W, H), (30, 60, 100))
    return Image.blend(img, cool, 0.12)


def shade(img, side):
    """Blue-black gradient on the text side so white text reads on any shot."""
    mask = Image.new("L", (W, H))
    px = mask.load()
    for x in range(W):
        t = x / W if side == "right" else 1 - x / W
        a = int(max(0.0, (t - 0.3) / 0.7) ** 1.4 * 200)
        for y in range(H):
            px[x, y] = a
    return Image.composite(Image.new("RGB", (W, H), SHADE_BLUE), img, mask)


def vignette(img):
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse((-W * 0.15, -H * 0.2, W * 1.15, H * 1.2), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(120))
    dark = ImageEnhance.Brightness(img).enhance(0.55)
    return Image.composite(img, dark, mask)


def fit_lines(lines, max_w, max_h):
    size = 160
    while size > 40:
        font = load_font(size)
        widths = [font.getbbox(l)[2] - font.getbbox(l)[0] for l in lines]
        if max(widths) <= max_w and len(lines) * size * 1.05 <= max_h:
            return font, size
        size -= 4
    return load_font(size), size


def draw_text(img, lines, side):
    margin = 60
    font, size = fit_lines(lines, W * 0.6, H * 0.66)
    stroke = max(4, size // 18)
    lh = int(size * 1.05)
    top = (H - lh * len(lines)) // 2

    def anchor_x(line):
        bbox = font.getbbox(line)
        tw = bbox[2] - bbox[0]
        return W - margin - tw - bbox[0] if side == "right" else margin - bbox[0]

    # Soft glow layer
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i, line in enumerate(lines):
        gd.text((anchor_x(line), top + i * lh), line, font=font,
                fill=GLOW_BLUE + (150,), stroke_width=stroke * 3,
                stroke_fill=GLOW_BLUE + (150,))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img = Image.alpha_composite(img.convert("RGBA"), glow)

    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        d.text((anchor_x(line), top + i * lh), line, font=font, fill=WHITE,
               stroke_width=stroke, stroke_fill=OUTLINE_BLUE)
    return img


def draw_tag(img, tag, side):
    if not tag:
        return img
    font = load_font(34)
    bbox = font.getbbox(tag)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 18, 10
    x = 40 if side == "right" else W - 40 - tw - 2 * pad_x
    y = 36
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x, y, x + tw + 2 * pad_x, y + th + 2 * pad_y),
                        radius=12, fill=(20, 40, 70, 200), outline=OUTLINE_BLUE, width=3)
    d.text((x + pad_x - bbox[0], y + pad_y - bbox[1]), tag, font=font, fill=WHITE)
    return img


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("still")
    p.add_argument("out")
    p.add_argument("text", help='lines separated by "|"')
    p.add_argument("--crop", default=None)
    p.add_argument("--side", choices=["left", "right"], default="right")
    p.add_argument("--tag", default="MW4")
    a = p.parse_args(argv)

    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    img = background(a.still, crop)
    img = vignette(img)
    img = shade(img, a.side)
    img = draw_text(img, [l.strip().upper() for l in a.text.split("|")], a.side)
    img = draw_tag(img, a.tag, a.side)
    img.convert("RGB").save(a.out, optimize=True)
    print(a.out)


if __name__ == "__main__":
    sys.exit(main())
