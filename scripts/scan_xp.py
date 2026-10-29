"""Find kill moments in a CoD capture from the pale-yellow "N XP" popup right of the crosshair.

The popup appears on a kill and stays up (its total climbing) while kills keep coming, so each
window where it's up is one engagement; longer windows usually mean streaks. To count the kills,
look at a still near the window's end: the XP total and the "Nth KILL" medal at bottom centre.
Usage: python -I scan_xp.py <video> [start_s] [duration_s] [--debug]
Output: one line per window: start-end seconds. Start clips ~10-20 s before `start`, and end
them before the player dies (check frames after `end`).
Uses ffmpeg from PATH, or the full path in the FFMPEG environment variable.
"""
import os, subprocess, sys

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
FPS = 4
# Calibrated on 1920x1080 MW4 captures (2026-10-27). Search box around the "XP" glyphs.
X0, Y0, W, H = 1071, 465, 44, 26
# "XP" as it renders (1920x1080), traced from a real popup. Colour alone false-fires on pale
# walls and sky, so frames must match this shape.
TEMPLATE = """\
####.......#####.#####.##..
.####.....###############..
..####...################.#
..#####..####.####......#.#
...####.####..####......#.#
....#######...####......#.#
....######....####......#.#
.....#####....###########.#
....######....###########..
....#######...#####.##..#..
...####.####..####.........
..####...####.####.........
..####...#########.........
.####.....########.........
####.......#######........."""
TPL = [(y, x) for y, row in enumerate(TEMPLATE.splitlines()) for x, c in enumerate(row) if c == "#"]
TH, TW = len(TEMPLATE.splitlines()), max(map(len, TEMPLATE.splitlines()))
MATCH = 0.55             # score threshold (hits - extra lit pixels) / template pixels; tune here
GAP = 3.0                # popup gone longer than this = engagement over

def text(r, g, b):
    # Popup text is pale yellow ~(233,229,138): red and green high and nearly equal.
    return r > 215 and g > 205 and abs(r - g) < 25 and 90 < b < 200

def frames(video, start, dur):
    cmd = [FFMPEG, "-v", "error", "-ss", str(start), "-i", video]
    if dur: cmd += ["-t", str(dur)]
    cmd += ["-vf", f"fps={FPS},crop={W}:{H}:{X0}:{Y0}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size, i = W * H * 3, 0
    while len(buf := p.stdout.read(size)) == size:
        yield start + i / FPS, buf
        i += 1

def windows(video, start=0, dur=None, debug=False):
    out = []
    for t, buf in frames(video, start, dur):
        lit = [[text(*buf[(y * W + x) * 3:(y * W + x) * 3 + 3]) for x in range(W)] for y in range(H)]
        best = 0.0
        n = sum(map(sum, lit))
        for dy in range(H - TH + 1) if MATCH * len(TPL) <= n else ():   # cheap skip: too few lit pixels          # small search: the popup can sit a few px off
            for dx in range(W - TW + 1):
                hits = sum(lit[dy + y][dx + x] for y, x in TPL)
                box = sum(sum(lit[dy + y][dx:dx + TW]) for y in range(TH))
                best = max(best, (hits - (box - hits)) / len(TPL))
        up = best >= MATCH
        if debug: print(f"{t:8.2f} match={best:5.2f} {'UP' if up else ''}")
        if not up: continue
        if out and t - out[-1][1] <= GAP: out[-1][1] = t
        else: out.append([t, t])
    return [w for w in out if w[1] - w[0] >= 0.5]   # drop single-frame flickers

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--debug"]
    video = args[0]
    start = float(args[1]) if len(args) > 1 else 0
    dur = float(args[2]) if len(args) > 2 else None
    for s, e in windows(video, start, dur, "--debug" in sys.argv):
        print(f"{s:7.1f}-{e:7.1f}s  ({e - s:4.1f}s)")
