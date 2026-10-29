# Claude highlight reel

A [Claude Code](https://claude.com/claude-code) skill that turns your OBS Call of Duty recordings into YouTube videos ready for you to review:

- a 3-6 minute **main video** (1920x1080 60fps), commentary-led, long takes around each kill streak, hard cuts
- a 30-45 second **vertical Short** (1080x1920 60fps) of the best streak, with royalty-free music
- **3 thumbnail options** and a `review.md` with titles, description and tags

Claude builds each one as a **DaVinci Resolve timeline**, so you can tweak the cut, then renders and loudness-checks it (-14 LUFS, true peak -1 dBTP). It never uploads anything. You review and upload by hand.

## What's here

| Path | What it does |
|---|---|
| `skills/highlight-reel/SKILL.md` | The editing recipe Claude follows. |
| `docs/audio-brief.md` | Music licence (StreamBeats), SFX rules and loudness targets. |
| `scripts/scan_xp.py` | Finds kills by spotting the yellow "N XP" popup next to the crosshair. |
| `thumbnails/make_thumbnail.py` | Makes a 1280x720 thumbnail from a still. See `thumbnail-recipe.md`. |
| `automation/obs-session-end.lua` + `launch.ps1` | Optional: starts a build automatically when you close OBS. |

## You need

- Windows, OBS, DaVinci Resolve Studio with the DaVinci Resolve MCP connected to Claude Code
- ffmpeg on PATH (or set the `FFMPEG` environment variable to its full path)
- Python 3 with Pillow (`pip install pillow`)
- PowerShell 7 (only for the automation)
- Music from [StreamBeats](https://streambeats.bandcamp.com) in `<VIDEOS>\Assets\Music\`

## Setup

1. Copy `skills/highlight-reel` into `%USERPROFILE%\.claude\skills\`.
2. Open `SKILL.md` and fill in the **Setup** section: your videos folder, channel name, Resolve project and where you put `scripts\`.
3. In OBS, record **four audio tracks**: 1 mix, 2 game, 3 mic, 4 Discord/party chat. Remux recordings to MP4 into `<VIDEOS>\Captures\`. Mute the game's own music in its settings.
4. In Resolve, create the project yourself and set it to **60 fps** before importing anything.
5. Ask Claude: *"Make a highlight reel from today's captures."*

### Optional: build automatically when OBS closes

Put `obs-session-end.lua` and `launch.ps1` in the same folder, then add the Lua script in OBS (Tools > Scripts > +). When OBS closes, `launch.ps1` waits for it to finish, finds new captures over 200 MB and runs Claude headless. A Windows notification pops up when it's done.

To test it without building anything (close OBS first):

```bash
pwsh -File launch.ps1 -DryRun
```

If your videos aren't in `%USERPROFILE%\Videos`, pass `-Videos <path>`.

## Good to know

- `scan_xp.py` is calibrated for 1920x1080 MW4 captures. Other games or HUD scales need the search box and template re-traced.
- **Resolve trap:** every audio track must be routed to **Bus 1** (Fairlight > Bus Assign) or it plays silent. The scripting API can't see bus routing, mute or solo, so check these yourself after a build.
- The style rules (long takes, no music in the main video, calm blue labels) are one creator's taste. Edit `SKILL.md` to match yours.

## Licence

MIT. See `LICENSE`. Music and sound effects aren't included; follow their own licences.
