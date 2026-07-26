"""打包用 API 入口：PyInstaller 冻结后直接拉起 uvicorn。"""

from __future__ import annotations

import argparse

import uvicorn

from lottery.api.app import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Aether Lottery API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    # 冻结环境下必须传 app 对象，不能用 "module:app" 字符串。
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
