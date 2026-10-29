"""Check a rendered highlight MP4 against the highlight-reel rules.

Usage: python -I validate_reel.py <video.mp4> [--short] [--out <dir>]
Prints PASS/FAIL per check, writes <out>/<name>_report.json and a contact sheet of
the last frames before each hard cut (scene change) so deaths/killcams/scoreboards can
be eyeballed. Exit code 1 if any check fails. Never uploads anything.
"""
import json, os, re, subprocess, sys, glob

FF = glob.glob(os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin"))
BIN = FF[0] if FF else ""
ffmpeg = os.path.join(BIN, "ffmpeg") if BIN else "ffmpeg"
ffprobe = os.path.join(BIN, "ffprobe") if BIN else "ffprobe"


def run(*a):
    return subprocess.run(a, capture_output=True, text=True, errors="replace")


def probe(path):
    r = run(ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", path)
    return json.loads(r.stdout)


def loudness(path):
    r = run(ffmpeg, "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-")
    s = r.stderr.split("Summary:")[-1]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", s).group(1)), \
        float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", s).group(1))


def edge_level(path, start, dur):
    """Mean volume (dB) of an audio window; very low = faded to silence."""
    r = run(ffmpeg, "-nostats", "-ss", str(start), "-t", str(dur), "-i", path,
            "-af", "volumedetect", "-vn", "-f", "null", "-")
    m = re.search(r"mean_volume:\s+(-?[\d.]+|-inf)", r.stderr)
    return -99.0 if not m or m.group(1) == "-inf" else float(m.group(1))


def edge_luma(path, t):
    """Average luma (0-255) of a single frame; near 0 = black."""
    r = subprocess.run([ffmpeg, "-v", "error", "-ss", str(t), "-i", path, "-frames:v", "1",
                        "-vf", "scale=16:16,format=gray", "-f", "rawvideo", "-"],
                       capture_output=True)
    return sum(r.stdout) / len(r.stdout) if r.stdout else 255


def cut_sheet(path, out):
    """Last frame before each scene change, tiled into one image."""
    r = run(ffmpeg, "-nostats", "-i", path, "-vf", "select='gt(scene,0.4)',showinfo",
            "-an", "-f", "null", "-")
    times = [float(t) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]
    if not times:
        return 0
    sel = "+".join(f"between(t,{max(t - 0.05, 0):.3f},{t:.3f})" for t in times)
    run(ffmpeg, "-y", "-i", path, "-vf", f"select='{sel}',scale=480:-1,tile=5x4",
        "-frames:v", "1", out)
    return len(times)


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    path = args[0]
    short = "--short" in args
    out = args[args.index("--out") + 1] if "--out" in args else os.path.dirname(os.path.abspath(path))
    name = os.path.splitext(os.path.basename(path))[0]
    info = probe(path)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    dur = float(info["format"]["duration"])
    num, den = map(int, v["r_frame_rate"].split("/"))
    fps = num / den
    lufs, peak = loudness(path)
    checks = {}

    def chk(k, ok, val):
        checks[k] = {"pass": bool(ok), "value": val}

    want = (1080, 1920) if short else (1920, 1080)
    chk("resolution", (v["width"], v["height"]) == want, f'{v["width"]}x{v["height"]}')
    chk("fps_60", abs(fps - 60) < 0.01, round(fps, 2))
    lo, hi = (30, 45) if short else (180, 360)
    chk("duration", lo <= dur <= hi, f"{dur:.1f}s (want {lo}-{hi}s)")
    chk("loudness_-14_LUFS", abs(lufs + 14) <= 0.5, lufs)
    chk("true_peak_<=-1", peak <= -1.0, peak)
    chk("audio_fade_in", edge_level(path, 0, 0.3) < edge_level(path, 2, 1) - 6, "first 0.3s quieter than 2-3s")
    chk("audio_fade_out", edge_level(path, dur - 0.3, 0.3) < edge_level(path, dur - 3, 1) - 6 or short,
        "last 0.3s quieter than 3s before end" + (" (skipped: Short ends on music)" if short else ""))
    chk("picture_fade_in", edge_luma(path, 0) < 20, "first frame near black")
    chk("picture_fade_out", edge_luma(path, max(dur - 0.05, 0)) < 20, "last frame near black")
    n = cut_sheet(path, os.path.join(out, f"{name}_cuts.png"))

    for k, c in checks.items():
        print(("PASS" if c["pass"] else "FAIL"), k, c["value"])
    print(f"Cut sheet: {n} cuts -> {name}_cuts.png (look for deaths/killcams/scoreboards)")
    with open(os.path.join(out, f"{name}_report.json"), "w") as f:
        json.dump({"file": path, "checks": checks, "cuts": n}, f, indent=2)
    sys.exit(0 if all(c["pass"] for c in checks.values()) else 1)


if __name__ == "__main__":
    main()
