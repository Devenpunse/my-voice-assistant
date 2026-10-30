$ErrorActionPreference = "Stop"

$shortcutPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup\Charu Assistant.lnk"

if (Test-Path -LiteralPath $shortcutPath) {
    Remove-Item -LiteralPath $shortcutPath
    Write-Output "Charu was removed from Windows startup."
} else {
    Write-Output "Charu is not registered in Windows startup."
}
