#!/usr/bin/env bash
set -euo pipefail

APP_ID="zenith-browser"
APP_BINARY_NAME="ZenithBrowser"
APP_DISPLAY_NAME="Zenith Browser"
APP_VERSION="${APP_VERSION:-1.0.0}"
ARCH="${ARCH:-amd64}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/linux"
DIST_DIR="$ROOT_DIR/dist"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.build-venv-linux}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "dpkg-deb not found. Install dpkg to build Debian packages."
  exit 1
fi

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
  --name "$APP_BINARY_NAME" \
  "$ROOT_DIR/browser.py"

BUNDLE_DIR="$ROOT_DIR/dist/$APP_BINARY_NAME"
if [[ ! -d "$BUNDLE_DIR" ]]; then
  echo "Build output not found: $BUNDLE_DIR"
  exit 1
fi

PKG_ROOT="$BUILD_DIR/pkgroot"
mkdir -p \
  "$PKG_ROOT/DEBIAN" \
  "$PKG_ROOT/opt/$APP_ID" \
  "$PKG_ROOT/usr/bin" \
  "$PKG_ROOT/usr/share/applications"

cp -a "$BUNDLE_DIR/." "$PKG_ROOT/opt/$APP_ID/"

cat > "$PKG_ROOT/usr/bin/$APP_ID" <<EOF
#!/usr/bin/env bash
exec /opt/$APP_ID/$APP_BINARY_NAME "\$@"
EOF
chmod 755 "$PKG_ROOT/usr/bin/$APP_ID"

cat > "$PKG_ROOT/usr/share/applications/$APP_ID.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_DISPLAY_NAME
Exec=$APP_ID
Terminal=false
Categories=Network;WebBrowser;
StartupNotify=true
EOF
chmod 644 "$PKG_ROOT/usr/share/applications/$APP_ID.desktop"

cat > "$PKG_ROOT/DEBIAN/control" <<EOF
Package: $APP_ID
Version: $APP_VERSION
Section: web
Priority: optional
Architecture: $ARCH
Maintainer: Zenith Browser Team <support@zenith.local>
Depends: libasound2t64 | libasound2, libatk-bridge2.0-0, libc6, libdrm2, libgbm1, libglib2.0-0, libnspr4, libnss3, libx11-6, libxcb1, libxcomposite1, libxdamage1, libxext6, libxfixes3, libxkbcommon0, libxrandr2
Description: Zenith Browser desktop app built with PyQt6 WebEngine.
 A modern tabbed web browser written in Python and Qt.
EOF

DEB_PATH="$DIST_DIR/${APP_ID}_${APP_VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$PKG_ROOT" "$DEB_PATH"

echo "Linux package ready: $DEB_PATH"
