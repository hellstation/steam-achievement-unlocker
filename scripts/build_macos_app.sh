#!/usr/bin/env bash
# Build a double-clickable macOS .app (opens Terminal with the CLI).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP_NAME="Steam Achievement Unlocker"
DIST_DIR="$ROOT/dist"
BUILD_DIR="$ROOT/build"
BUNDLE="$DIST_DIR/${APP_NAME}.app"
INNER_NAME="SteamAchievementUnlocker"

echo "==> Installing build deps..."
python3 -m pip install -q -r requirements.txt "pyinstaller>=6.0"

echo "==> Cleaning previous build..."
rm -rf "$BUILD_DIR/$INNER_NAME" "$DIST_DIR/$INNER_NAME" "$BUNDLE"

echo "==> PyInstaller..."
python3 -m PyInstaller --noconfirm --clean "$ROOT/SteamAchievementUnlocker.spec"

BIN_DIR="$DIST_DIR/$INNER_NAME"
if [[ ! -x "$BIN_DIR/$INNER_NAME" ]]; then
  echo "ERROR: binary not found at $BIN_DIR/$INNER_NAME"
  exit 1
fi

echo "==> Assembling .app bundle..."
rm -rf "$BUNDLE"
mkdir -p "$BUNDLE/Contents/MacOS"
mkdir -p "$BUNDLE/Contents/Resources/bin"

# Copy frozen payload next to launcher
cp -R "$BIN_DIR/" "$BUNDLE/Contents/Resources/bin/"

# Launcher: open Terminal so the interactive CLI is usable
cat > "$BUNDLE/Contents/MacOS/launcher" <<'LAUNCH'
#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$ROOT/Resources/bin/SteamAchievementUnlocker"
# Escape for AppleScript string
BIN_ESC="${BIN//\\/\\\\}"
BIN_ESC="${BIN_ESC//\"/\\\"}"

osascript <<EOF
tell application "Terminal"
    activate
    do script "clear; \"$BIN_ESC\"; echo; echo 'Нажмите Enter чтобы закрыть...'; read"
end tell
EOF
LAUNCH
chmod +x "$BUNDLE/Contents/MacOS/launcher"
chmod +x "$BUNDLE/Contents/Resources/bin/$INNER_NAME"

# Primary executable name for macOS (must match CFBundleExecutable)
mv "$BUNDLE/Contents/MacOS/launcher" "$BUNDLE/Contents/MacOS/$INNER_NAME"

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
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSHighResolutionCapable</key>
    <true/>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
PLIST

# Optional icon from image.png if sips/iconutil available later — skip for now

echo "==> Done"
echo ""
echo "Приложение: $BUNDLE"
echo "Запуск: open \"$BUNDLE\""
echo "Или перетащи в /Applications"
echo ""
echo "Примечание: первый запуск — ПКМ → Открыть (Gatekeeper)."
echo "Steam должен быть запущен. Данные: ~/.steam_ach_manager.json"
echo "dylib: ~/Library/Application Support/SteamAchievementUnlocker/"
