-- Add in OBS: Tools > Scripts > +. Costs nothing while OBS runs; when OBS shuts down it hands off
-- to launch.ps1 (kept in the same folder as this script), which waits for OBS to close and builds
-- the reel if there are new captures.
-- Uses script_unload because OBS unloads scripts before the frontend EXIT event reaches them.
function script_description()
    return "Builds a highlight reel from new recordings after OBS closes."
end

function script_unload()
    local launcher = (script_path() .. "launch.ps1"):gsub("/", "\\")
    os.execute('start "" conhost.exe --headless "C:\\Program Files\\PowerShell\\7\\pwsh.exe" -NoProfile '
        .. '-ExecutionPolicy Bypass -File "' .. launcher .. '"')
end
