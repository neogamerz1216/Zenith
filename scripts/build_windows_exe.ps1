param(
    [string]$Version = "1.0.0",
    [string]$PythonBin = "python"
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $RootDir ".build-venv-win"
$DistDir = Join-Path $RootDir "dist"

if (!(Test-Path $VenvDir)) {
    & $PythonBin -m venv $VenvDir
}

$Py = Join-Path $VenvDir "Scripts\python.exe"
$Pip = Join-Path $VenvDir "Scripts\pip.exe"

& $Py -m pip install --upgrade pip
& $Pip install -r (Join-Path $RootDir "requirements.txt")

& $Py -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onedir `
  --name "ZenithBrowser" `
  (Join-Path $RootDir "browser.py")

$BundleDir = Join-Path $DistDir "ZenithBrowser"
$ExePath = Join-Path $BundleDir "ZenithBrowser.exe"
if (!(Test-Path $ExePath)) {
    throw "Build output not found: $ExePath"
}

$ZipPath = Join-Path $DistDir ("ZenithBrowser_windows_" + $Version + ".zip")
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

Compress-Archive -Path (Join-Path $BundleDir "*") -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host "Windows EXE ready: $ExePath"
Write-Host "Windows ZIP ready: $ZipPath"
