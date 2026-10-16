#!/usr/bin/env python3
"""把 manifest 里列出的候选页面组装成一个可以离线打开的风格对比页。

只用标准库。候选 HTML 里引用的本地 CSS、图片、字体会被内嵌成 data URI，
产物是单个 HTML 文件。
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "style-explorer.html"
PLACEHOLDER = "/*__ORBIT_DATA__*/null"

DEFAULT_DESKTOP = {"width": 1280, "height": 800}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
VIEWPORT_RE = re.compile(r"^\s*(\d{3,5})\s*[x×]\s*(\d{3,5})\s*$")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

EPILOG = """用法示例：
  python build_explorer.py examples/launch-page/manifest.json
      生成 examples/launch-page/style-explorer.html；已存在时加 --force。

manifest.json 最少要有：
  {"schemaVersion": 1, "project": "<项目名>", "brief": "<共同的内容与任务>",
   "candidates": [{"id": "mission", "name": "<方向名>", "concept": "<北极星>",
     "typography": "<字体关系>", "palette": ["#07090c", "#ffb547"],
     "traits": ["<看得见的特征>"], "source": "mission.html"}]}

可选字段：
  round           顶层。轮次，例如 "01"，会出现在复制的选择里。
  nativeViewport  顶层或候选。"1920x1080" 或 {"width":1920,"height":1080}；
                  固定画布的大屏用它，对比页按此渲染再等比缩放。
  kind            候选。"html"（默认）或 "image"（source 指向 PNG/JPEG/WebP）。
  baseline        候选。true 表示现状，排第一位，每轮最多一个。
"""


class ManifestError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def parse_viewport(value, where: str, problems: list[str]):
    if value is None:
        return None
    if isinstance(value, dict):
        w, h = value.get("width"), value.get("height")
        if isinstance(w, int) and isinstance(h, int) and w >= 200 and h >= 200:
            return {"width": w, "height": h}
    elif isinstance(value, str):
        m = VIEWPORT_RE.match(value)
        if m:
            return {"width": int(m.group(1)), "height": int(m.group(2))}
    problems.append(f'{where}.nativeViewport 写成 "1920x1080" 或 {{"width": 1920, "height": 1080}}')
    return None


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix.lower() == ".woff2":
        mime = "font/woff2"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def is_local_ref(ref: str) -> bool:
    ref = ref.strip()
    return bool(ref) and not re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", ref, re.I)


def resolve_inside(base: Path, ref: str, root: Path) -> Path | None:
    target = (base / ref.split("#")[0].split("?")[0]).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target if target.is_file() else None


def inline_css_urls(css: str, base: Path, root: Path) -> str:
    def repl(m: re.Match) -> str:
        ref = m.group(2)
        if not is_local_ref(ref):
            return m.group(0)
        target = resolve_inside(base, ref, root)
        return f'url("{data_uri(target)}")' if target else m.group(0)

    return re.sub(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""", repl, css)


def inline_html(html_path: Path, root: Path, problems: list[str], where: str) -> str:
    html = html_path.read_text(encoding="utf-8")
    base = html_path.parent

    def link_repl(m: re.Match) -> str:
        tag = m.group(0)
        if not re.search(r"""rel\s*=\s*['"]?stylesheet""", tag, re.I):
            return tag
        href = re.search(r"""href\s*=\s*(['"])(.*?)\1""", tag, re.I)
        if not href or not is_local_ref(href.group(2)):
            return tag
        target = resolve_inside(base, href.group(2), root)
        if not target:
            problems.append(f"{where}: 找不到样式 {href.group(2)}（要放在 manifest 所在目录里）")
            return tag
        css = inline_css_urls(target.read_text(encoding="utf-8"), target.parent, root)
        return f"<style>/* {href.group(2)} */\n{css}</style>"

    html = re.sub(r"<link\b[^>]*>", link_repl, html, flags=re.I)

    def src_repl(m: re.Match) -> str:
        attr, quote, ref = m.group(1), m.group(2), m.group(3)
        if not is_local_ref(ref):
            return m.group(0)
        target = resolve_inside(base, ref, root)
        if not target:
            problems.append(f"{where}: 找不到文件 {ref}")
            return m.group(0)
        if target.suffix.lower() in {".js", ".mjs"}:
            return m.group(0)  # 脚本在下面整体内联
        return f"{attr}={quote}{data_uri(target)}{quote}"

    html = re.sub(r"""\b(src|poster)\s*=\s*(['"])(.*?)\2""", src_repl, html, flags=re.I)

    def script_repl(m: re.Match) -> str:
        ref = m.group(2)
        if not is_local_ref(ref):
            return m.group(0)
        target = resolve_inside(base, ref, root)
        if not target:
            problems.append(f"{where}: 找不到脚本 {ref}")
            return m.group(0)
        code = target.read_text(encoding="utf-8").replace("</script", "<\\/script")
        return f"<script>{code}</script>"

    html = re.sub(r"""<script\b[^>]*\bsrc\s*=\s*(['"])(.*?)\1[^>]*>\s*</script>""",
                  lambda m: script_repl(m), html, flags=re.I)
    return inline_css_urls(html, base, root)


def load_manifest(path: Path) -> dict:
    problems: list[str] = []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ManifestError([f"找不到 {path}"])
    except json.JSONDecodeError as e:
        raise ManifestError([f"manifest 不是合法 JSON：第 {e.lineno} 行第 {e.colno} 列，{e.msg}"])
    if not isinstance(raw, dict):
        raise ManifestError(["manifest 顶层要是一个对象 {...}"])

    root = path.parent.resolve()
    if raw.get("schemaVersion") != 1:
        problems.append('顶层加 "schemaVersion": 1')
    for key in ("project", "brief"):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            problems.append(f'顶层 "{key}" 要是非空字符串')
    top_vp = parse_viewport(raw.get("nativeViewport"), "顶层", problems)

    cands = raw.get("candidates")
    if not isinstance(cands, list) or not cands:
        problems.append('"candidates" 要是至少有一项的数组')
        cands = []

    out, seen, baselines = [], set(), 0
    for i, c in enumerate(cands):
        where = f"candidates[{i}]"
        if not isinstance(c, dict):
            problems.append(f"{where} 要是对象")
            continue
        cid = c.get("id")
        if not isinstance(cid, str) or not ID_RE.match(cid):
            problems.append(f'{where}.id 用小写字母、数字和连字符，例如 "mission"')
        elif cid in seen:
            problems.append(f"{where}.id “{cid}” 重复了")
        else:
            seen.add(cid)
        for key in ("name", "concept", "typography", "source"):
            if not isinstance(c.get(key), str) or not c[key].strip():
                problems.append(f'{where}.{key} 要是非空字符串')
        palette = c.get("palette")
        if not isinstance(palette, list) or not palette or not all(isinstance(p, str) and HEX_RE.match(p) for p in palette):
            problems.append(f'{where}.palette 写成十六进制色值数组，例如 ["#07090c", "#ffb547"]')
            palette = []
        traits = c.get("traits", [])
        if not isinstance(traits, list) or not all(isinstance(t, str) for t in traits):
            problems.append(f"{where}.traits 要是字符串数组")
            traits = []
        kind = c.get("kind", "html")
        if kind not in ("html", "image"):
            problems.append(f'{where}.kind 只认 "html" 或 "image"')
        if c.get("baseline") is True:
            baselines += 1
        vp = parse_viewport(c.get("nativeViewport"), where, problems) or top_vp

        entry = {
            "id": cid, "name": c.get("name"), "concept": c.get("concept"),
            "typography": c.get("typography"), "palette": palette, "traits": traits,
            "baseline": c.get("baseline") is True, "viewport": vp, "kind": kind,
        }
        src = c.get("source")
        if isinstance(src, str) and src.strip():
            target = resolve_inside(root, src, root)
            if not target:
                problems.append(f"{where}.source 找不到 {src}（路径相对 manifest，且不能跑出这个目录）")
            elif kind == "image":
                if target.suffix.lower() not in IMAGE_EXT:
                    problems.append(f"{where}.source 图片只认 PNG、JPEG、WebP、GIF")
                else:
                    entry["image"] = data_uri(target)
            else:
                entry["html"] = inline_html(target, root, problems, where)
        out.append(entry)

    if baselines > 1:
        problems.append("baseline 每轮最多一个")
    if problems:
        raise ManifestError(problems)

    out.sort(key=lambda e: not e["baseline"])
    return {
        "project": raw["project"], "brief": raw["brief"],
        "round": str(raw.get("round", "01")),
        "defaultViewport": DEFAULT_DESKTOP, "candidates": out,
    }


def build(manifest: Path, output: Path | None = None, force: bool = False) -> Path:
    data = load_manifest(manifest)
    output = output or manifest.parent / "style-explorer.html"
    if output.exists() and not force:
        raise ManifestError([f"{output} 已存在，加 --force 覆盖，或用 --output 换一个文件名"])
    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise RuntimeError(f"模板 {TEMPLATE} 缺少占位符 {PLACEHOLDER}")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")
    title = f"{data['project']} · 第 {data['round']} 轮方向对比"
    html = template.replace(PLACEHOLDER, payload).replace("{{TITLE}}", title.replace("<", "&lt;"))
    output.write_text(html, encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows 控制台默认 GBK，中文提示会乱码
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="把 manifest 里列出的候选页面组装成一个可以离线打开的风格对比页",
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path, help="manifest.json 的路径")
    parser.add_argument("--output", type=Path, help="输出路径；默认 manifest 旁边的 style-explorer.html")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的输出文件")
    args = parser.parse_args(argv)
    try:
        out = build(args.manifest, args.output, args.force)
    except ManifestError as e:
        print("manifest 有这些地方要改：", file=sys.stderr)
        for p in e.problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"已生成 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
