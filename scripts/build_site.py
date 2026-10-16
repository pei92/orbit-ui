#!/usr/bin/env python3
"""从 website/ 生成介绍网站到 dist/。

- website/      网站页面源码（index / showcase / docs 和 site/ 下的样式脚本）
- assets/orbit.css → dist/site/orbit.css，以及每个示例目录里的 orbit.css
- examples/     → dist/examples/，案例页里的实时预览用

dist/ 是产物，每次整体重建，不要直接改它。
用法：python scripts/build_site.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "website"
DIST = ROOT / "dist"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if not (SRC / "index.html").exists():
        print(f"找不到 {SRC / 'index.html'}", file=sys.stderr)
        return 1

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SRC, DIST)

    css = ROOT / "assets" / "orbit.css"
    (DIST / "site").mkdir(exist_ok=True)
    shutil.copy2(css, DIST / "site" / "orbit.css")

    shutil.copytree(ROOT / "examples", DIST / "examples")
    # 每个示例目录都引用自己目录下的 orbit.css，统一换成最新版
    for copy in (DIST / "examples").rglob("orbit.css"):
        shutil.copy2(css, copy)

    pages = sum(1 for _ in SRC.glob("*.html"))
    examples = sum(1 for _ in (DIST / "examples").rglob("*.html"))
    print(f"已生成 {DIST}：{pages} 个网站页面，{examples} 个示例页面")
    return 0


if __name__ == "__main__":
    sys.exit(main())
