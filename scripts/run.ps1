# HashMate launcher (Windows PowerShell)
# Usage:         .\scripts\run.ps1
# Create shortcut: .\scripts\run.ps1 -CreateShortcut

param(
    [switch]$CreateShortcut
)

$ErrorActionPreference = "Stop"

# Locate project root (parent of script dir)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# ---------- Create desktop shortcut with icon ----------
if ($CreateShortcut) {
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut("$env:USERPROFILE\Desktop\HashMate.lnk")
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-NoExit -File `"$ScriptDir\run.ps1`""
    $Shortcut.WorkingDirectory = "$ProjectRoot"
    $IconPath = "$ProjectRoot\assets\icon.ico"
    if (Test-Path $IconPath) {
        $Shortcut.IconLocation = $IconPath
    }
    $Shortcut.Save()
    Write-Host "Desktop shortcut created: Desktop\HashMate.lnk" -ForegroundColor Green
    exit 0
}

# ---------- Normal launch ----------
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] uv not found. Install: https://docs.astral.sh/uv/" -ForegroundColor Red
    exit 1
}

Write-Host "Syncing dependencies (uv sync)..." -ForegroundColor Cyan
uv sync

Write-Host "Starting HashMate..." -ForegroundColor Green
uv run hashmate
