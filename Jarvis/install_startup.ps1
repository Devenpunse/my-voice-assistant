$ErrorActionPreference = "Stop"

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryDirectory = Split-Path -Parent $scriptDirectory
$pythonw = Join-Path $repositoryDirectory ".venv\Scripts\pythonw.exe"

if (-not (Test-Path -LiteralPath $pythonw)) {
    throw "Project Python was not found at '$pythonw'. Create the project .venv and install requirements first."
}

$startupDirectory = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupDirectory "Charu Assistant.lnk"
$scriptPath = Join-Path $scriptDirectory "jarvis.py"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = "`"$scriptPath`""
$shortcut.WorkingDirectory = $scriptDirectory
$shortcut.Description = "Start Charu personal voice assistant when you sign in."
$shortcut.Save()

Write-Output "Charu will start when you sign in to Windows. Run uninstall_startup.ps1 to remove this shortcut."
