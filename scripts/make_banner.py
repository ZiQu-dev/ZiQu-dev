#!/usr/bin/env python3
"""Render banner.gif: portfolio-style dark card over falling violet meteors.

Run locally (needs Pillow): python3 scripts/make_banner.py banner.gif
Output is committed; the Forgejo job does not regenerate it.
"""
import sys

from PIL import Image, ImageDraw, ImageFont

W, H, FRAMES = 860, 220, 36
CARD = (28, 20, 832, 200)
RADIUS = 16
BG = (5, 5, 7)  # portfolio near-black
ACCENT = (167, 139, 250)  # portfolio violet accent
FONT_BOLD = "/System/Library/Fonts/HelveticaNeue.ttc"
FONT_MONO = "/System/Library/Fonts/Menlo.ttc"


# (start x, start y, speed in loops per banner cycle, tail length, phase): fixed so the GIF loops cleanly
METEORS = [(780, -10, 1, 110, .00), (640, 20, 2, 80, .35), (520, -30, 1, 130, .62), (860, 60, 2, 90, .15),
           (400, 0, 1, 100, .80), (300, 40, 2, 70, .50), (700, 90, 1, 120, .28), (180, -20, 2, 85, .90)]
DX, DY = -0.8, 0.6  # falls from top right to bottom left
SS = 2  # supersample for smooth thin lines


def background(t):
    # thin meteor streaks, like magicui's Meteors: bright head, fading tail
    img = Image.new("RGBA", (W * SS, H * SS), BG + (255,))
    for x0, y0, sp, ln, ph in METEORS:
        u = (ph + t * sp) % 1
        hx, hy = x0 + DX * u * 900, y0 + DY * u * 900
        for j in range(0, ln, 3):
            a = (1 - j / ln) ** 2
            px, py = hx - DX * j, hy - DY * j
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).line([(px * SS, py * SS), ((px - DX * 3) * SS, (py - DY * 3) * SS)],
                                    fill=(196, 181, 253, int(230 * a)), width=SS * 3 // 2)
            img = Image.alpha_composite(img, ov)
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse(((hx - 1.8) * SS, (hy - 1.8) * SS, (hx + 1.8) * SS, (hy + 1.8) * SS), fill=(245, 243, 255, 255))
        img = Image.alpha_composite(img, ov)
    return img.resize((W, H), Image.LANCZOS).convert("RGB")


def card(frame):
    # flat zinc-950 surface with zinc-800 border, like the portfolio cards
    ov = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(CARD, RADIUS, fill=(9, 9, 11, 205), outline=(63, 63, 70, 255), width=1)
    frame.paste(Image.alpha_composite(frame.convert("RGBA"), ov).convert("RGB"))


def text(frame, t):
    X = 76
    name = ImageFont.truetype(FONT_BOLD, 54, index=1)
    mono = ImageFont.truetype(FONT_MONO, 16)
    small = ImageFont.truetype(FONT_MONO, 14)
    label = "MATEUSZ KORNIAK"
    # white -> zinc vertical gradient through the name, as in the portfolio hero
    mask = Image.new("L", frame.size, 0)
    ImageDraw.Draw(mask).text((X, 76), label, font=name, fill=255)
    grad = Image.new("RGB", frame.size)
    gd = ImageDraw.Draw(grad)
    for y in range(76, 140):
        k = min(1, (y - 76) / 62)
        c = tuple(int(a + (b - a) * k) for a, b in zip((250, 250, 250), (113, 113, 122)))
        gd.line([(0, y), (W, y)], fill=c)
    frame.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(frame)
    d.text((X, 48), "~ $ whoami", font=mono, fill=ACCENT)
    if (int(t * FRAMES) // 6) % 2 == 0:  # blinking cursor
        d.rectangle((X + 112, 50, X + 120, 64), fill=ACCENT)
    d.rectangle((X, 146, X + 40, 147), fill=ACCENT)
    d.text((X, 160), "full-stack · mobile · homelab · UKEN", font=small, fill=(113, 113, 122))


def main(out):
    frames = []
    for i in range(FRAMES):
        t = i / FRAMES
        frame = background(t)
        card(frame)
        text(frame, t)
        frames.append(frame.quantize(colors=160, method=Image.Quantize.MEDIANCUT))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "banner.gif")
