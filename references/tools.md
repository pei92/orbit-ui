# 工具

本目录自带的程序不需要读源码，全部选项见各自的 `--help`。

## 设计令牌与控件：`assets/orbit.css`

复制到任务目录后引用。`<html data-orbit="mission|blueprint|deepfield">` 选色板；类名：

| 类 | 用途 |
| --- | --- |
| `.o-panel` | 切角面板 |
| `.o-brackets` | 四角定位标（一屏最多一处） |
| `.o-grid-bg` | 坐标网格背景 |
| `.o-btn` / `.o-btn--primary` / `.o-btn--danger` | 按钮；`aria-busy="true"` 显示处理中 |
| `.o-input` | 输入框；`aria-invalid="true"` 显示错误 |
| `.o-status--nominal / --warn / --alert` | 状态灯（形状 + 颜色 + 文字） |
| `.o-gauge`（`style="--v:62"`） | 刻度条 |
| `.o-readout` / `.o-label` / `.o-mono` / `.o-display` | 读数、标签、等宽、展示字 |
| `.o-boot`（`style="--i:2"`） | 上电进入动效 |
| `.o-stripe`（`--w`、`--h`） | 四色涂装条 |
| `.o-rule` / `.o-rule--soft` | 带端点的分区线 |
| `.o-arc`（`--v`、`--size`） | 刻度环，圆心放读数 |
| `.o-list`（`aria-current`） | 菜单列表，选中整行反白 |
| `.o-tabs`（`aria-selected`） | 胶囊分段标签 |
| `.o-objectives`（`data-state="done" / "active"`） | 任务目标清单 |
| `.o-key` | 按键提示 [E] |
| `.o-switch`（`<input type="checkbox">`） | 开关 |
| `.o-table`（数字列加 `.num`） | 表格 |
| `.o-track`（`data-state`） | 订单 / 物流 / 审批步骤轨迹 |
| `.o-avatar` | 头像、首字图标位 |

组件总览页：[`examples/components.html`](../examples/components.html)。

## 风格对比页

```text
python <skill>/scripts/build_explorer.py <目录>/manifest.json [--force]
```

见 [风格对比页](style-explorer.md)。

## 截图

```text
node <skill>/scripts/shoot.mjs <HTML 文件或 http 地址> [--size desktop|mobile|宽x高] [--out 文件.png] [--full]
```

用本机的 Chrome / Edge / Chromium 无头模式截图，不需要安装 npm 依赖。找不到浏览器时设置环境变量 `ORBIT_CHROME=<浏览器可执行文件路径>`。默认手机 390x844；`--size both` 一次出桌面和手机两张。

截图保存成功不等于看过：截完用看图能力打开检查。宿主有自己的浏览器工具时，查看和走查照常用宿主工具。
