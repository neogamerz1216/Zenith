#!/usr/bin/env bash
set -euo pipefail

APP_VERSION="${APP_VERSION:-1.0.0}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
BUILD_DIR="$ROOT_DIR/build/macos"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.build-venv-macos}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$ROOT_DIR/requirements.txt"

"$VENV_DIR/bin/python" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onedir \
  --name "Zenith Browser" \
  "$ROOT_DIR/browser.py"

APP_CONTAINER="$DIST_DIR/Zenith Browser"
APP_BUNDLE="$APP_CONTAINER/Zenith Browser.app"
if [[ ! -d "$APP_BUNDLE" ]]; then
  echo "Build output not found: $APP_BUNDLE"
  exit 1
fi

ZIP_PATH="$DIST_DIR/ZenithBrowser_macos_${APP_VERSION}.zip"
rm -f "$ZIP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_BUNDLE" "$ZIP_PATH"

if command -v hdiutil >/dev/null 2>&1; then
  DMG_ROOT="$BUILD_DIR/dmg-root"
  DMG_PATH="$DIST_DIR/ZenithBrowser_macos_${APP_VERSION}.dmg"
  rm -rf "$DMG_ROOT" "$DMG_PATH"
  mkdir -p "$DMG_ROOT"
  cp -R "$APP_BUNDLE" "$DMG_ROOT/"
  hdiutil create -volname "Zenith Browser" -srcfolder "$DMG_ROOT" -ov -format UDZO "$DMG_PATH"
  echo "macOS DMG ready: $DMG_PATH"
fi

echo "macOS app bundle: $APP_BUNDLE"
echo "macOS ZIP ready: $ZIP_PATH"
