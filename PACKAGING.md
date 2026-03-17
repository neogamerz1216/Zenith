# Packaging Zenith Browser

This project now includes build scripts for:

1. Linux Debian package (`.deb`)
2. Windows executable bundle (`.exe` inside zip)
3. macOS app bundle (`.app` + optional `.dmg`)

## Important

PyQt6 WebEngine apps must be built on the target OS:

1. Build `.deb` on Linux
2. Build `.exe` on Windows
3. Build `.app`/`.dmg` on macOS

Cross-compiling these reliably from one OS is not supported for this stack.

## Dependencies

Install Python build dependencies:

```bash
pip install -r requirements.txt
```

## Linux (`.deb`)

```bash
chmod +x scripts/build_linux_deb.sh
APP_VERSION=1.0.0 scripts/build_linux_deb.sh
```

Output:

1. `dist/zenith-browser_1.0.0_amd64.deb`

## Windows (`.exe`)

Run in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_windows_exe.ps1 -Version 1.0.0
```

Output:

1. `dist\ZenithBrowser\ZenithBrowser.exe`
2. `dist\ZenithBrowser_windows_1.0.0.zip`

## macOS (`.app`, `.dmg`)

```bash
chmod +x scripts/build_macos_app.sh
APP_VERSION=1.0.0 scripts/build_macos_app.sh
```

Output:

1. `dist/Zenith Browser/Zenith Browser.app`
2. `dist/ZenithBrowser_macos_1.0.0.zip`
3. `dist/ZenithBrowser_macos_1.0.0.dmg` (if `hdiutil` is available)

## CI Build For All OS

GitHub Actions workflow is included at:

1. `.github/workflows/build-packages.yml`

Trigger manually from Actions tab or push a version tag like `v1.0.0`.
