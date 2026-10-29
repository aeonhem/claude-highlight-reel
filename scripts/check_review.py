"""Stop hook: block finishing while a fresh render in Review/ lacks a passing validate_reel report.

A render counts as fresh if modified in the last WINDOW seconds, so older files
(e.g. the 2026-10-28 Short) never block. Exit 2 = block with message on stderr.
"""
import glob, json, os, sys, time

WINDOW = 2 * 3600  # ponytail: mtime heuristic, tighten if it blocks unrelated sessions
ROOT = os.environ.get("HIGHLIGHTS_DIR") or os.path.dirname(os.path.abspath(__file__))  # folder holding Review and the report files

try:
    if json.load(sys.stdin).get("stop_hook_active"):
        sys.exit(0)  # already blocked once this turn; don't loop
except ValueError:
    pass

bad = []
for mp4 in glob.glob(os.path.join(ROOT, "Review", "*.mp4")):
    if time.time() - os.path.getmtime(mp4) > WINDOW:
        continue
    name = os.path.splitext(os.path.basename(mp4))[0]
    reports = glob.glob(os.path.join(ROOT, "**", name + "_report.json"), recursive=True)
    if not reports or os.path.getmtime(reports[0]) < os.path.getmtime(mp4):
        bad.append(f"{name}: not validated since last render")
    else:
        fails = [k for k, c in json.load(open(reports[0]))["checks"].items() if not c["pass"]]
        if fails:
            bad.append(f"{name}: failed {', '.join(fails)}")

if bad:
    print("Run Highlights\\validate_reel.py and fix before finishing:\n" + "\n".join(bad), file=sys.stderr)
    sys.exit(2)
