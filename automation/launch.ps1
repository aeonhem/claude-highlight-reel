# Builds a highlight reel from new captures once OBS has fully closed.
# Started by obs-session-end.lua on OBS's exit event, so nothing runs while gaming.
param([switch]$DryRun, [string]$Videos = "$env:USERPROFILE\Videos")   # folder with Captures\ and Highlights\

$captures   = Join-Path $Videos 'Captures'
$highlights = Join-Path $Videos 'Highlights'
$review     = Join-Path $highlights 'Review'             # finished reels wait here for review
$marker     = Join-Path $highlights '.last-auto-reel'   # its timestamp = newest capture already handled
$minBytes   = 200MB                                     # skip quick test clips

# One run at a time, even if OBS is opened and closed again quickly.
$mutex = [System.Threading.Mutex]::new($false, 'Local\AutoHighlightReel')
if (-not $mutex.WaitOne(0)) { exit }

# OBS may still be remuxing MKV -> MP4 while it shuts down.
Wait-Process obs64 -ErrorAction SilentlyContinue
Start-Sleep -Seconds 10

$since = if (Test-Path $marker) { (Get-Item $marker).LastWriteTime } else { (Get-Date).Date }
$new = Get-ChildItem $captures -Filter *.mp4 |
    Where-Object { $_.LastWriteTime -gt $since -and $_.Length -ge $minBytes } |
    Sort-Object LastWriteTime
if (-not $new) { exit }

$date = $new[-1].LastWriteTime.ToString('yyyy-MM-dd')
$out  = Join-Path $highlights $date
New-Item -ItemType Directory -Force $out, $review | Out-Null
$log  = Join-Path $out 'auto-run.log'

# Prefer the standalone CLI (logged in on its own); the desktop app's bundled copy only has auth while the app runs.
# Check the install folder directly: OBS (our parent) may have started before the installer updated PATH.
$claude = @("$env:USERPROFILE\.local\bin\claude.exe", (Get-Command claude -ErrorAction SilentlyContinue).Source) |
    Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $claude) {
    $claude = Get-ChildItem "$env:LOCALAPPDATA\Claude-Data\claude_*\claude-code\*\*\claude.exe" |
        Sort-Object LastWriteTime | Select-Object -Last 1 -ExpandProperty FullName }
if (-not $claude) { "claude.exe not found" | Add-Content $log; exit 1 }

$files  = ($new | ForEach-Object { "- $($_.FullName)" }) -join "`n"
$prompt = @"
Use the highlight-reel skill to build the $date main video and Short from these new captures:
$files
Working files go in $out, deliverables in $review. Reuse anything already made for this date. Do NOT publish or upload anything.
"@

if ($DryRun) { "$claude`n$prompt"; exit }

$started = Get-Date
"$(Get-Date -f s) starting: $($new.Name -join ', ')" | Add-Content $log
Push-Location $Videos   # same folder as the interactive sessions, so CLAUDE.md and memory load
# Second attempt covers a Resolve crash mid-build; it picks up the work already done.
foreach ($try in 1..2) {
    if ($try -eq 2) { $prompt += "`nA previous attempt stopped partway; pick up from the files already made." }
    & $claude -p $prompt --allowedTools 'mcp__DaVinci_Resolve' Read Write Edit Glob Grep PowerShell Skill 2>&1 |
        Add-Content $log
    # Only count it done if a reel actually landed; a stop (e.g. no music) keeps these captures queued.
    $ok = $LASTEXITCODE -eq 0 -and (Get-ChildItem $review -Filter *.mp4 | Where-Object LastWriteTime -gt $started)
    if ($ok) { break }
}
Pop-Location
"$(Get-Date -f s) finished, exit $LASTEXITCODE" | Add-Content $log

if ($ok) { (Get-Item $marker -ErrorAction SilentlyContinue) ?? (New-Item $marker) | Out-Null
           (Get-Item $marker).LastWriteTime = $new[-1].LastWriteTime }

# Toast so you know the reel is waiting for review (WinRT toasts need Windows PowerShell).
$msg = if ($ok) { "Highlight reel for $date is ready to review." } else { "Highlight reel for $date failed, see auto-run.log." }
powershell.exe -NoProfile -Command @"
[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]|Out-Null
`$x=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(1)
`$x.GetElementsByTagName('text')[0].AppendChild(`$x.CreateTextNode('$msg'))|Out-Null
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe').Show([Windows.UI.Notifications.ToastNotification]::new(`$x))
"@
Invoke-Item $(if ($ok) { $review } else { $out })
