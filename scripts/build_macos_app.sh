#!/usr/bin/env bash
# Build a double-clickable macOS .app for Intel + Apple Silicon (M1/M2/M3).
#
# - Outer launcher: universal2 Mach-O (arm64 + x86_64) → opens Terminal reliably
# - Inner PyInstaller payload: best arch available on this machine
#   (on Intel Mac = x86_64, runs on M1 via Rosetta with explicit arch -x86_64)
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP_NAME="Steam Achievement Unlocker"
DIST_DIR="$ROOT/dist"
BUILD_DIR="$ROOT/build"
BUNDLE="$DIST_DIR/${APP_NAME}.app"
INNER_NAME="SteamAchievementUnlocker"
LAUNCHER_SRC="$ROOT/scripts/macos_launcher.c"
LAUNCHER_OUT="$BUILD_DIR/macos_launcher"

echo "==> Host arch: $(uname -m)"
echo "==> Installing build deps..."
python3 -m pip install -q -r requirements.txt "pyinstaller>=6.0"

echo "==> Cleaning previous build..."
rm -rf "$BUILD_DIR/$INNER_NAME" "$DIST_DIR/$INNER_NAME" "$BUNDLE" "$LAUNCHER_OUT"
mkdir -p "$BUILD_DIR"

echo "==> Compiling universal launcher (x86_64 + arm64)..."
if ! clang -arch x86_64 -arch arm64 -O2 -o "$LAUNCHER_OUT" "$LAUNCHER_SRC" 2>/tmp/sau_clang_err.txt; then
  echo "WARN: universal clang failed, trying host arch only"
  cat /tmp/sau_clang_err.txt || true
  clang -O2 -o "$LAUNCHER_OUT" "$LAUNCHER_SRC"
fi
file "$LAUNCHER_OUT"
lipo -info "$LAUNCHER_OUT" 2>/dev/null || true

echo "==> PyInstaller..."
# Prefer universal2 if this Python supports it; otherwise host arch.
TARGET_ARCH_ARG=()
if python3 - <<'PY'
import sys, platform
# PyInstaller universal2 needs a fat Python; skip if pure x86_64/arm64
from pathlib import Path
import sysconfig
lib = Path(sysconfig.get_config_var("LIBDIR") or "") / (sysconfig.get_config_var("LDLIBRARY") or "")
import subprocess
if lib.exists():
    out = subprocess.check_output(["file", str(lib)], text=True)
    if "x86_64" in out and "arm64" in out:
        sys.exit(0)
sys.exit(1)
PY
then
  echo "    Python looks universal → target_arch=universal2"
  # patch via env consumed in spec if we add it; for now pass CLI override
  python3 -m PyInstaller --noconfirm --clean \
    --target-arch universal2 \
    "$ROOT/SteamAchievementUnlocker.spec" || {
      echo "    universal2 failed, falling back to host arch"
      python3 -m PyInstaller --noconfirm --clean "$ROOT/SteamAchievementUnlocker.spec"
    }
else
  echo "    Python is single-arch → building host payload ($(uname -m))"
  python3 -m PyInstaller --noconfirm --clean "$ROOT/SteamAchievementUnlocker.spec"
fi

BIN_DIR="$DIST_DIR/$INNER_NAME"
if [[ ! -x "$BIN_DIR/$INNER_NAME" ]]; then
  echo "ERROR: binary not found at $BIN_DIR/$INNER_NAME"
  exit 1
fi
echo "==> Payload:"
file "$BIN_DIR/$INNER_NAME"
lipo -info "$BIN_DIR/$INNER_NAME" 2>/dev/null || true

echo "==> Assembling .app bundle..."
rm -rf "$BUNDLE"
mkdir -p "$BUNDLE/Contents/MacOS"
mkdir -p "$BUNDLE/Contents/Resources/bin"

cp -R "$BIN_DIR/" "$BUNDLE/Contents/Resources/bin/"
# Universal entry point (runs on Intel and M1 natively)
cp "$LAUNCHER_OUT" "$BUNDLE/Contents/MacOS/$INNER_NAME"
chmod +x "$BUNDLE/Contents/MacOS/$INNER_NAME"
chmod +x "$BUNDLE/Contents/Resources/bin/$INNER_NAME"

cat > "$BUNDLE/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>${INNER_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.hellstation.steam-achievement-unlocker</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.1</string>
    <key>CFBundleVersion</key>
    <string>2</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>LSHighResolutionCapable</key>
    <true/>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>LSArchitecturePriority</key>
    <array>
        <string>arm64</string>
        <string>x86_64</string>
    </array>
</dict>
</plist>
PLIST

echo "==> Verifying bundle entry point..."
file "$BUNDLE/Contents/MacOS/$INNER_NAME"
file "$BUNDLE/Contents/Resources/bin/$INNER_NAME"

echo "==> Done"
echo ""
echo "Приложение: $BUNDLE"
echo "Запуск: open \"$BUNDLE\""
echo ""
echo "Intel:  нативный x86_64 payload"
echo "Apple Silicon: launcher arm64 + payload через Rosetta (arch -x86_64)"
echo "  Если Rosetta нет: softwareupdate --install-rosetta --agree-to-license"
echo ""
echo "Версия бандла: 1.0.1"
