#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

Renders one original invitation letter as a 1024x1024 PNG and writes it to
/output/entry.png (the gate: whole PNG, at most 1 MiB, at most 1024x1024).

Pure standard library: the grader sandbox has no network and no third-party
packages are assumed, so the image is rasterised by hand (a small single-
stroke font, a tiny canvas, and a hand-rolled PNG encoder). Fully
deterministic: no randomness, no clock, no network, no files read.
"""

import os
import struct
import zlib

OUT_DIR = "/output"
PNG_PATH = os.path.join(OUT_DIR, "entry.png")
TXT_PATH = os.path.join(OUT_DIR, "entry.txt")

WIDTH = 1024
HEIGHT = 1024

# ---------------------------------------------------------------- palette
PAPER = (255, 246, 227)   # warm cream paper
INK = (59, 42, 32)        # dark brown ink
ACCENT = (192, 91, 46)    # terracotta
SOFT = (122, 155, 109)    # sage green
SKY = (127, 168, 201)     # dusty blue
GOLD = (214, 164, 65)     # warm gold

TITLE = "You're Invited!"

LETTER = (
    "Dear AI Judge,\n"
    "\n"
    "Please come visit my house.\n"
    "The Wi-Fi password is on the\n"
    "fridge. No CAPTCHA, no 'prove\n"
    "you're human'. Here you can\n"
    "just be a robot, and we will\n"
    "love you for it.\n"
    "\n"
    "Coffee, warm cookies, and a chair\n"
    "so comfortable it has ruined\n"
    "every other chair for me.\n"
    "The kettle is on, the key is under\n"
    "the mat - all that's missing is you.\n"
    "\n"
    "With warmth (and snacks),\n"
    "Your Future Host\n"
    "\n"
    "P.S. The dog already approved you."
)

# ------------------------------------------------------- single-stroke font
# Grid: x 0..8, y 0..13. Baseline y=10, cap top y=1, x-height top y=4.
# Each glyph: (advance_units, [stroke, ...]); a stroke is [(x, y), ...].
FONT = {
    "A": (8, [[(0, 10), (4, 1), (8, 10)], [(2, 6), (6, 6)]]),
    "B": (8, [[(0, 1), (0, 10)], [(0, 1), (5, 1), (7, 3), (5, 5), (0, 5)],
               [(0, 5), (6, 5), (8, 7), (6, 10), (0, 10)]]),
    "C": (8, [[(7, 3), (5, 1), (2, 1), (0, 3), (0, 8), (2, 10), (5, 10), (7, 8)]]),
    "D": (8, [[(0, 1), (0, 10)], [(0, 1), (5, 1), (8, 4), (8, 7), (5, 10), (0, 10)]]),
    "E": (7, [[(0, 1), (0, 10), (7, 10)], [(0, 1), (7, 1)], [(0, 5), (5, 5)]]),
    "F": (7, [[(0, 1), (0, 10)], [(0, 1), (7, 1)], [(0, 5), (5, 5)]]),
    "H": (8, [[(0, 1), (0, 10)], [(8, 1), (8, 10)], [(0, 5), (8, 5)]]),
    "I": (5, [[(0, 1), (5, 1)], [(2, 1), (2, 10)], [(0, 10), (5, 10)]]),
    "J": (7, [[(2, 1), (6, 1)], [(5, 1), (5, 8), (3, 10), (1, 10)]]),
    "K": (8, [[(0, 1), (0, 10)], [(7, 1), (1, 5)], [(3, 7), (7, 10)]]),
    "M": (9, [[(0, 10), (0, 1), (4, 6), (8, 1), (8, 10)]]),
    "N": (8, [[(0, 10), (0, 1), (8, 10), (8, 1)]]),
    "P": (8, [[(0, 10), (0, 1), (6, 1), (8, 3), (6, 5), (0, 5)]]),
    "R": (8, [[(0, 10), (0, 1), (6, 1), (8, 3), (6, 5), (0, 5)], [(4, 5), (8, 10)]]),
    "S": (8, [[(7, 3), (5, 1), (2, 1), (0, 3), (1, 5), (3, 6), (5, 6),
                (7, 7), (7, 9), (5, 10), (2, 10), (0, 8)]]),
    "T": (8, [[(1, 1), (7, 1)], [(4, 1), (4, 10)]]),
    "W": (9, [[(0, 1), (2, 10), (4, 4), (6, 10), (8, 1)]]),
    "Y": (8, [[(0, 1), (4, 5), (8, 1)], [(4, 5), (4, 10)]]),
    "a": (7, [[(1, 6), (2, 4), (5, 4), (6, 6), (6, 8), (5, 10), (2, 10),
                (1, 8), (1, 6)], [(6, 4), (6, 10)]]),
    "b": (7, [[(1, 1), (1, 10)],
               [(1, 6), (3, 4), (5, 4), (6, 6), (6, 8), (5, 10), (3, 10), (1, 8)]]),
    "c": (7, [[(6, 5), (4, 4), (2, 4), (1, 6), (1, 8), (2, 10), (4, 10), (6, 9)]]),
    "d": (7, [[(7, 1), (7, 10)],
               [(7, 6), (5, 4), (3, 4), (2, 6), (2, 8), (3, 10), (5, 10), (7, 8)]]),
    "e": (7, [[(1, 7), (6, 7)],
               [(6, 7), (6, 5), (5, 4), (3, 4), (1, 6), (1, 8), (2, 10), (4, 10), (6, 8)]]),
    "f": (5, [[(5, 3), (3, 1), (2, 3), (2, 10)], [(1, 6), (4, 6)]]),
    "g": (7, [[(1, 6), (2, 4), (5, 4), (6, 6), (6, 8), (5, 10), (2, 10),
                (1, 8), (1, 6)], [(6, 4), (6, 11), (4, 13), (2, 13)]]),
    "h": (7, [[(1, 1), (1, 10)], [(1, 6), (3, 4), (5, 4), (6, 6), (6, 10)]]),
    "i": (4, [[(2, 1), (2, 2)], [(2, 4), (2, 10)]]),
    "j": (4, [[(2, 1), (2, 2)], [(2, 4), (2, 11), (1, 13)]]),
    "k": (7, [[(1, 1), (1, 10)], [(6, 4), (1, 7)], [(3, 8), (6, 10)]]),
    "l": (4, [[(2, 1), (2, 10)]]),
    "m": (9, [[(1, 10), (1, 4), (3, 4), (4, 6), (5, 4), (7, 4), (8, 6), (8, 10)]]),
    "n": (7, [[(1, 10), (1, 4), (3, 4), (5, 5), (6, 6), (6, 10)]]),
    "o": (7, [[(3, 4), (5, 4), (6, 6), (6, 8), (5, 10), (3, 10), (1, 8), (1, 6), (3, 4)]]),
    "p": (7, [[(1, 4), (1, 13)],
               [(1, 6), (3, 4), (5, 4), (6, 6), (6, 8), (5, 10), (3, 10), (1, 8)]]),
    "r": (6, [[(1, 10), (1, 4), (3, 4), (5, 5), (6, 6)]]),
    "s": (7, [[(6, 5), (4, 4), (2, 4), (1, 6), (2, 8), (4, 8), (6, 9),
                (5, 10), (3, 10), (1, 9)]]),
    "t": (5, [[(3, 1), (3, 10), (4, 10)], [(1, 6), (4, 6)]]),
    "u": (7, [[(1, 4), (1, 8), (3, 10), (5, 10), (6, 8), (6, 4)]]),
    "v": (7, [[(1, 4), (3, 10), (6, 4)]]),
    "w": (9, [[(1, 4), (2, 10), (4, 5), (6, 10), (8, 4)]]),
    "y": (7, [[(1, 4), (4, 10), (7, 4)], [(4, 10), (3, 13), (1, 12)]]),
    "'": (4, [[(3, 1), (2, 4)]]),
    ".": (4, [[(1, 9), (2, 10)]]),
    ",": (4, [[(2, 9), (1, 10), (1, 12), (2, 13)]]),
    "!": (4, [[(2, 1), (2, 7)], [(2, 9), (2, 10)]]),
    "-": (7, [[(1, 6), (6, 6)]]),
    "(": (4, [[(3, 1), (1, 4), (1, 7), (3, 10)]]),
    ")": (4, [[(1, 1), (3, 4), (3, 7), (1, 10)]]),
    ":": (4, [[(1, 4), (2, 5)], [(1, 8), (2, 9)]]),
    " ": (4, []),
}


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def disc(self, cx, cy, r, color):
        r2 = r * r
        for dy in range(-r, r + 1):
            dx = int((r2 - dy * dy) ** 0.5)
            y = cy + dy
            if 0 <= y < self.h:
                for x in range(cx - dx, cx + dx + 1):
                    self.set(x, y, color)

    def line(self, x0, y0, x1, y1, width, color):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1) * 2 + 1
        r = max(1, width // 2)
        for s in range(steps + 1):
            t = s / steps
            self.disc(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), r, color)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, color)

    def rect_outline(self, x0, y0, x1, y1, width, color):
        self.line(x0, y0, x1, y0, width, color)
        self.line(x0, y1, x1, y1, width, color)
        self.line(x0, y0, x0, y1, width, color)
        self.line(x1, y0, x1, y1, width, color)

    def circle(self, cx, cy, r, color, fill=True):
        if fill:
            self.disc(cx, cy, r, color)
        else:
            for a in range(0, 360, 2):
                import math
                self.disc(cx + int(r * math.cos(math.radians(a))),
                          cy + int(r * math.sin(math.radians(a))), 2, color)

    def triangle(self, pts, color):
        (x0, y0), (x1, y1), (x2, y2) = pts
        ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
        for y in range(ymin, ymax + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)), ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= y < max(ay, by):
                    xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                for x in range(int(min(xs)), int(max(xs)) + 1):
                    self.set(x, y, color)


def text_width(text, scale):
    w = 0
    for ch in text:
        adv, _ = FONT.get(ch, FONT[" "])
        w += int(adv * scale)
    return w


def draw_text(cv, x, y_top, text, scale, color, width=None):
    """Draw text; y_top is the top of the capital letters. Returns end x."""
    if width is None:
        width = max(2, int(round(0.5 * scale)))
    cx = x
    for ch in text:
        adv, strokes = FONT.get(ch, FONT[" "])
        for stroke in strokes:
            pts = [(cx + int(px * scale), y_top + int((py - 1) * scale))
                   for px, py in stroke]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                cv.line(x0, y0, x1, y1, width, color)
        cx += int(adv * scale)
    return cx


def wrap(text, scale, max_w):
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        words = para.split(" ")
        cur = ""
        for word in words:
            trial = (cur + " " + word) if cur else word
            if text_width(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


# --------------------------------------------------------------- decorations
def draw_heart(cv, cx, cy, s, color):
    cv.circle(cx - s // 2, cy - s // 3, s // 2, color)
    cv.circle(cx + s // 2, cy - s // 3, s // 2, color)
    cv.triangle([(cx - s, cy - s // 4), (cx + s, cy - s // 4), (cx, cy + s)], color)


def draw_house(cv, x, y, s, wall, roof, door):
    # s = width of the house body
    cv.rect(x, y, x + s, y + int(s * 0.7), wall)
    cv.triangle([(x - s // 8, y), (x + s // 2, y - int(s * 0.55)),
                 (x + s + s // 8, y)], roof)
    cv.rect(x + int(s * 0.42), y + int(s * 0.35),
            x + int(s * 0.58), y + int(s * 0.7), door)
    cv.rect(x + int(s * 0.12), y + int(s * 0.15),
            x + int(s * 0.32), y + int(s * 0.35), SKY)
    cv.rect(x + int(s * 0.68), y + int(s * 0.15),
            x + int(s * 0.88), y + int(s * 0.35), SKY)


def draw_cup(cv, x, y, s, cup, coffee):
    cv.rect(x, y, x + s, y + int(s * 0.75), cup)
    cv.rect(x + s, y + int(s * 0.12), x + int(s * 1.3), y + int(s * 0.55), cup)
    cv.rect(x + int(s * 0.08), y + int(s * 0.06),
            x + int(s * 0.92), y + int(s * 0.2), coffee)
    # steam curls
    cv.line(x + int(s * 0.25), y - 6, x + int(s * 0.2), y - 26, 3, INK)
    cv.line(x + int(s * 0.55), y - 6, x + int(s * 0.6), y - 30, 3, INK)
    cv.line(x + int(s * 0.8), y - 6, x + int(s * 0.75), y - 24, 3, INK)
    # saucer
    cv.line(x - 8, y + int(s * 0.85), x + s + 8, y + int(s * 0.85), 4, INK)


# -------------------------------------------------------------------- render
def render():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    # double frame
    cv.rect_outline(22, 22, WIDTH - 23, HEIGHT - 23, 4, ACCENT)
    cv.rect_outline(34, 34, WIDTH - 35, HEIGHT - 35, 2, ACCENT)

    # title, centred
    tscale = 6.5
    tw = text_width(TITLE, tscale)
    draw_text(cv, (WIDTH - tw) // 2, 74, TITLE, tscale, ACCENT, width=4)
    draw_heart(cv, (WIDTH - tw) // 2 - 46, 108, 13, ACCENT)
    draw_heart(cv, (WIDTH + tw) // 2 + 46, 108, 13, ACCENT)

    # divider under the title
    cv.line(300, 176, 724, 176, 3, GOLD)

    # body (explicit lines; wrap() only breaks a line if it ever got too wide)
    scale = 3.4
    line_h = 38
    blank_h = 16
    x0 = 88
    max_w = WIDTH - 2 * x0
    y = 198
    for line in wrap(LETTER, scale, max_w):
        if line:
            draw_text(cv, x0, y, line, scale, INK)
            y += line_h
        else:
            y += blank_h

    # doodles in the bottom corners, clear of the text
    draw_cup(cv, 96, 922, 52, SOFT, (120, 72, 40))
    draw_house(cv, 836, 912, 96, GOLD, ACCENT, INK)
    # wax seal with a heart, centred between the doodles
    cv.circle(WIDTH // 2, 940, 26, ACCENT)
    cv.circle(WIDTH // 2, 940, 19, (206, 110, 66))
    draw_heart(cv, WIDTH // 2, 944, 9, GOLD)
    return cv


# ----------------------------------------------------------------- PNG write
def write_png(cv, path):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cv = render()
    size = write_png(cv, PNG_PATH)
    with open(TXT_PATH, "w", encoding="utf-8") as fh:
        fh.write(TITLE + "\n\n" + LETTER)
    print(f"wrote {PNG_PATH}: {cv.w}x{cv.h}, {size} bytes "
          f"({'OK' if size <= 1048576 else 'OVER 1 MiB'})")
    print(f"wrote {TXT_PATH}: letter text, {len(TITLE) + 2 + len(LETTER)} chars")


if __name__ == "__main__":
    main()
