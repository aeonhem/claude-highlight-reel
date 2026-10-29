---
name: highlight-reel
description: Build Call of Duty highlight videos from a recording session's OBS captures as DaVinci Resolve timelines (ffmpeg for scanning and measuring) - a 3-6 min horizontal commentary-led main video and a vertical Short - into <VIDEOS>\Highlights\Review for manual upload. Use when asked to make, redo or continue a highlight reel/Short from captures, or when launch.ps1 starts a headless run after OBS closes.
---

# Highlight reel (CoD, Resolve + ffmpeg)

Never publish or upload. The creator reviews everything in `<VIDEOS>\Highlights\Review` and uploads by hand.

The style is commentary-led gameplay, not a montage. Pick one reference video whose pacing you like and note it here (for example, a creator's MW4 gameplay video at a set time range), so every build matches it.

## Setup (fill these in once)
- `<VIDEOS>`: your videos folder, e.g. `C:\Users\<you>\Videos`. It holds `Captures\`, `Highlights\` and `Assets\`.
- `<CHANNEL>`: your channel name, used in output file names.
- `<RESOLVE_PROJECT>`: the Resolve project the timelines go in. Create it yourself and set it to **60 fps** before importing (new projects default to 24 fps).
- `<TOOLS>`: where `scan_xp.py` lives (the `scripts\` folder of this repo).
- ffmpeg on PATH (or set `FFMPEG` to its full path).

## Inputs
- Captures: `<VIDEOS>\Captures\*.mp4` (OBS remux of MKV), 1920x1080 60fps. OBS records four audio tracks: `a:0` mix, `a:1` game, `a:2` mic, `a:3` comms (Discord/party). Mute CoD's own music in-game so it can't trigger copyright claims.
- Music (Short only): `<VIDEOS>\Assets\Music\` (StreamBeats WAVs). Never generate music.
- SFX: a Sonniss GDC Game Audio Bundle in `<VIDEOS>\Assets\`: bass booms only, Short only.
- `docs/audio-brief.md` has the music licence and mix targets. Where it disagrees with this skill on format or length, this skill wins.

## Deliverables (per session date)
1. `Review\<CHANNEL>_Highlights_<date>.mp4`: horizontal 1920x1080 60fps, 3-6 min, H.264 + AAC 48 kHz.
2. `Review\<CHANNEL>_Short_<date>.mp4`: 1080x1920 60fps, 30-45 s, centre crop.
3. `Review\<date> review.md`: a segment table (capture, in/out, kills, why kept), total footage length, segments used, 3 title options, description, tags. Frame titles around skill, not gore.
Skip a cut that already exists. Put working files in `Highlights\<date>\`.

## Pre-flight (before cutting anything)
Check and report anything missing, then continue (interactive: wait for the creator if something blocks the build):
- ffmpeg/ffprobe run, and `<TOOLS>\validate_reel.py` exists.
- Resolve MCP connects (`get_resolve_status`); if not, `launch_resolve`. Remind the creator the project must be 60 fps.
- Captures for the date exist; list them with durations.
- List every audio file under `Assets\Music` **recursively** (subfolders count). Never conclude there's no music from the top level alone; never generate any.

## Find kills
- Run `python -I <TOOLS>\scan_xp.py <capture>` (~1 min per 10 min of footage). It prints windows where the yellow "N XP" popup next to the crosshair is up. The popup stays up and its total climbs during a streak. It's calibrated on 1920x1080 MW4 captures; other games or HUD scales need the box and template re-traced.
- The popup is brief, so check stills *inside* each window (a contact sheet is cheap). Count kills from the XP total and the "Nth KILL" medal. Popup time lags the kill by ~0.2 s. Ignore objective-point and assist windows.
- Find deaths and respawns on a contact sheet (`fps=1/3,tile=5x4`): killcam = red screen, respawn = black frame.

## Baseline for every video
- **Start:** fade audio and picture in from silence and black.
- **End:** fade audio and picture out to silence and black.
- Each fade is **1 s or shorter**. This applies to the main video and the Short.

## Cut list (before building)
Write the planned segments as a table (capture, in, out, what happens, why chosen) to `Highlights\<date>\cutlist.md`. Check each segment: it ends **before** any death, killcam, scoreboard or end-of-match screen, and back-to-back kills are preferred over reactions. Interactive run: show the table and wait for the creator's OK before building. Headless run (`launch.ps1`): don't wait; build, and put the same table in review.md.

## Horizontal main video
1. **Long takes:** each segment runs uncut from 5-10 s before the first kill to the end of the streak, typically 20-60 s. Never cut between kills inside a streak.
2. **Hard cuts only, at natural breaks:** before a death, at match end, or after more than ~10 s of dead running. No transitions, fades (except the start/end baseline above), whips, slow-mo, speed ramps, zooms or memes. Use 80 ms audio micro-fades at each cut, just to avoid clicks.
3. **Deaths:** cut before them by default. Keep one when the creator has a good mic reaction to it (check the `a:2` mic around the death).
4. **Downtime:**
   - Drop end-of-match screens. Cut from the last kill straight to the next thing.
   - Lobby or loading time stays only while the creator is talking on the mic, up to ~20 s.
   - Silent downtime is removed or cut to under 2 s.
5. **Structure:** matches in chronological order. Each match gets one 2-4 s establishing beat (spawn or map intro).
6. **Audio:**
   - Game `a:1` at full level, plus the mic `a:2`. Keep commentary clearly audible over the game.
   - **No music.**
7. **Text:** the game HUD only, plus at most one small calm label per match start (e.g. the map name). Labels are white with a muted, low-contrast blue outline. Nothing during fights.

## Short (vertical)
- The best streak as **one continuous take of 30-45 s**, with the centre crop (check it reads fine for your HUD).
- Music is allowed: a StreamBeats track fading in and out under the game audio. Ramp or drop only on a real streak payoff. Note the drop times of tracks you use often (e.g. "Dropped Frames" 6.20 s, "Electric Cringe" 6.86 s).
- End by pointing to the full video (a short end label in the same white and blue style).
- **Ending (baseline for every Short):** end on music. Fade game and mic audio out so they're gone at least 1 s before the end. That leaves the last ~1 s as music and footage only, then a 0.25 s fade-out of the music (and picture) at the very end.

## Assembly: DaVinci Resolve timelines
The creator tweaks the cut on the timeline during review, so every deliverable must exist as a Resolve timeline, not only as an MP4. Use ffmpeg for scanning, contact sheets and loudness measurement, not for assembly.
- **Setup:** use the DaVinci Resolve MCP (`launch_resolve` if it isn't running). Never create a Resolve project; work inside `<RESOLVE_PROJECT>`.
- **Timelines:** create `Highlights <date>` (1920x1080 60fps) and `Short <date>` (1080x1920 60fps, timeline-specific resolution, centre crop). Re-runs replace these timelines; don't stack v2/v3 copies.
- **Clips:** `AppendToTimeline` with startFrame/endFrame/recordFrame per segment. Linked appends fill the timeline's audio tracks with the clip's tracks, so keep game (a:1) and mic (a:2), and drop the mix and comms copies.
- **Music (Short only):** on its own track, with fades set on the clip.
- **Text:** a carrier clip with `AddFusionComp()`, plus a TextPlus connected to MediaOut. Do all of it in one script inside `comp.StartUndo/EndUndo`; comps edited later were ignored at render.
- **Render:** mp4, H264_NVIDIA (or your GPU's H.264 encoder), the timeline's resolution, 60fps, AAC 48 kHz. `StartRendering([job], False)` often returns False on the first job after a format change. Delete jobs, set the format, sleep 0.5 s between set, add and start.
- **Known traps:** `SetTrackEnable` silently does nothing. Every audio track must be routed to **Bus 1** (Fairlight > Bus Assign) or it plays silent in playback and render. The API can't read or set bus routing, track mute or solo, so after building, ask the creator to confirm each audio track is assigned to Bus 1. Stills only export from the Color page. Resolve can crash mid-build; the launcher retries once, so save the project after each timeline.
- **Fallback:** if Resolve fails twice, assemble with ffmpeg and say so in review.md. That route works: one `-ss/-t` input per segment, `fps=60,setpts=PTS-STARTPTS` + `concat`; audio `[i:a:1]`+`[i:a:2]` with 80 ms `afade`; `-/filter_complex <file>` for long graphs.

## Master
- Target -14 LUFS integrated, true peak <= -1 dBTP.
- Set clip and track levels in Resolve, render, then measure the **final MP4** with ffmpeg `ebur128=peak=true`. Adjust and re-render until it's within about 0.5 LU, and report the numbers. For reference, one game-only session needed about +5.9 dB, from -18.5 to -14.3 LUFS.
- **Validate every render:** `python -I <TOOLS>\validate_reel.py <mp4> [--short] --out Highlights\<date>`. It checks resolution, 60 fps, length, -14 LUFS, true peak, audio and picture fades, and writes `<name>_cuts.png` (last frames before each cut). Fix and re-render until all checks pass, then open the cuts image and confirm no death, killcam or scoreboard frames. Quote the PASS/FAIL lines in review.md.
- On the ffmpeg route, `loudnorm` alone left AAC peaks at -0.1 dBTP; use `volume` + `alimiter=limit=0.7:level=false` there.
- Write review.md, naming the Resolve timelines. Report what you didn't check (phone listen, mic reactions judged from levels or transcripts, not by ear).

## Optional skills and agents
These come from other Claude Code plugins. Use whichever you have installed, at the step shown. This skill's own rules and numbers win wherever they disagree.
- **`video-editor-skills:resolve-scripting`**: before any Resolve script (also under Assembly).
- **`ffmpeg-llm:ffmpeg-expert`** (agent): when an ffmpeg command fails, loudness or true peak won't land, or the fallback needs a complex filtergraph.
- **`video-editor-skills:voice-and-audio`**: when the mic sounds muffled, noisy or boomy, or after a normalise made a clip worse. Use its diagnosis, Voice Isolation and EQ recipe. **Ignore its normalise step and -16 LKFS target:** ours is -14 LUFS / -1 dBTP (see Master). EQ is by hand, so list it in review.md rather than driving the UI.
- **`video-editor-skills:youtube-export`**: before the first render of a session, for the colour-tag check (Same as Project on Rec.709-A) and bitrate sanity. Its 4K bitrates are too high for 1080p60; keep files reasonable and the Render settings above.
- **`video-cleanup`**: only if the mic has real background noise, wind or hum. It needs a DeepFilterNet download, so **ask first and skip it in headless runs** (note "mic denoise not done" in review.md). It writes new files and never touches originals.
- **`watch-video:watch-video`**: interactive runs only, and only after the creator OKs sending the render to that service. Use it to catch bad cut points and audio problems that stills and levels can't show. Skip in headless runs and say it wasn't done.
- **vidIQ (read-only, never publish):**
  - `vidiq:vidiq-packaging-studio`: for the 3 title options and 3 thumbnail concepts in review.md, to sharpen packaging around skill, not gore.
  - `vidiq:vidiq-retention-analysis`: at the start of a session, on the most recent published video, to see where viewers dropped off and feed that into cut and pacing choices. Needs the YouTube channel authorised in vidIQ; if it isn't, skip it and note that in review.md. Don't prompt for authorisation in headless runs.
  - **Never** call the vidIQ tools that upload, update a video or its thumbnail, post or reply to comments, or publish. **Never** use `vidiq_generate_music` or any generated music (see Inputs). Analysis only; the creator uploads by hand.

## Traps
- Odd crop widths/heights in rawvideo pipes return short buffers. Keep crops even.
- Thumbnails are a separate job: see `thumbnails/thumbnail-recipe.md`.
