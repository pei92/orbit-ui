#!/usr/bin/env node
// 用本机 Chrome / Edge / Chromium 截图，不需要 npm 依赖。
// 通过 DevTools 协议模拟视口：无头 Chrome 的窗口最窄约 500px，直接设窗口宽度截不了手机尺寸。
// 需要 Node 22+（内置 WebSocket）。
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve, dirname, basename, extname, join } from "node:path";
import { pathToFileURL } from "node:url";

const HELP = `用法：node shoot.mjs <HTML 文件或 http 地址> [选项]

选项：
  --size <desktop|mobile|both|宽x高>  默认 mobile（390x844，2 倍像素）；desktop 是 1440x900
  --out <文件.png>                    输出路径；默认 shots/<页面名>-<尺寸>.png
  --full                              截整页长图
  --wait <毫秒>                       加载后再等多久（字体、入场动画），默认 1200
  --dry-run                           只打印计划，不启动浏览器

找不到浏览器时设置 ORBIT_CHROME=<浏览器可执行文件路径>。`;

const SIZES = { mobile: [390, 844, 2, true], desktop: [1440, 900, 1, false] };

function fail(msg) { console.error(`${msg}\n\n${HELP}`); process.exit(2); }

function parse(argv) {
  const o = { size: "mobile", wait: 1200, full: false, dry: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "-h" || a === "--help") { console.log(HELP); process.exit(0); }
    else if (a === "--size") o.size = argv[++i];
    else if (a === "--out") o.out = argv[++i];
    else if (a === "--wait") o.wait = Number(argv[++i]);
    else if (a === "--full") o.full = true;
    else if (a === "--dry-run") o.dry = true;
    else if (a.startsWith("--")) fail(`不认识的选项 ${a}`);
    else o.target = a;
  }
  if (!o.target) fail("缺少要截图的页面");
  return o;
}

function findChrome() {
  if (process.env.ORBIT_CHROME) return process.env.ORBIT_CHROME;
  const pf = process.env.PROGRAMFILES || "C:\\Program Files";
  const pf86 = process.env["PROGRAMFILES(X86)"] || "C:\\Program Files (x86)";
  const local = process.env.LOCALAPPDATA || "";
  return [
    `${pf}\\Google\\Chrome\\Application\\chrome.exe`,
    `${pf86}\\Google\\Chrome\\Application\\chrome.exe`,
    `${local}\\Google\\Chrome\\Application\\chrome.exe`,
    `${pf86}\\Microsoft\\Edge\\Application\\msedge.exe`,
    `${pf}\\Microsoft\\Edge\\Application\\msedge.exe`,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/microsoft-edge",
  ].find(p => p && existsSync(p));
}

function sizesOf(s) {
  if (s === "both") return [["desktop", ...SIZES.desktop], ["mobile", ...SIZES.mobile]];
  if (SIZES[s]) return [[s, ...SIZES[s]]];
  const m = /^(\d{3,5})x(\d{3,5})$/.exec(s || "");
  if (!m) fail("--size 写成 desktop、mobile、both 或 宽x高，例如 1920x1080");
  const w = Number(m[1]);
  return [[s, w, Number(m[2]), w < 768 ? 2 : 1, w < 768]];
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function waitForPort(profile, ms = 15000) {
  const file = join(profile, "DevToolsActivePort");
  for (const end = Date.now() + ms; Date.now() < end; await sleep(100)) {
    if (existsSync(file)) {
      const [port] = readFileSync(file, "utf8").split("\n");
      if (port) return Number(port);
    }
  }
  throw new Error("浏览器没有在 15 秒内启动");
}

class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.waiters = []; }
  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((ok, no) => { ws.onopen = ok; ws.onerror = () => no(new Error("连不上 DevTools")); });
    const c = new CDP(ws);
    ws.onmessage = e => {
      const msg = JSON.parse(e.data);
      if (msg.id && c.pending.has(msg.id)) {
        const { ok, no } = c.pending.get(msg.id); c.pending.delete(msg.id);
        msg.error ? no(new Error(msg.error.message)) : ok(msg.result);
      } else if (msg.method) {
        c.waiters = c.waiters.filter(w => (w.method === msg.method ? (w.ok(msg.params), false) : true));
      }
    };
    return c;
  }
  send(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((ok, no) => this.pending.set(id, { ok, no }));
  }
  once(method, ms = 30000) {
    return new Promise((ok, no) => {
      this.waiters.push({ method, ok });
      setTimeout(() => no(new Error(`等待 ${method} 超时`)), ms);
    });
  }
}

async function shoot(chrome, url, jobs, o) {
  const profile = mkdtempSync(join(tmpdir(), "orbit-shoot-"));
  const proc = spawn(chrome, [
    "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
    "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank",
  ], { stdio: "ignore" });
  try {
    const port = await waitForPort(profile);
    const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const page = targets.find(t => t.type === "page");
    const cdp = await CDP.connect(page.webSocketDebuggerUrl);
    await cdp.send("Page.enable");
    for (const [label, w, h, scale, mobile] of jobs) {
      await cdp.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: scale, mobile });
      await cdp.send("Emulation.setTouchEmulationEnabled", { enabled: mobile });
      const loaded = cdp.once("Page.loadEventFired");
      await cdp.send("Page.navigate", { url });
      await loaded;
      await cdp.send("Runtime.evaluate", { expression: "document.fonts.ready.then(() => 1)", awaitPromise: true });
      await sleep(o.wait);
      let clip;
      if (o.full) {
        // 先从上滚到下：触发进入视口才出现的内容和懒加载的 iframe / 图片，再回到顶部截长图
        await cdp.send("Runtime.evaluate", { awaitPromise: true, expression: `(async () => {
          const step = innerHeight * 0.8;
          for (let y = 0; y < document.documentElement.scrollHeight; y += step) { scrollTo({ top: y, behavior: "instant" }); await new Promise(r => setTimeout(r, 120)); }
          scrollTo({ top: 0, behavior: "instant" }); await new Promise(r => setTimeout(r, 300));
        })()` });
        await sleep(Math.min(o.wait, 1500));
        const { cssContentSize } = await cdp.send("Page.getLayoutMetrics");
        clip = { x: 0, y: 0, width: w, height: Math.ceil(cssContentSize.height), scale: 1 };
      }
      const { data } = await cdp.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: !!o.full, ...(clip && { clip }) });
      const out = resolve(o.out && jobs.length === 1 ? o.out : `shots/${basename(o.target, extname(o.target)) || "page"}-${label}.png`);
      mkdirSync(dirname(out), { recursive: true });
      writeFileSync(out, Buffer.from(data, "base64"));
      console.log(`${label} ${w}x${h}@${scale}x → ${out}`);
    }
    cdp.ws.close();
  } finally {
    proc.kill();
    await sleep(300);
    try { rmSync(profile, { recursive: true, force: true }); } catch {}
  }
}

const o = parse(process.argv.slice(2));
// 本地文件也可以带 ?state=… 这类地址参数
const [file, query] = o.target.split(/(?=[?#])/);
const url = /^https?:\/\//.test(o.target) ? o.target : pathToFileURL(resolve(file)).href + (query || "");
o.target = file;
const jobs = sizesOf(o.size);
const chrome = findChrome();
if (o.dry) {
  console.log(`浏览器：${chrome || "未找到"}\n页面：${url}`);
  for (const [label, w, h, s] of jobs) console.log(`  ${label} ${w}x${h}@${s}x${o.full ? " 整页" : ""}`);
  process.exit(0);
}
if (!chrome) fail("找不到 Chrome / Edge / Chromium，设置 ORBIT_CHROME 指向浏览器");
if (typeof WebSocket === "undefined") fail("需要 Node 22 或更高版本（内置 WebSocket）");
try {
  await shoot(chrome, url, jobs, o);
  console.log("截图保存成功不等于看过：用看图能力打开检查。");
} catch (e) {
  console.error(`截图失败：${e.message}`);
  process.exit(1);
}
