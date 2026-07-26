#!/usr/bin/env bash
# 构建内嵌 API 可执行文件到 desktop/resources/bin/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
OUT_DIR="$ROOT/desktop/resources/bin"
mkdir -p "$OUT_DIR"

"$PYTHON" -m pip install -q -U pip wheel
"$PYTHON" -m pip install -q -e .
"$PYTHON" -m pip install -q "pyinstaller>=6.3"

NAME="aether-api"
if [[ "${OS:-}" == "Windows_NT" || "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* ]]; then
  NAME="aether-api.exe"
fi

rm -rf "$ROOT/build/pyinstaller" "$ROOT/dist/aether-api" "$ROOT/dist/aether-api.exe"
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name aether-api \
  --distpath "$ROOT/dist" \
  --workpath "$ROOT/build/pyinstaller" \
  --specpath "$ROOT/build/pyinstaller" \
  --paths "$ROOT" \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols \
  --hidden-import uvicorn.protocols.http \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.websockets \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.lifespan \
  --hidden-import uvicorn.lifespan.on \
  --collect-all uvicorn \
  --collect-all fastapi \
  --collect-submodules pydantic \
  lottery/api/sidecar.py

BIN_SRC="$ROOT/dist/aether-api"
if [[ -f "$ROOT/dist/aether-api.exe" ]]; then
  BIN_SRC="$ROOT/dist/aether-api.exe"
  NAME="aether-api.exe"
fi
cp "$BIN_SRC" "$OUT_DIR/$NAME"
chmod +x "$OUT_DIR/$NAME" || true
if [[ "$(uname -s)" == Darwin ]]; then
  codesign --force --sign - "$OUT_DIR/$NAME" || true
fi
echo "Built: $OUT_DIR/$NAME"
ls -lh "$OUT_DIR/$NAME"
