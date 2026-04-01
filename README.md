# Console PPT

一个基于终端的 PPT 演示工具，使用 Markdown 文件作为输入。

## 核心功能

### 1. Markdown 解析

- 使用 `---` 分割幻灯片
- 支持的 Markdown 元素：
  - 标题（H1-H6）
  - 段落（支持 **粗体**、*斜体*、`行内代码`）
  - 代码块（带语法高亮）
  - 有序列表 / 无序列表（支持多级嵌套）
  - 引用块
  - 表格
  - 图片（显示占位符）
  - 水平分割线
  - 空行（保留原文空行）
- 支持演讲者备注：`<!-- notes: 备注内容 -->`

### 2. 特殊语法

#### 标题页元素

- `<title>标题</title>` - 幻灯片主标题，带上下横线装饰，水平居中
- `<subtitle>子标题</subtitle>` - 幻灯片子标题，水平居中
- `<p align="center">内容</p>` - 居中段落

#### 标题页特性

- 包含 `<title>` 元素的页面被识别为标题页
- 标题页不显示进度条和页码
- 标题页不计入总页数
- title 和 subtitle 上下垂直居中
- 可在标题页下方继续添加其他内容

### 3. HTML 标签支持

#### 块级标签

| 标签 | 说明 | 支持的属性 |
|------|------|-----------|
| `<div>` | 块级容器 | `align`, `valign`, `style` |
| `<p>` | 段落 | `align`, `valign`, `style` |
| `<animate>` | 动画容器 | `type`, `speed`, `align`, `valign` |
| `<h1>`-`<h6>` | 标题 | `align`, `style` |

#### 行内标签

| 标签 | 说明 | 支持的属性 |
|------|------|-----------|
| `<strong>`, `<b>` | 粗体 | — |
| `<em>`, `<i>` | 斜体 | — |
| `<code>` | 行内代码 | — |
| `<a>` | 超链接 | `href` |
| `<span>` | 行内容器 | `style`, `align` |
| `<animate>` | 行内动画 | `type`, `speed` |
| `<br>` | 换行 | — |

#### 标签嵌套

块级标签内可嵌套行内标签，样式会正确叠加。局部动效标签支持与其他 HTML 标签深度嵌套：

```markdown
<animate type="rainbow">
  <div align="center">
    <h1>带彩虹动效的居中大标题</h1>
  </div>
</animate>
```

父元素的 `style` 或动画属性会与子元素的样式合并。

### 4. HTML 属性

#### align（水平对齐）

适用于 `<div>`、`<p>`、`<span>`。

| 值 | 说明 |
|----|------|
| `left` | 左对齐（默认） |
| `center` | 居中 |
| `right` | 右对齐 |
| `justify` | 两端对齐（实际为左对齐） |

#### valign（垂直对齐）

适用于 `<div>`、`<p>`。

| 值 | 说明 |
|----|------|
| `top` | 顶部对齐（默认） |
| `middle` / `center` | 垂直居中 |
| `bottom` | 底部对齐 |

#### style（行内 CSS）

适用于 `<div>`、`<p>`、`<span>`。

| CSS 属性 | 值示例 | 对应 Rich 样式 |
|----------|--------|---------------|
| `color` | `red`, `#ff0000` | 文本颜色 |
| `font-weight` | `bold` | 粗体 |
| `font-style` | `italic` | 斜体 |
| `text-decoration` | `underline` | 下划线 |

多个属性用 `;` 分隔：

```html
<span style="color: red; font-weight: bold">Red bold text</span>
```

#### href（链接地址）

适用于 `<a>`，渲染时在链接文字后显示 URL。

### 5. 幻灯片指令

通过 HTML 注释控制幻灯片行为：

#### hideprogress

隐藏当前幻灯片的进度条和页码：

```markdown
---

<!-- hideprogress -->

# Break Time

10 minute break
```

适用于过渡页、休息页、Q&A 页等场景。

### 6. TUI 渲染

- 使用 Textual 框架
- 支持颜色和样式
- 代码块使用 Rich 库进行彩色语法高亮（monokai 主题）
- 中文字符宽度正确处理（CJK 字符占 2 列宽度）
- 内容超出终端尺寸时自动截除，由用户控制每页内容长度

### 7. 标题渲染

标题不使用装饰符号，仅通过颜色区分级别：

| 级别 | 颜色 |
|------|------|
| H1 | 天蓝色 (bold cyan) |
| H2 | 橙色 (bold dark_orange) |
| H3 | 黄色 (bold yellow) |
| H4+ | 高亮白色 (bold bright_white) |

### 8. 导航功能

- 键盘导航：
  - `→` 或 `Space`：下一页
  - `←`：上一页
  - `Home`：第一页
  - `End`：最后一页
  - `g` + 数字：跳转到指定页
  - `/`：搜索（待实现）
  - `o`：概览模式（支持列表展示、快速导航与跳转）
  - `n`：切换演讲者备注
  - `?`：显示帮助
  - `q`：退出

### 9. 概览模式

- **进入方式**：按下 `o` 键开启。
- **列表显示**：显示所有幻灯片的编号和标题。
- **标题提取规则**（按优先级）：
  1. `<title>` 标签内容
  2. `<subtitle>` 标签内容
  3. 幻灯片内的第一个标题（H1-H6）
  4. 第一个非空文本元素（段落、引用、列表等）的第一行文字（自动清理 Markdown 和 HTML 标签）
- **交互操作**：
  - `↑` / `↓`：上下移动选择。
  - `Enter`：跳转到选中的幻灯片并关闭概览。
  - `Esc` 或 `o`：关闭概览窗口。
- **UI 样式**：
  - 采用白色双实线边框（double white）。
  - 在展示区域自适应居中显示。
  - 标题与内容间设有双实线分割线。

### 10. 进度指示器

- 位于屏幕底部
- 贯穿显示区域的细横线
- 已完成进度：灰色 (grey35)
- 未完成进度：暗灰色 (grey15)
- 页码显示在进度条上方右侧
- 标题页不显示进度条和页码
- 使用 `<!-- hideprogress -->` 可隐藏指定页的进度条和页码

### 11. 切换动效

- **动画类型**：基于重力的字符级独立坠落动效。
- **切出效果（Fall Out）**：当前幻灯片的所有非空白字符根据重力加速度公式 $y' = y + g \cdot t^2$ 向屏幕底部坠落。
- **切入效果（Fall In）**：新幻灯片的所有非空白字符从屏幕上方起始位置，根据重力加速度落位到目标坐标。
- **粒子化特性**：
  - 字符独立化：每个字符作为一个独立的物理粒子运动。
  - 随机延迟：每个粒子分配 0-0.4s 的随机启动延迟，形成错落有致的“沙化”坠落效果。
  - 样式保留：动画过程中保留字符的所有原始样式（颜色、加粗、代码高亮等）。
  - CJK 支持：正确处理中文字符占用 2 列宽度的物理特性，确保动画过程中间距不乱。
- **可配置性**：支持在配置文件中开启/关闭动效及调整动画时长。

### 12. 局部动效

- **语法**：使用 `<animate>` 标签包裹内容。
- **属性**：
  - `type`：动效类型（必填）。
  - `speed`：动画速度倍率（可选，默认 1.0）。
  - `color`：指定动画颜色（可选，目前支持 `pulse` 类型）。
- **支持类型**：
  - `pulse`：平滑的亮度呼吸效果。可配合 `color` 属性实现特定颜色的闪烁。
  - `rainbow`：文字颜色在彩虹色谱间循环。
  - `glitch`：极客风格的随机位置抖动。
  - `bounce`：文字上下弹跳。
  - `wave`：颜色在字符序列间像波浪一样流动（适合箭头 `>>>>` 或连续符号）。
- **嵌套特性**：支持样式继承。被 `<animate>` 包裹的所有嵌套 HTML 标签（如 `<h1>`, `<span>`, `<p>`）都将继承该动画效果。
- **实现原理**：基于 TUI 20FPS 刷新率，动态计算每个字符粒子的空间偏移或颜色样式。

### 13. 展示区域

- 可配置展示区域的宽度和高度
- 展示区域在终端中水平和垂直居中显示
- 无边框设计
- 展示区域内左右各有 2 列 padding，实际内容宽度 = display_width - 4
- 对齐计算基于实际内容宽度

### 13. 表格渲染

- 使用 Unicode 边框字符
- 标题行使用高亮白色
- 表格线使用暗淡灰色
- 支持中文字符宽度正确计算

## 配置文件

支持 YAML 配置文件，配置项包括：

```yaml
# 主题颜色
theme:
  title: "bold cyan"              # H1
  heading_h2: "bold dark_orange"  # H2
  heading_h3: "bold yellow"       # H3
  heading_h4: "bold bright_white" # H4+
  code: "green"
  code_bg: "#1e1e1e"
  quote: "italic dim"
  list_bullet: "cyan"
  progress_done: "grey35"         # 进度条已完成
  progress_todo: "grey15"         # 进度条未完成

# 显示设置
show_line_numbers: false
code_highlight: true
enable_animations: true           # 开启切换动效
animation_duration: 0.5           # 动画时长（秒）

# 展示区域尺寸
display_width: 120
display_height: 40
```

### 配置文件查找顺序

1. `-c` / `--config` 参数指定的路径
2. `~/.console_ppt/config.yaml`（用户全局配置）

### 默认配置

系统内置默认配置：
- `display_width`: 120
- `display_height`: 40
- `progress_done`: grey23
- `progress_todo`: grey15

## 项目结构

```
console_ppt/
├── pyproject.toml           # 项目配置
├── REQUIREMENTS.md          # 需求文档
├── console_ppt/
│   ├── __init__.py
│   ├── main.py              # 主程序入口
│   ├── parser.py            # Markdown / HTML 解析器
│   ├── widgets.py           # TUI 组件与渲染
│   └── config.py            # 配置管理
└── example/
    ├── demo.md              # 基础功能示例
    ├── html_demo.md         # HTML 标签示例
    ├── valign_demo.md       # 垂直对齐示例
    ├── nested_demo.md       # 嵌套标签示例
    ├── style_align_demo.md  # 样式与对齐示例
    ├── hideprogress_demo.md # 隐藏进度条示例
    └── .console_ppt.yaml    # 示例配置
```

## 使用方法

```bash
# 安装依赖
pip install textual rich pyyaml

# 运行（使用默认配置或 ~/.console_ppt/config.yaml）
python -m console_ppt.main example/demo.md

# 指定配置文件
python -m console_ppt.main example/demo.md -c /path/to/config.yaml
```

## 技术栈

- **语言**: Python 3.10+
- **TUI 框架**: Textual
- **富文本渲染**: Rich
- **配置解析**: PyYAML


## 待开发功能

### 局部动效

* 左右移动：指定的字符在展示时不停左右移动

### 进度条显示控制策略

* 能在markdown文档内全局控制是否显示进度条
* 在markdown文档内全局未关闭进度条的情况下，可以隐藏某个页的进度条
