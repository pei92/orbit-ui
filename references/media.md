# 素材

先判断图像能否承担首屏的主信息或情绪重心。需要关键素材时先选定它，再围绕它安排文字，不等布局填满后再补图。

## 公共领域与开放许可的太空素材

| 来源 | 内容 | 许可要点 |
| --- | --- | --- |
| NASA Image and Video Library（images.nasa.gov） | 发射、在轨、行星、哈勃照片 | 多数为公共领域；不得暗示 NASA 背书，不用 NASA 标志 |
| NASA Visible Earth / Blue Marble | 全球地球贴图、夜光图 | 公共领域，适合做 3D 地球贴图 |
| ESA / Hubble / Webb（esahubble.org、esawebb.org） | 深场、星云 | CC BY 4.0，需署名 |
| Solar System Scope Textures | 行星贴图 | CC BY 4.0 |
| Sentinel / Copernicus | 卫星影像 | 开放许可，需注明 “Contains modified Copernicus Sentinel data” |

素材的署名和来源写进任务目录的 `SOURCES.md`。不使用真实机构的标志、任务徽章冒充产品身份。

## 自己画的东西

- 轨道图、星图、剖面图、刻度、准星：用 SVG 画，线宽和界面细线一致。
- 星空背景：Canvas 程序化生成，不用一张拉伸的星空 JPG。
- 写实行星、宇航员、火箭：不手画 SVG，用照片、生成图或 3D。

## 生成配图

提示词写清：机位、光源方向（太空中只有一个主光源，阴影硬）、留给文字的暗部位置、色温与页面色板一致。避免“科幻概念图”默认的紫青双色光。

## 实时 3D

地球、卫星星座、轨道用 three.js（或 globe.gl）：贴图用 Blue Marble，大气用一层菲涅尔发光球。截图取证时 WebGL 可能是空白，空白截图不能当证据，换有 GPU 的浏览器重截或交录屏。
