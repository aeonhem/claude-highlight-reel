# Highlight reel thumbnail recipe

Written so the OBS automation can add it as a step after the reel is built.

## Style
- 1280x720 PNG (YouTube thumbnail size, under 2 MB).
- Action shot from the session's captures. Swap in a face still when a good one shows up.
- White text, heavy font, low-contrast blue outline (#34547A) plus a soft blue glow. Blue-black gradient on the text side so it reads on any shot. Slightly cool, desaturated grade for a calm vibe.
- Small game pill (default "MW4") in the opposite top corner.
- Copy: curious and positive about the game. Two short lines, ending in a question or a hook. Never trash the game.

## Text bank (example; rotate, don't repeat back-to-back)
- Everyone's wrong | about MW4?
- Is MW4 | actually good?
- I like MW4. | Here's why.
- MW4 isn't | the problem
- Wait... | MW4 is fun?
- Nobody talks | about this

## Steps
1. Pick 1 to 3 stills where an enemy is visible on screen (kill moments from the reel's analysis, e.g. `Highlights\<date>\analysis\*.jpg`, or export a still from the Color page in Resolve). Use the 16:9 1920x1080 frames, not the 9:16 Short crops.
2. Choose a 16:9 crop box that cuts the minimap/HUD and puts the action on the side opposite the text. Example: `--crop 480,190,1920,1000` on a frame where the action is centre-left.
3. Render 3 options with the same shot and different text:
   ```
   python make_thumbnail.py STILL.jpg "<Review>\<date> thumbnail A.png" "Everyone's wrong|about MW4?" --crop 480,190,1920,1000 --side right
   ```
4. Look at the result. If text covers the action, flip `--side` or move the crop.
5. Save next to the reel in `Highlights\Review` and list the files in that day's `review.md`. The creator picks one and uploads it manually. No auto-publishing.

Needs Python 3 + Pillow (`pip install pillow`). On Windows it uses Segoe UI Black, falling back to Bahnschrift or Arial Bold.
