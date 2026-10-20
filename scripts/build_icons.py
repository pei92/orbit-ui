#!/usr/bin/env python3
"""把 assets/icons/*.svg 写进 orbit.css 的图标段，生成 .o-icon--<名字> 类。

图标用 CSS mask 着色（跟随 currentColor），HTML 用 file:// 打开也能显示，
不依赖外部雪碧图。改了或新增 SVG 后重新运行本脚本。

用法：python scripts/build_icons.py [--css assets/orbit.css] [--icons assets/icons]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
START = "/* @icons:start —— 由 scripts/build_icons.py 生成，不要手改 */"
END = "/* @icons:end */"


def data_uri(svg: str) -> str:
    svg = re.sub(r"\s+", " ", svg.strip()).replace("currentColor", "#000")
    return "data:image/svg+xml," + quote(svg, safe=" =:/.,-'\"")


def build(icons_dir: Path) -> str:
    files = sorted(icons_dir.glob("*.svg"))
    if not files:
        sys.exit(f"没有找到图标：{icons_dir}")
    rules = [
        f'.o-icon--{f.stem} {{ --o-i: url("{data_uri(f.read_text(encoding="utf-8")).replace(chr(34), chr(39))}"); }}'
        for f in files
    ]
    return "\n".join([START, *rules, END])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--css", type=Path, default=ROOT / "assets" / "orbit.css")
    p.add_argument("--icons", type=Path, default=ROOT / "assets" / "icons")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    css = a.css.read_text(encoding="utf-8")
    block = build(a.icons)
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(css):
        sys.exit(f"{a.css} 里没有图标段标记，先在合适位置放入：\n{START}\n{END}")
    a.css.write_text(pattern.sub(lambda _: block, css), encoding="utf-8", newline="\n")
    print(f"写入 {block.count('.o-icon--')} 个图标 → {a.css}")


if __name__ == "__main__":
    main()
