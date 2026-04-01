<!-- showprogress: true -->

<title>Console PPT Pro</title>
<subtitle>全功能终极演示指南</subtitle>

---

# 🚀 欢迎使用 Console PPT

这是一个基于 **Textual** & **Rich** 的终端演示引擎。

- **纯文本驱动**: 使用 Markdown 编写所有内容
- **极致视觉**: 支持 256 色及 ANSI 动效
- **现代交互**: 丝滑的 TUI 导航体验

<p align="center" style="color: cyan; font-weight: bold">按下 [Space] 或 [→] 开始探索</p>

---

# 🎨 局部动效矩阵

你可以为任何文字或区块添加实时动效：

- <animate type="pulse">**呼吸灯 (Pulse)**</animate>：平滑的亮度变化
- <animate type="rainbow" speed="1.2">**彩虹循环 (Rainbow)**</animate>：五彩斑斓的视觉效果
- <animate type="glitch">**故障艺术 (Glitch)**</animate>：极客范的随机抖动
- <animate type="bounce">**上下弹跳 (Bounce)**</animate>：充满活力的跳动
- <animate type="move" range="3">**左右平移 (Move)**</animate>：吸引注意的位移
- <animate type="wave" speed="2.0">**颜色波浪 (Wave)**</animate>：适合连续符号 >>>>>>

---

# 🏗️ 高级 HTML 布局

支持标准的 HTML 标签进行精准排版：

<div align="center" style="border: solid grey">
  <h2>居中容器</h2>
  <p>支持 <b>粗体</b>、<i>斜体</i> 以及 <span style="color: #ff00ff; text-decoration: underline">自定义 CSS 样式</span></p>
</div>

<div align="right">
  <p>这是右对齐的内容</p>
  <p style="color: yellow">利用 valign 属性还可以实现垂直居中</p>
</div>

---

# 💻 代码高亮演示

支持 Monokai 主题的高质量语法高亮：

```python
import math

class Particle:
    def __init__(self, char: str, x: int, y: int):
        self.char = char
        self.pos = (x, y)

    def move(self, t: float):
        # 计算重力坠落动效
        y_offset = int(10 * (t ** 2))
        return (self.pos[0], self.pos[1] + y_offset)

# 控制台 PPT 核心逻辑片段
```

---

# 📊 列表与表格

<div align="center">
  <h3>多层级嵌套列表</h3>
</div>

1. 第一章：环境准备
   - Python 3.10+
   - `pip install textual rich pyyaml`
2. 第二章：基础语法
   - 使用 `---` 分割幻灯片
   - 使用 `<!-- notes: ... -->` 添加备注

<br>

| 功能 | Markdown | HTML 扩展 |
|------|:--------:|:---------:|
| 基础样式 | Y | Y |
| 动效支持 | N | Y |
| 垂直对齐 | N | Y |

---

# 🛠️ 幻灯片指令

你可以通过注释精准控制每一页的行为：

- `<!-- hideprogress -->`: 隐藏当前页进度条
- `<!-- showprogress: false -->`: 全局隐藏进度条
- `<!-- notes: ... -->`: 添加演讲者备注

---

<!-- hideprogress -->

# 🌙 过渡页示例 (无进度条)

<div valign="middle" align="center">
  <animate type="pulse" speed="0.5">
    <h1 style="color: grey">这是过渡页</h1>
  </animate>
  <p>使用了 <code><!-- hideprogress --></code> 隐藏了底部的状态栏</p>
</div>

---

# 📝 演讲者备注

按下 `n` 键查看底部的备注区域！

<br>
<div align="center">
  <animate type="move" range="2">
    <p>👇 备注现在呈现在屏幕底部 👇</p>
  </animate>
</div>

<!-- notes: 这里的备注已经优化了展示方式。它不再混在主内容中，而是使用了暗色调固定在屏幕底部展示，既方便演讲者阅读，又不干扰观众视觉。 -->

---

# 🎹 快捷键手册

- `Space` / `Enter`: 下一页
- `Backspace` / `Left`: 上一页
- `o`: **开启概览模式** (快速跳转)
- `g`: 输入数字快速跳转
- `n`: 切换备注显示
- `q`: 退出程序

---

<title>谢谢观看</title>
<subtitle>Enjoy Console PPT!</subtitle>

<p align="center">
  <animate type="rainbow">
    <b>GitHub: cnjowang/console_ppt</b>
  </animate>
</p>
