$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath("Desktop")

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut((Join-Path $desktop "Tidal Now Playing.lnk"))
$Shortcut.TargetPath = Join-Path $here "start-widget.bat"
$Shortcut.WorkingDirectory = $here
$Shortcut.IconLocation = Join-Path $here "app-icon.ico"
$Shortcut.WindowStyle = 7
$Shortcut.Save()
Write-Output "Shortcut created on Desktop."
