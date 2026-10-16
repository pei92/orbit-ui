# 风格对比页

把几个候选方向放在同一页里并排比较，由用户挑选。对比页的外壳中性，不带任何方向的风格。

## 准备输入

一个目录里放 `manifest.json` 和候选 HTML。候选引用的图片、字体、CSS 放在同一目录或子目录，用相对路径；生成器会把它们内嵌进对比页，产物是一个可以离线打开的单文件。

```json
{
  "schemaVersion": 1,
  "project": "<项目名称>",
  "brief": "<所有候选共同表达的内容与主要任务>",
  "round": "01",
  "candidates": [
    {
      "id": "mission",
      "name": "<方向名称>",
      "concept": "<北极星>",
      "typography": "<字族、字重与尺度关系>",
      "palette": ["#07090c", "#ffb547", "#5be3b0"],
      "traits": ["<看得见的特征>", "<看得见的特征>"],
      "source": "mission.html"
    }
  ]
}
```

可选字段：顶层或候选里的 `"nativeViewport": "1920x1080"`（固定画布的大屏，对比页等比缩放）；候选的 `"kind": "image"`（只有截图时）；`"baseline": true`（现状，排第一）。

示例见 [`examples/launch-page/manifest.json`](../examples/launch-page/manifest.json)。

## 生成和打开

```text
python <skill>/scripts/build_explorer.py <目录>/manifest.json [--force] [--output 路径]
```

产物默认是 manifest 旁边的 `style-explorer.html`。写错时生成器一次列出所有要改的地方。

对比页支持：并排 / 单张查看，桌面 / 手机视口切换，←→ 翻页，点“选择”复制一句“<轮次>：选 <编号> <方向名>”，用户把这句话发回给 Agent 继续工作。对比页不写回任何文件。

## 记录选择

用户粘贴选择或直接说出后，按轮次和编号对照 manifest，把选择和备注写进设计说明，再回到步骤 2。
