#!/bin/bash
# Build release/echo-pc-mac-arm64.zip containing a self-contained "Echo PC.app".
# Usage: scripts/build_mac_app.sh [python3.12]  (set ECHO_VERSION=v1.2.0 for the bundle version)
set -euo pipefail
cd "$(dirname "$0")/.."
python=${1:-python3.12}
rm -rf release/mac release/mac-build release/mac-venv release/echo-pc-mac-arm64.zip
"$python" -m venv release/mac-venv
release/mac-venv/bin/python -m pip install -q -r pc/requirements.txt pyinstaller==6.22.3
release/mac-venv/bin/python -m PyInstaller --noconfirm --distpath release/mac --workpath release/mac-build scripts/echo-pc-mac.spec
codesign --verify --deep --strict "release/mac/Echo PC.app"
ditto -c -k --keepParent "release/mac/Echo PC.app" release/echo-pc-mac-arm64.zip
echo release/echo-pc-mac-arm64.zip
