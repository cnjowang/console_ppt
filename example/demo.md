<title>Making a console based PPT 字符界面的PPT</title>
<subtitle>Joseph</subtitle>
---

# Console PPT Demo
Welcome to **Console PPT**, a terminal-based presentation tool!

1. Keypoint 1
1. Keypoint 2
1. Keypoint 3

<p align="right">right aligned block</p>

<p align="center">center aligned block</p>

---

# Features

## Core Features

- **Markdown-based**: Write slides in familiar Markdown syntax
- **TUI Interface**: Beautiful terminal UI with colors and styles
- **Keyboard Navigation**: Intuitive keyboard shortcuts
- **Code Highlighting**: Syntax highlighting for code blocks

## Another level 2

### Level 3

#### Level 4

##### Level 5

---

# Markdown Support

## Supported Elements

- Headings (H1-H6)
- **Bold** and *italic* text
- `inline code` blocks
- Code blocks with syntax highlighting
- Bullet and numbered lists
- Blockquotes

---

# Code Example

Here's a Python code example:

```python
def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

print(hello("World"))
```

以上是代码演示
---

# Lists Example

## Features in action

- First item
- Second item
  - Nested item
    - Level 3.1
    - Level 3.2
  - Another nested item
- Third item

<!-- notes: Don't forget to mention nested lists! -->

---

# Blockquotes

> "The best way to predict the future
> is to invent it."
>
> — Alan Kay

---

# Navigation Shortcuts

| Key | Action |
|-----|--------|
| → / Space | Next slide |
| ← | Previous slide |
| Home / End | First / Last slide |
| g + number | Go to slide N |
| / | Search |
| n | Toggle notes |
| ? | Show help |
| q | 退出 |

---

# Speaker Notes

This slide has speaker notes!

<!-- notes: Press 'n' to toggle speaker notes visibility. These notes are only visible to the presenter. -->

---

# Thank You!

## Get Started

```bash
console-ppt your-presentation.md
```

Questions?
