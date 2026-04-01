"""TUI widgets for console-ppt."""

import math
import random
import re
import time

from rich.console import Console
from rich.segment import Segment
from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Input, ListItem, ListView, Static

from .config import Config
from .parser import Element, ElementType, Slide


class LinesRenderable:
    """Helper to render particles with independent gravity and local animations."""

    def __init__(
        self,
        particles: list[tuple],
        progress: float,
        phase: int,
        height: int,
        width: int,
        current_time: float,
    ):
        self.particles = particles  # (char, x, y, style, delay, anim_meta)
        self.progress = progress
        self.phase = phase
        self.height = height
        self.width = width
        self.time = current_time

    def __rich_console__(self, console, options):
        # Create a buffer for the display area
        display_lines = [{} for _ in range(self.height + 2)]
        
        max_delay = 0.4
        
        # Colors for rainbow/wave animation
        rainbow_colors = ["red", "orange3", "yellow", "green", "cyan", "blue", "magenta"]
        
        for char, x, y, style, delay, anim_meta in self.particles:
            # 1. Calculate gravity transition
            local_t = max(0.0, min(1.0, (self.progress - delay) / (1.0 - max_delay)))
            
            y_offset = 0
            if self.phase == 1:
                y_offset = int(self.height * (local_t**2))
            elif self.phase == 2:
                y_offset = -int(self.height * ((1.0 - local_t) ** 2))
            
            target_y = y + y_offset
            target_x = x
            target_style = style
            
            # 2. Apply local animations
            if anim_meta:
                anim_type = anim_meta.get("anim")
                speed = float(anim_meta.get("speed", 1.0))
                
                if anim_type == "pulse":
                    # Oscillate brightness or color
                    if math.sin(self.time * speed * 6) < 0:
                        target_style += Style(dim=True)
                    else:
                        pulse_color = anim_meta.get("color")
                        if pulse_color:
                            target_style += Style(color=pulse_color)
                
                elif anim_type == "rainbow":
                    color_idx = int(self.time * speed * 5) % len(rainbow_colors)
                    target_style += Style(color=rainbow_colors[color_idx])
                
                elif anim_type == "glitch":
                    if random.random() < 0.1:
                        target_x += random.randint(-1, 1)
                        target_y += random.randint(-1, 1)
                
                elif anim_type == "bounce":
                    y_bounce = int(math.sin(self.time * speed * 8) * 1.5)
                    target_y += y_bounce
                
                elif anim_type == "wave":
                    wave_idx = int(self.time * speed * 8 + x * 0.5) % len(rainbow_colors)
                    target_style += Style(color=rainbow_colors[wave_idx])

            if 0 <= target_y < len(display_lines):
                # Calculate char width correctly
                is_cjk = ("\u4e00" <= char <= "\u9fff" or 
                          "\u3000" <= char <= "\u303f" or 
                          "\uff00" <= char <= "\uffef")
                width = 2 if is_cjk else 1
                display_lines[target_y][target_x] = (Segment(char, target_style), width)

        # Yield each line, filling gaps with spaces
        for line_dict in display_lines:
            if not line_dict:
                yield Segment.line()
                continue
                
            last_x = 0
            # Sort by x coordinate to handle segments in order
            for x in sorted(line_dict.keys()):
                if x > last_x:
                    yield Segment(" " * (x - last_x))
                segment, width = line_dict[x]
                yield segment
                last_x = x + width 
            yield Segment.line()


class SlideWidget(Widget):
    """Widget to render a single slide."""

    # CSS padding values (must match DEFAULT_CSS)
    HORIZONTAL_PADDING = 4  # Left 2 + Right 2

    DEFAULT_CSS = """
    SlideWidget {
        height: 1fr;
        padding: 1 2;
        overflow: hidden;
    }

    SlideWidget .title {
        text-align: center;
        margin-bottom: 1;
    }

    SlideWidget .heading {
        margin: 1 0;
    }

    SlideWidget .code-block {
        margin: 1 0;
        padding: 1;
    }

    SlideWidget .paragraph {
        margin: 1 0;
    }

    SlideWidget .list-item {
        margin: 0 0 0 2;
    }

    SlideWidget .blockquote {
        margin: 1 0 1 2;
        padding: 0 1;
    }
    """

    slide: reactive[Slide | None] = reactive(None)
    show_notes: reactive[bool] = reactive(False)
    # Animation states
    animation_progress: reactive[float] = reactive(0.0)
    animation_phase: reactive[int] = reactive(0)  # 0: none, 1: fall out, 2: fall in
    
    current_particles: list[tuple] = []
    next_particles: list[tuple] = []
    _animation_timer: Timer | None = None

    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config

    def watch_slide(self, slide: Slide | None) -> None:
        """Update displayed slide."""
        if slide is not None and self.animation_phase == 0:
            self._update_content(slide)

    def _render_slide(self, slide: Slide) -> None:
        """Render the slide content."""
        # This will be replaced by update() calls
        pass

    def compose(self) -> ComposeResult:
        # We handle rendering directly in render() now
        return []

    def _on_mount(self) -> None:
        if self.slide:
            self._update_content(self.slide)
        # Start a background timer for local animations (pulse, rainbow, etc.)
        self._animation_timer = self.set_interval(1 / 20, self.refresh)

    def _on_unmount(self) -> None:
        if self._animation_timer:
            self._animation_timer.stop()

    def _update_content(self, slide: Slide) -> None:
        """Update the slide content particle cache."""
        text = self._build_slide_text(slide)
        self.current_particles = self._render_to_particles(text)
        self.refresh()

    def _render_to_particles(self, text: Text) -> list[tuple]:
        """Render Rich Text to a list of individual character particles."""
        width = self._get_effective_display_width()
        console = Console(width=width, force_terminal=True)
        lines = console.render_lines(text, pad=False)
        
        particles = []
        for y, line in enumerate(lines):
            x = 0
            for segment in line:
                if segment.control:
                    continue
                
                # Extract animation metadata from Rich style if present
                anim_meta = segment.style.meta if segment.style else {}
                
                # Split segment into characters
                for char in segment.text:
                    if not char.isspace():
                        # Store (char, x, y, style, random_delay, anim_meta)
                        particles.append((char, x, y, segment.style, random.uniform(0.0, 0.4), anim_meta))
                    # Advance x by character display width
                    x += self._get_display_width(char)
        return particles

    def render(self) -> LinesRenderable:
        """Render the slide with animations."""
        # Use config height/width or fallback to widget size
        height = self.config.display_height or (self.size.height if self.size.height > 0 else 40)
        width = self.config.display_width or (self.size.width if self.size.width > 0 else 80)
        
        particles = self.current_particles if self.animation_phase != 2 else self.next_particles
        
        return LinesRenderable(
            particles=particles,
            progress=self.animation_progress,
            phase=self.animation_phase,
            height=height,
            width=width,
            current_time=time.time()
        )

    def animate_to_slide(self, new_slide: Slide, show_notes: bool = False) -> None:
        """Trigger per-character gravity animation to a new slide."""
        if not self.config.enable_animations:
            self.update_slide(new_slide, show_notes)
            return

        # Prepare next slide
        self.show_notes = show_notes
        next_text = self._build_slide_text(new_slide)
        self.next_particles = self._render_to_particles(next_text)
        
        duration = self.config.animation_duration
        
        def start_phase_2():
            self.slide = new_slide
            self.current_particles = self.next_particles
            self.animation_phase = 2
            self.animation_progress = 0.0
            self.animate(
                "animation_progress",
                value=1.0,
                duration=duration / 2,
                easing="linear",
                on_complete=finish_animation
            )

        def finish_animation():
            self.animation_phase = 0
            self.animation_progress = 0.0
            self.refresh()

        # Phase 1: Fall out
        self.animation_phase = 1
        self.animation_progress = 0.0
        self.animate(
            "animation_progress",
            value=1.0,
            duration=duration / 2,
            easing="linear",
            on_complete=start_phase_2
        )

    def _build_slide_text(self, slide: Slide) -> Text:
        """Build Rich Text from slide elements."""
        text = Text()

        # Check if slide has title/subtitle (special layout)
        has_title = any(e.type == ElementType.TITLE for e in slide.elements)
        has_subtitle = any(e.type == ElementType.SUBTITLE for e in slide.elements)

        if has_title or has_subtitle:
            # Special centered layout for title/subtitle
            return self._build_title_slide_text(slide)

        # Elements that add trailing blank line (their own blank line before next element)
        trailing_blank_elements = {
            ElementType.HEADING,
            ElementType.LIST,
            ElementType.ORDERED_LIST,
            ElementType.BLOCKQUOTE,
            ElementType.TABLE,
        }

        i = 0
        while i < len(slide.elements):
            elem = slide.elements[i]

            # Special case: skip blank line after heading/code_block (they already add their own spacing)
            if elem.type == ElementType.BLANK_LINE:
                if i > 0 and slide.elements[i - 1].type in trailing_blank_elements:
                    i += 1
                    continue

            self._render_element(text, elem)
            i += 1

        # Show notes if enabled
        if self.show_notes and slide.notes:
            text.append("\n\n")
            text.append("📝 Notes: ", style="bold yellow")
            text.append(slide.notes, style="italic dim")

        return text

    def _build_title_slide_text(self, slide: Slide) -> Text:
        """Build text for title slide with centered layout."""
        text = Text()

        # Get display height for centering
        height = self.config.display_height or 24

        # Collect title, subtitle, and other elements
        title_elem = None
        subtitle_elem = None
        other_elements = []
        for elem in slide.elements:
            if elem.type == ElementType.TITLE:
                title_elem = elem
            elif elem.type == ElementType.SUBTITLE:
                subtitle_elem = elem
            elif elem.type not in (ElementType.BLANK_LINE,):
                other_elements.append(elem)

        # Calculate title/subtitle content height for vertical centering
        title_content_lines = 0
        if title_elem:
            title_content_lines += 3  # Title with border takes 3 lines
        if subtitle_elem:
            title_content_lines += 1  # One blank line between title and subtitle
            title_content_lines += 1  # Subtitle line

        # Reserve 2 lines for progress bar and page info at bottom
        available_height = height - 2

        # If there are other elements, don't center as much
        if other_elements:
            top_padding = max(0, min(2, (available_height - title_content_lines) // 4))
        else:
            top_padding = max(0, (available_height - title_content_lines) // 2)

        # Add top padding
        for _ in range(top_padding):
            text.append("\n")

        # Render title with border
        if title_elem:
            self._render_title(text, title_elem)

        # Render subtitle
        if subtitle_elem:
            text.append("\n")  # Blank line between title and subtitle
            self._render_subtitle(text, subtitle_elem)

        # Render other elements
        for elem in other_elements:
            if elem.type == ElementType.CENTERED_PARAGRAPH:
                text.append("\n")
                self._render_centered_paragraph(text, elem)
            else:
                self._render_element(text, elem)

        # Show notes if enabled
        if self.show_notes and slide.notes:
            text.append("\n\n")
            text.append("📝 Notes: ", style="bold yellow")
            text.append(slide.notes, style="italic dim")

        return text

    def _render_element(self, text: Text, elem: Element) -> None:
        """Render a single element to Text."""
        if elem.type == ElementType.HEADING:
            self._render_heading(text, elem)
        elif elem.type == ElementType.PARAGRAPH:
            self._render_paragraph(text, elem)
        elif elem.type == ElementType.CODE_BLOCK:
            self._render_code_block(text, elem)
        elif elem.type == ElementType.LIST:
            self._render_list(text, elem, ordered=False)
        elif elem.type == ElementType.ORDERED_LIST:
            self._render_list(text, elem, ordered=True)
        elif elem.type == ElementType.BLOCKQUOTE:
            self._render_blockquote(text, elem)
        elif elem.type == ElementType.IMAGE:
            self._render_image(text, elem)
        elif elem.type == ElementType.TABLE:
            self._render_table(text, elem)
        elif elem.type == ElementType.TITLE:
            self._render_title(text, elem)
        elif elem.type == ElementType.SUBTITLE:
            self._render_subtitle(text, elem)
        elif elem.type == ElementType.CENTERED_PARAGRAPH:
            self._render_centered_paragraph(text, elem)
        elif elem.type == ElementType.HTML_ELEMENT:
            # Block-level HTML element
            self._render_html_element(text, elem)
            text.append("\n")
        elif elem.type == ElementType.BLANK_LINE:
            text.append("\n")
        elif elem.type == ElementType.HR:
            text.append("─" * 50, style="dim")
            text.append("\n")

    def _get_effective_display_width(self) -> int:
        """Get effective display width accounting for CSS padding.

        The widget has padding: 1 2 (top/bottom: 1, left/right: 2),
        so total horizontal padding is 4 columns.
        """
        width = self.config.display_width or 80
        return max(1, width - self.HORIZONTAL_PADDING)

    def _get_display_width(self, text: str) -> int:
        """Calculate the display width of a string, accounting for CJK characters."""
        width = 0
        for char in text:
            # CJK characters and fullwidth characters have width 2
            if "\u4e00" <= char <= "\u9fff":  # CJK Unified Ideographs
                width += 2
            elif "\u3000" <= char <= "\u303f":  # CJK Symbols and Punctuation
                width += 2
            elif "\uff00" <= char <= "\uffef":  # Halfwidth and Fullwidth Forms
                width += 2
            else:
                width += 1
        return width

    def _pad_to_width(self, text: str, target_width: int) -> str:
        """Pad text to target display width, accounting for CJK characters."""
        current_width = self._get_display_width(text)
        if current_width < target_width:
            return text + " " * (target_width - current_width)
        return text

    def _truncate_to_width(self, text: str, max_width: int) -> str:
        """Truncate text to fit within max display width, accounting for CJK characters."""
        result = []
        current_width = 0
        for char in text:
            char_width = (
                2
                if (
                    "\u4e00" <= char <= "\u9fff"
                    or "\u3000" <= char <= "\u303f"
                    or "\uff00" <= char <= "\uffef"
                )
                else 1
            )
            if current_width + char_width > max_width:
                break
            result.append(char)
            current_width += char_width
        return "".join(result)

    def _render_title(self, text: Text, elem: Element) -> None:
        """Render a title with horizontal lines above and below, centered."""
        title = elem.content
        width = self._get_effective_display_width()

        # Calculate display width (CJK chars are 2 columns wide)
        title_display_width = self._get_display_width(title)

        # Line width is slightly longer than title
        line_width = title_display_width + 4  # 2 extra chars on each side
        line = "─" * line_width

        # Center horizontally
        left_pad = (width - line_width) // 2
        padding = " " * max(0, left_pad)

        # Render with H1 color (cyan)
        style = self.config.theme.title
        text.append(padding + line + "\n", style=style)
        text.append(padding + "  " + title + "  " + "\n", style=style)
        text.append(padding + line + "\n", style=style)

    def _render_subtitle(self, text: Text, elem: Element) -> None:
        """Render a subtitle, horizontally centered."""
        subtitle = elem.content
        width = self._get_effective_display_width()

        # Center horizontally using actual display width
        subtitle_width = self._get_display_width(subtitle)
        left_pad = (width - subtitle_width) // 2
        padding = " " * max(0, left_pad)

        # Render with H2 color (dark_orange)
        style = self.config.theme.heading_h2
        text.append(padding + subtitle + "\n", style=style)

    def _render_centered_paragraph(self, text: Text, elem: Element) -> None:
        """Render a centered paragraph."""
        content = elem.content
        width = self._get_effective_display_width()

        # Center horizontally using actual display width
        content_width = self._get_display_width(content)
        left_pad = (width - content_width) // 2
        padding = " " * max(0, left_pad)

        text.append(padding)
        self._render_inline(text, content)
        text.append("\n")

    def _render_heading(self, text: Text, elem: Element) -> None:
        """Render a heading with colors based on level."""
        # Choose color based on heading level
        if elem.level == 1:
            style = self.config.theme.title  # bold cyan
        elif elem.level == 2:
            style = self.config.theme.heading_h2  # bold dark_orange
        elif elem.level == 3:
            style = self.config.theme.heading_h3  # bold yellow
        else:
            style = self.config.theme.heading_h4  # bold white

        text.append(elem.content, style=style)
        text.append("\n\n")  # Add empty line after heading

    def _render_paragraph(self, text: Text, elem: Element) -> None:
        """Render a paragraph with inline formatting."""
        self._render_inline(text, elem.content)
        text.append("\n")

    def _render_inline(self, text: Text, content: str) -> None:
        """Render inline markdown formatting including HTML tags."""
        pos = 0
        content_len = len(content)

        while pos < content_len:
            # Find the next tag start
            tag_start = content.find("<", pos)

            if tag_start == -1:
                # No more tags, process remaining content
                remaining = content[pos:]
                if remaining:
                    self._render_inline_code_and_markdown(text, remaining)
                break

            # Process text before the tag
            if tag_start > pos:
                self._render_inline_code_and_markdown(text, content[pos:tag_start])

            # Parse the tag
            tag_end = content.find(">", tag_start)
            if tag_end == -1:
                # Malformed tag, treat as text
                text.append(content[tag_start:])
                break

            full_tag = content[tag_start : tag_end + 1]

            # Check for self-closing br tag
            br_match = re.match(r"<br\s*/?>", full_tag, re.IGNORECASE)
            if br_match:
                text.append("\n")
                pos = tag_end + 1
                continue

            # Check for end tag
            end_tag_match = re.match(r"</(\w+)>", full_tag, re.IGNORECASE)
            if end_tag_match:
                # Unexpected end tag, skip it
                pos = tag_end + 1
                continue

            # Check for start tag
            start_tag_match = re.match(r"<(\w+)([^>]*)>", full_tag, re.IGNORECASE)
            if start_tag_match:
                tag = start_tag_match.group(1).lower()
                attrs_str = start_tag_match.group(2)

                if tag in ("strong", "b", "em", "i", "code", "a", "span", "animate"):
                    # Find the matching end tag
                    end_tag_pattern = f"</{tag}>"
                    search_start = tag_end + 1
                    # Use regex for case-insensitive search
                    end_tag_match = re.search(
                        re.escape(end_tag_pattern),
                        content[search_start:],
                        re.IGNORECASE,
                    )

                    if end_tag_match:
                        # Extract tag content
                        tag_content = content[
                            search_start : search_start + end_tag_match.start()
                        ]

                        # Parse attributes for <a>, <span>, and <animate>
                        attrs = {}
                        if tag in ("a", "span", "animate"):
                            for attr_match in re.finditer(
                                r'(\w+)=["\']([^"\']+)["\']', attrs_str
                            ):
                                attrs[attr_match.group(1)] = attr_match.group(2)

                        self._render_inline_html_tag(text, tag, attrs, tag_content)
                        pos = search_start + end_tag_match.end()
                    else:
                        # No matching end tag, treat as text
                        text.append(full_tag)
                        pos = tag_end + 1
                else:
                    # Unsupported tag, skip
                    pos = tag_end + 1
            else:
                # Unknown tag format, treat as text
                text.append(full_tag)
                pos = tag_end + 1

    def _render_inline_code_and_markdown(self, text: Text, content: str) -> None:
        """Render inline code and markdown bold/italic."""
        # Process inline code first
        if "`" in content:
            code_parts = re.split(r"(`[^`]+`)", content)
            for code_part in code_parts:
                if code_part.startswith("`") and code_part.endswith("`"):
                    # Inline code
                    code = code_part[1:-1]
                    text.append(code, style=self.config.theme.code)
                elif code_part:
                    # Process bold and italic
                    self._render_bold_italic(text, code_part)
        else:
            # Process bold and italic
            self._render_bold_italic(text, content)

    def _render_inline_html_tag(
        self, text: Text, tag: str, attrs: dict, content: str
    ) -> None:
        """Render inline HTML tags within text."""
        # Get the base style for this tag
        base_style = ""
        if tag in ("strong", "b"):
            base_style = "bold"
        elif tag in ("em", "i"):
            base_style = "italic"
        elif tag == "code":
            base_style = self.config.theme.code
        elif tag == "a":
            base_style = "underline cyan"
        elif tag == "span":
            style_str = attrs.get("style", "")
            base_style = self._parse_css_style(style_str)
        elif tag == "animate":
            anim_type = attrs.get("type", "pulse")
            anim_speed = attrs.get("speed", "1.0")
            anim_color = attrs.get("color", "")
            # Store animation info in Style meta
            base_style = Style(meta={"anim": anim_type, "speed": anim_speed, "color": anim_color})
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            # Map HTML headings to theme styles
            level = int(tag[1])
            if level == 1:
                base_style = self.config.theme.title
            elif level == 2:
                base_style = self.config.theme.heading_h2
            elif level == 3:
                base_style = self.config.theme.heading_h3
            else:
                base_style = self.config.theme.heading_h4

        # Special handling for links
        if tag == "a":
            href = attrs.get("href", "")
            # Append content with link style
            if content:
                text.append(content, style="underline cyan")
            if href:
                text.append(f" ({href})", style="dim")
            return

        # For other tags, check if content has nested HTML
        has_nested_html = bool(
            re.search(r"<\w+[^>]*>.*?</\w+>", content, re.DOTALL | re.IGNORECASE)
        )

        if has_nested_html:
            # Content has nested HTML, render recursively
            start_len = len(text)
            self._render_inline(text, content)
            # Apply base style to the entire range of nested content
            if base_style:
                text.stylize(base_style, start_len, len(text))
        else:
            # Simple content without nested HTML, append directly with style
            if base_style:
                text.append(content, style=base_style)
            else:
                text.append(content)

    def _render_bold_italic(self, text: Text, content: str) -> None:
        """Render bold and italic text."""
        # Split by bold (**text** or __text__)
        parts = re.split(r"(\*\*[^*]+\*\*|__[^_]+__)", content)

        for part in parts:
            if (part.startswith("**") and part.endswith("**")) or (
                part.startswith("__") and part.endswith("__")
            ):
                # Bold text
                bold_content = part[2:-2]
                text.append(bold_content, style="bold")
            elif part:
                # Split by italic (*text* or _text_)
                italic_parts = re.split(r"(\*[^*]+\*|_[^_]+_)", part)
                for ip in italic_parts:
                    if (ip.startswith("*") and ip.endswith("*")) or (
                        ip.startswith("_") and ip.endswith("_")
                    ):
                        italic_content = ip[1:-1]
                        text.append(italic_content, style="italic")
                    else:
                        text.append(ip)

    def _render_code_block(self, text: Text, elem: Element) -> None:
        """Render a code block with optional syntax highlighting."""
        from io import StringIO
        from rich.console import Console
        from rich.syntax import Syntax

        # Try to use syntax highlighting
        if self.config.code_highlight and elem.language:
            try:
                syntax = Syntax(
                    elem.content,
                    elem.language,
                    theme="monokai",
                    line_numbers=self.config.show_line_numbers,
                    word_wrap=False,
                )
                # Render Syntax to Text using a Console
                console = Console(
                    file=StringIO(), force_terminal=True, legacy_windows=False
                )
                console.print(syntax)
                highlighted = console.file.getvalue()
                # Parse ANSI codes back to Rich Text
                text.append_text(Text.from_ansi(highlighted))
                text.append("\n")
                return
            except Exception:
                pass

        # Fallback: render without highlighting
        for line in elem.content.split("\n"):
            text.append("  ")
            text.append(line, style=self.config.theme.code)
            text.append("\n")

    def _render_list(self, text: Text, elem: Element, ordered: bool = False) -> None:
        """Render a list with support for nested levels."""
        # Use list_items if available (new format), otherwise fall back to items
        items_to_render = (
            elem.list_items if elem.list_items else [(0, item) for item in elem.items]
        )

        # Different bullet styles for different levels (unordered list)
        bullets = ["•", "◦", "▪", "▫", "‣", "⁃"]

        for idx, (level, item) in enumerate(items_to_render):
            indent = "  " * (level + 1)
            if ordered:
                # Ordered list: show number
                bullet = f"{idx + 1}."
            else:
                # Unordered list: show bullet
                bullet = bullets[level % len(bullets)]
            text.append(f"{indent}{bullet} ", style=self.config.theme.list_bullet)
            self._render_inline(text, item)
            text.append("\n")
        text.append("\n")  # Add empty line after list

    def _render_blockquote(self, text: Text, elem: Element) -> None:
        """Render a blockquote."""
        lines = elem.content.split("\n")
        for line in lines:
            text.append("  │ ", style=self.config.theme.quote)
            # Process inline HTML in blockquote lines
            line_text = Text()
            self._render_inline(line_text, line)
            text.append_text(line_text)
            text.append("\n")
        text.append("\n")  # Add empty line after blockquote

    def _render_image(self, text: Text, elem: Element) -> None:
        """Render an image placeholder."""
        alt_text = elem.items[0] if elem.items else "Image"
        text.append("  🖼 ", style="dim")
        text.append(f"[{alt_text}]", style="italic dim")
        text.append("\n")

    def _render_html_element(self, text: Text, elem: Element) -> None:
        """Render an HTML element with tag and attributes."""
        tag = elem.html_tag
        attrs = elem.html_attrs
        content = elem.content

        # Self-closing tags
        if tag == "br":
            text.append("\n")
            return

        # Block-level elements with alignment, style, and vertical align
        if tag in ("div", "p", "animate", "h1", "h2", "h3", "h4", "h5", "h6"):
            align = attrs.get("align", "left")
            valign = attrs.get("valign", "top")
            style_str = attrs.get("style", "")
            rich_style = self._parse_css_style(style_str)
            
            # Map animate and headings to base_style
            if tag == "animate":
                anim_type = attrs.get("type", "pulse")
                anim_speed = attrs.get("speed", "1.0")
                anim_color = attrs.get("color", "")
                rich_style = Style(meta={"anim": anim_type, "speed": anim_speed, "color": anim_color})
            elif tag.startswith("h"):
                level = int(tag[1])
                if level == 1: rich_style = self.config.theme.title
                elif level == 2: rich_style = self.config.theme.heading_h2
                elif level == 3: rich_style = self.config.theme.heading_h3
                else: rich_style = self.config.theme.heading_h4

            # Prepare styled content
            has_nested_html = bool(
                re.search(r"<\w+[^>]*>.*?</\w+>", content, re.DOTALL | re.IGNORECASE)
            )
            styled_text = Text()
            if has_nested_html:
                self._render_inline(styled_text, content)
                # Apply base rich_style to existing spans
                if rich_style:
                    # If we have spans, we need to merge styles
                    new_text = Text(str(styled_text))
                    if styled_text.spans:
                        for span in styled_text.spans:
                            merged_style = f"{rich_style} {span.style}" if span.style else rich_style
                            new_text.stylize(merged_style, span.start, span.end)
                        styled_text = new_text
                    else:
                        styled_text.stylize(rich_style)
            else:
                styled_text.append(content, style=rich_style)

            # Ensure rich_style (meta) is applied to the whole text
            if rich_style:
                styled_text.stylize(rich_style)

            # Route to appropriate rendering method
            if valign in ("middle", "center", "bottom"):
                self._render_vcentered_styled_content(text, styled_text, align, valign)
            else:
                self._render_aligned_styled_content(text, styled_text, align)
            return

        # Inline elements
        if tag in ("strong", "b"):
            text.append(content, style="bold")
        elif tag in ("em", "i"):
            text.append(content, style="italic")
        elif tag == "code":
            text.append(content, style=self.config.theme.code)
        elif tag == "a":
            href = attrs.get("href", "")
            # Show as underlined cyan with optional link indicator
            if href:
                text.append(content, style="underline cyan")
                text.append(f" ({href})", style="dim")
            else:
                text.append(content, style="underline cyan")
        elif tag == "span":
            # Check for style and align attributes
            style_str = attrs.get("style", "")
            rich_style = self._parse_css_style(style_str)
            align = attrs.get("align", "")

            # Handle align attribute for span
            if align in ("center", "right"):
                # For inline align, we add padding based on available width
                content_width = self._get_display_width(content)
                width = self._get_effective_display_width()

                if align == "center":
                    left_pad = max(0, (width - content_width) // 2)
                    text.append(" " * left_pad)
                elif align == "right":
                    left_pad = max(0, width - content_width)
                    text.append(" " * left_pad)

            text.append(content, style=rich_style)
        elif tag == "blockquote":
            self._render_blockquote(
                text, Element(type=ElementType.BLOCKQUOTE, content=content)
            )
        elif tag in ("ul", "ol"):
            # Parse list items from content (simplified)
            items = [line.strip() for line in content.split("\n") if line.strip()]
            is_ordered = tag == "ol"
            list_elem = Element(
                type=ElementType.ORDERED_LIST if is_ordered else ElementType.LIST,
                content="",
                list_items=[(0, item) for item in items],
            )
            self._render_list(text, list_elem, ordered=is_ordered)
        else:
            # Unknown tag, render content as-is
            text.append(content)

    def _render_aligned_content(self, text: Text, content: str, align: str) -> None:
        """Render content with specified alignment."""
        # Use effective display width (accounting for CSS padding)
        width = self._get_effective_display_width()
        lines = content.split("\n")

        for line in lines:
            # Create a sub-text with the line content (to handle inline HTML)
            line_text = Text()
            self._render_inline(line_text, line)
            # Get plain text content for accurate width calculation
            plain_text = line_text.plain
            line_width = self._get_display_width(plain_text)

            # Truncate content if it exceeds display width
            if line_width > width:
                # Truncate plain text and rebuild line_text
                truncated = self._truncate_to_width(plain_text, width)
                line_text = Text()
                self._render_inline(line_text, truncated)
                plain_text = line_text.plain
                line_width = self._get_display_width(plain_text)

            if align == "center":
                left_pad = max(0, (width - line_width) // 2)
                padding = " " * left_pad
                text.append(padding)
                text.append_text(line_text)
                text.append("\n")
            elif align == "right":
                left_pad = max(0, width - line_width)
                padding = " " * left_pad
                text.append(padding)
                text.append_text(line_text)
                text.append("\n")
            elif align == "justify":
                # For justify, we just left-align (no word wrapping in terminal)
                text.append_text(line_text)
                text.append("\n")
            else:  # left (default)
                text.append_text(line_text)
                text.append("\n")

    def _render_aligned_styled_content(
        self, text: Text, styled_text: Text, align: str
    ) -> None:
        """Render already styled content with specified alignment."""
        # Use effective display width (accounting for CSS padding)
        width = self._get_effective_display_width()

        # Get the text as string for splitting
        full_text = str(styled_text)
        lines = full_text.split("\n")

        # Track character position for span mapping
        char_pos = 0

        for line_idx, line in enumerate(lines):
            if not line:
                text.append("\n")
                continue

            # Calculate width of this line
            line_width = self._get_display_width(line)

            # Truncate if needed
            if line_width > width:
                line = self._truncate_to_width(line, width)
                line_width = self._get_display_width(line)

            # Create a Text object for this line
            line_text_obj = Text(line)

            # Copy applicable spans from styled_text to line_text_obj
            line_start = char_pos
            line_end = char_pos + len(line)

            for span in styled_text.spans:
                # Check if span overlaps with this line
                span_start = max(0, span.start - line_start)
                span_end = min(len(line), span.end - line_start)

                if span_start < span_end and span_end > 0:
                    # This span applies to this line
                    line_text_obj.stylize(span.style, span_start, span_end)

            if align == "center":
                left_pad = max(0, (width - line_width) // 2)
                padding = " " * left_pad
                text.append(padding)
                text.append_text(line_text_obj)
                text.append("\n")
            elif align == "right":
                left_pad = max(0, width - line_width)
                padding = " " * left_pad
                text.append(padding)
                text.append_text(line_text_obj)
                text.append("\n")
            elif align == "justify":
                text.append_text(line_text_obj)
                text.append("\n")
            else:  # left (default)
                text.append_text(line_text_obj)
                text.append("\n")

            # Update char position (add line length + 1 for newline)
            char_pos += len(line) + 1

    def _render_vcentered_content(
        self, text: Text, content: str, align: str, valign: str
    ) -> None:
        """Render content with vertical alignment.

        Args:
            text: The Text object to append to
            content: The content to render
            align: Horizontal alignment (left, center, right)
            valign: Vertical alignment (top, middle, bottom)
        """
        # Get display dimensions
        width = self._get_effective_display_width()
        height = self.config.display_height or 40
        # Reserve 2 lines for progress bar and page info at bottom
        effective_height = max(1, height - 2)

        # First, render the content to calculate its height
        content_text = Text()
        self._render_inline(content_text, content)
        content_str = str(content_text)

        # Count lines (including empty lines)
        content_lines = content_str.split("\n")
        content_height = len(content_lines)

        # Calculate vertical padding
        if valign in ("middle", "center"):
            top_padding = max(0, (effective_height - content_height) // 2)
        elif valign == "bottom":
            top_padding = max(0, effective_height - content_height)
        else:  # top (default)
            top_padding = 0

        # Add top padding (empty lines)
        for _ in range(top_padding):
            text.append("\n")

        # Track character position for span mapping
        char_pos = 0

        # Now render each line with horizontal alignment and preserve styles
        for line in content_lines:
            if not line.strip():
                text.append("\n")
                char_pos += len(line) + 1
                continue

            line_width = self._get_display_width(line)

            # Truncate if needed
            if line_width > width:
                line = self._truncate_to_width(line, width)
                line_width = self._get_display_width(line)

            # Create Text object for this line
            line_text = Text(line)

            # Copy applicable spans from content_text
            line_start = char_pos
            line_end = char_pos + len(line)

            for span in content_text.spans:
                # Check if span overlaps with this line
                span_start = max(0, span.start - line_start)
                span_end = min(len(line), span.end - line_start)

                if span_start < span_end and span_end > 0:
                    # This span applies to this line
                    line_text.stylize(span.style, span_start, span_end)

            # Add horizontal alignment padding
            if align == "center":
                left_pad = max(0, (width - line_width) // 2)
                text.append(" " * left_pad)
            elif align == "right":
                left_pad = max(0, width - line_width)
                text.append(" " * left_pad)
            # left: no padding

            text.append_text(line_text)
            text.append("\n")

            # Update char position
            char_pos += len(line) + 1

    def _render_vcentered_styled_content(
        self, text: Text, styled_text: Text, align: str, valign: str
    ) -> None:
        """Render styled content with vertical alignment.

        Args:
            text: The Text object to append to
            styled_text: Pre-styled Text object
            align: Horizontal alignment (left, center, right)
            valign: Vertical alignment (top, middle, bottom)
        """
        # Get display dimensions
        width = self._get_effective_display_width()
        height = self.config.display_height or 40
        # Reserve 2 lines for progress bar and page info at bottom
        effective_height = max(1, height - 2)

        # Get the styled text as string
        content_str = str(styled_text)

        # Count lines (including empty lines)
        content_lines = content_str.split("\n")
        content_height = len(content_lines)

        # Calculate vertical padding
        if valign in ("middle", "center"):
            top_padding = max(0, (effective_height - content_height) // 2)
        elif valign == "bottom":
            top_padding = max(0, effective_height - content_height)
        else:  # top (default)
            top_padding = 0

        # Add top padding (empty lines)
        for _ in range(top_padding):
            text.append("\n")

        # Track character position for span mapping
        char_pos = 0

        # Now render each line with horizontal alignment and preserve styles
        for line in content_lines:
            if not line.strip():
                text.append("\n")
                char_pos += len(line) + 1
                continue

            line_width = self._get_display_width(line)

            # Truncate if needed
            if line_width > width:
                line = self._truncate_to_width(line, width)
                line_width = self._get_display_width(line)

            # Create Text object for this line
            line_text_obj = Text(line)

            # Copy applicable spans from styled_text
            line_start = char_pos
            line_end = char_pos + len(line)

            for span in styled_text.spans:
                # Check if span overlaps with this line
                span_start = max(0, span.start - line_start)
                span_end = min(len(line), span.end - line_start)

                if span_start < span_end and span_end > 0:
                    # This span applies to this line
                    line_text_obj.stylize(span.style, span_start, span_end)

            # Add horizontal alignment padding
            if align == "center":
                left_pad = max(0, (width - line_width) // 2)
                text.append(" " * left_pad)
            elif align == "right":
                left_pad = max(0, width - line_width)
                text.append(" " * left_pad)
            # left: no padding

            text.append_text(line_text_obj)
            text.append("\n")

            # Update char position
            char_pos += len(line) + 1

    def _parse_css_style(self, style_str: str) -> str:
        """Parse CSS style string and convert to Rich style."""
        if not style_str:
            return ""

        styles = []
        # Simple CSS property parsing
        declarations = [d.strip() for d in style_str.split(";") if d.strip()]

        for decl in declarations:
            if ":" not in decl:
                continue
            prop, value = decl.split(":", 1)
            prop = prop.strip().lower()
            value = value.strip().lower()

            if prop == "color":
                styles.append(value)
            elif prop == "font-weight" and value in ("bold", "bolder"):
                styles.append("bold")
            elif prop == "font-style" and value == "italic":
                styles.append("italic")
            elif prop == "text-decoration" and "underline" in value:
                styles.append("underline")

        return " ".join(styles) if styles else ""

    def _render_table(self, text: Text, elem: Element) -> None:
        """Render a table."""
        if not elem.rows:
            return

        # Calculate column widths using display width (for CJK support)
        num_cols = max(len(row) for row in elem.rows)
        col_widths = [0] * num_cols

        for row in elem.rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], self._get_display_width(cell))

        # Build border characters
        top_border = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        mid_border = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        bot_border = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"

        # Render top border
        text.append(top_border, style="dim")
        text.append("\n")

        for row_idx, row in enumerate(elem.rows):
            # Render cells with separators
            text.append("│", style="dim")
            for i in range(num_cols):
                cell = row[i] if i < len(row) else ""
                # Pad cell to display width
                padded_cell = " " + self._pad_to_width(cell, col_widths[i]) + " "
                if row_idx == 0:
                    # Header row: bright white text
                    text.append(padded_cell, style="bold bright_white")
                else:
                    text.append(padded_cell)
                if i < num_cols - 1:
                    text.append("│", style="dim")
            text.append("│", style="dim")
            text.append("\n")

            if row_idx == 0:
                text.append(mid_border, style="dim")
                text.append("\n")

        text.append(bot_border, style="dim")
        text.append("\n")  # Add newline after table

    def update_slide(self, slide: Slide, show_notes: bool = False) -> None:
        """Update the displayed slide."""
        self.slide = slide
        self.show_notes = show_notes
        self._update_content(slide)


class ProgressBar(Widget):
    """A progress bar widget for slide navigation."""

    DEFAULT_CSS = """
    ProgressBar {
        height: 1;
        width: 100%;
        dock: bottom;
    }

    #progress-content {
        width: 100%;
    }
    """

    current: reactive[int] = reactive(0)
    total: reactive[int] = reactive(1)

    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        yield Static("", id="progress-content")

    def _on_mount(self) -> None:
        self._update_progress()

    def _on_resize(self) -> None:
        """Handle resize events to update progress bar width."""
        self._update_progress()

    def watch_current(self, old: int, new: int) -> None:
        self._update_progress()

    def watch_total(self, old: int, new: int) -> None:
        self._update_progress()

    def _update_progress(self) -> None:
        """Update the progress bar display."""
        content = self.query_one("#progress-content", Static)
        if self.total <= 0:
            content.update("")
            return

        # Get widget width, fallback to app size
        width = (
            self.size.width
            if self.size.width > 0
            else (
                self.app.size.width
                if hasattr(self, "app") and self.app.size.width > 0
                else 80
            )
        )

        # Calculate progress
        progress = self.current / self.total if self.total > 0 else 0
        done_width = int(width * progress)
        todo_width = width - done_width

        # Build the progress bar - thin line
        text = Text()
        text.append("─" * done_width, style=self.config.theme.progress_done)
        text.append("─" * todo_width, style=self.config.theme.progress_todo)

        content.update(text)

    def update_progress(self, current: int, total: int) -> None:
        """Update progress values."""
        self.current = current
        self.total = total


class HelpOverlay(Widget):
    """Overlay showing keyboard shortcuts."""

    DEFAULT_CSS = """
    HelpOverlay {
        display: none;
        width: 60;
        height: auto;
        padding: 0 1;
        background: $surface;
        border: double white;
    }

    HelpOverlay.visible {
        display: block;
    }

    HelpOverlay #help-title {
        text-align: center;
        width: 100%;
        margin-bottom: 0;
        padding: 1 0;
        border-bottom: double white;
        color: $text;
        text-style: bold;
    }
    """

    visible: reactive[bool] = reactive(False)

    def watch_visible(self, visible: bool) -> None:
        """Handle visibility changes."""
        self.set_class(visible, "visible")

    def compose(self) -> ComposeResult:
        yield Static("Keyboard Shortcuts", id="help-title")
        yield Static(self._get_help_text(), id="help-content")

    def _get_help_text(self) -> str:
        return """
  → / Space    Next slide
  ←            Previous slide
  Home         First slide
  End          Last slide
  g + number   Go to slide N
  /            Search
  o            Overview mode
  n            Toggle speaker notes
  ?            Show this help
  q            Quit
"""

    def toggle(self) -> None:
        """Toggle visibility."""
        self.visible = not self.visible


class SearchOverlay(Widget):
    """Search overlay widget."""

    DEFAULT_CSS = """
    SearchOverlay {
        display: none;
        dock: top;
        height: 3;
        padding: 0 1;
        background: $surface;
    }

    SearchOverlay.visible {
        display: block;
    }
    """

    visible: reactive[bool] = reactive(False)

    def watch_visible(self, visible: bool) -> None:
        """Handle visibility changes."""
        self.set_class(visible, "visible")

    class SearchSubmitted(Message):
        """Sent when a search is submitted."""

        def __init__(self, query: str):
            super().__init__()
            self.query = query

    def compose(self) -> ComposeResult:
        from textual.widgets import Input

        yield Input(placeholder="Search in slides...", id="search-input")

    def toggle(self) -> None:
        """Toggle visibility."""
        self.visible = not self.visible
        if self.visible:
            self.query_one("#search-input", Input).focus()


class OverviewOverlay(Widget):
    """Overview overlay widget showing all slides."""

    DEFAULT_CSS = """
    OverviewOverlay {
        display: none;
        width: 60%;
        height: 60%;
        max-width: 80;
        max-height: 24;
        padding: 0 1;
        background: $surface;
        border: double white;
    }

    OverviewOverlay.visible {
        display: block;
    }

    OverviewOverlay #overview-title {
        text-align: center;
        width: 100%;
        margin-bottom: 0;
        padding: 1 0;
        border-bottom: double white;
        color: $text;
        text-style: bold;
    }

    OverviewOverlay ListView {
        height: 1fr;
        background: $surface;
        margin-top: 0;
    }

    OverviewOverlay ListItem {
        padding: 0 1;
    }
    """

    visible: reactive[bool] = reactive(False)

    def watch_visible(self, visible: bool) -> None:
        """Handle visibility changes."""
        self.set_class(visible, "visible")

    class SlideSelected(Message):
        """Sent when a slide is selected from overview."""

        def __init__(self, index: int):
            super().__init__()
            self.index = index

    def compose(self) -> ComposeResult:
        yield Static("PPT Overview (Enter to select, Esc to close)", id="overview-title")
        yield ListView(id="overview-list")

    def update_slides(self, slides: list[Slide], current_index: int = 0) -> None:
        """Update the list of slides in the overview."""
        list_view = self.query_one("#overview-list", ListView)
        # Clear existing items
        for child in list_view.children:
            child.remove()
        
        for i, slide in enumerate(slides):
            title = slide.title or f"Slide {i+1}"
            list_view.append(ListItem(Static(f"{i+1:2d}. {title}")))
        
        if 0 <= current_index < len(slides):
            list_view.index = current_index

    def toggle(self) -> None:
        """Toggle visibility."""
        self.visible = not self.visible
        if self.visible:
            self.query_one("#overview-list", ListView).focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection of a slide."""
        if event.list_view.index is not None:
            self.post_message(self.SlideSelected(event.list_view.index))
            self.visible = False

    def on_key(self, event) -> None:
        """Handle escape to close."""
        if event.key == "escape":
            self.visible = False
            event.stop()
        elif event.key == "o":
            self.visible = False
            event.stop()
