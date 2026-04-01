# Local Animations Demo

<title>局部动效演示</title>
<subtitle>让 PPT 动起来</subtitle>

---

# 基础动效

- **呼吸灯 (Pulse)**: <animate type="pulse">注意这里，我在闪烁...</animate>
- **彩色呼吸灯 (Pulse with Color)**: <animate type="pulse" color="bright_yellow">警告：红色闪烁！</animate>
- **彩虹循环 (Rainbow)**: <animate type="rainbow" speed="1.5">五彩斑斓的文字效果</animate>
- **故障艺术 (Glitch)**: <animate type="glitch">极客风格的系统故障感</animate>


- **弹跳 (Bounce)**: <animate type="bounce">我跳，我跳，我跳跳跳！</animate>

---

# 进阶动效

- **波浪 (Wave)**: 
<animate type="wave" speed="2.0">>>>>>>>> 蠕动的箭头 >>>>>>>>></animate>

- **组合使用**:
<div align="center">
        <animate type="rainbow"><h1>大标题彩虹动效</h1></animate>
        <animate type="bounce" speed="0.5"><p>缓慢弹跳的副标题</p></animate>
</div>

---

# 语法说明

使用 `<animate>` 标签包裹需要动效的内容：

```html
<animate type="pulse" speed="1.0">
  闪烁的内容
</animate>
```

**支持的类型 (type)**:
- `pulse`: 亮度呼吸
- `rainbow`: 颜色循环
- `glitch`: 随机抖动
- `bounce`: 上下弹跳
- `wave`: 颜色波浪

**支持的属性**:
- `speed`: 动画速度缩放（默认 1.0）
