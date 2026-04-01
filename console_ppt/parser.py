"""Markdown parser for console-ppt."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ElementType(Enum):
    """Types of markdown elements."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    LIST = "list"
    ORDERED_LIST = "ordered_list"
    BLOCKQUOTE = "blockquote"
    HR = "hr"
    IMAGE = "image"
    NOTES = "notes"  # Speaker notes
    TABLE = "table"
    BLANK_LINE = "blank_line"  # Empty line
    TITLE = "title"  # Slide main title
    SUBTITLE = "subtitle"  # Slide subtitle
    CENTERED_PARAGRAPH = "centered_paragraph"  # <p align="center">...</p>
    HTML_ELEMENT = "html_element"  # Generic HTML element


@dataclass
class Element:
    """A markdown element."""

    type: ElementType
    content: str
    level: int = 0  # For headings (1-6)
    language: str = ""  # For code blocks
    items: list[str] = field(default_factory=list)  # For lists
    rows: list[list[str]] = field(default_factory=list)  # For tables
    list_items: list[tuple[int, str]] = field(
        default_factory=list
    )  # For nested lists: (indent_level, text)
    # HTML support
    html_tag: str = ""  # HTML tag name (e.g., div, span, a)
    html_attrs: dict = field(
        default_factory=dict
    )  # HTML attributes (e.g., align, href, style)


@dataclass
class Slide:
    """A single slide."""

    elements: list[Element] = field(default_factory=list)
    notes: Optional[str] = None  # Speaker notes
    hide_progress: bool = False  # Whether to hide progress bar for this slide

    @property
    def title(self) -> Optional[str]:
        """Get the title of the slide."""
        # 1. Check for <title> element
        for elem in self.elements:
            if elem.type == ElementType.TITLE:
                return elem.content
        
        # 2. Check for <subtitle> element
        for elem in self.elements:
            if elem.type == ElementType.SUBTITLE:
                return elem.content

        # 3. Check for headings (H1-H6)
        for elem in self.elements:
            if elem.type == ElementType.HEADING:
                return elem.content

        # 4. Fallback: get first non-empty line from other elements
        for elem in self.elements:
            content = ""
            if elem.type in (ElementType.PARAGRAPH, ElementType.CENTERED_PARAGRAPH, ElementType.BLOCKQUOTE):
                content = elem.content
            elif elem.type in (ElementType.LIST, ElementType.ORDERED_LIST) and elem.list_items:
                content = elem.list_items[0][1]
            elif elem.type == ElementType.HTML_ELEMENT and elem.content:
                content = elem.content
            
            if content.strip():
                # Take only the first non-empty line
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                if lines:
                    first_line = lines[0]
                    # Clean up content (remove markdown/html tags for overview)
                    clean_text = re.sub(r"<[^>]+>", "", first_line)
                    clean_text = re.sub(r"[*_`#]", "", clean_text)
                    return clean_text

        return None

    def is_title_slide(self) -> bool:
        """Check if this is a title slide (contains title element)."""
        return any(elem.type == ElementType.TITLE for elem in self.elements)


@dataclass
class Presentation:
    """A presentation containing multiple slides."""

    slides: list[Slide] = field(default_factory=list)
    title: str = ""
    show_progress: bool = True

    def __len__(self) -> int:
        return len(self.slides)

    def __getitem__(self, index: int) -> Slide:
        return self.slides[index]


class MarkdownParser:
    """Parse markdown into presentation slides."""

    def __init__(self, content: str):
        self.content = content
        self.pos = 0

    def parse(self) -> Presentation:
        """Parse the markdown content into a Presentation."""
        # Check for global directives before splitting
        show_progress = True
        show_progress_match = re.search(
            r"^<!--\s*showprogress:\s*(false|true)\s*-->$", 
            self.content, 
            re.MULTILINE | re.IGNORECASE
        )
        if show_progress_match:
            show_progress = show_progress_match.group(1).lower() == "true"

        # Split by --- for slides
        raw_slides = re.split(r"^---\s*$", self.content, flags=re.MULTILINE)

        presentation = Presentation()
        presentation.show_progress = show_progress

        for raw_slide in raw_slides:
            raw_slide = raw_slide.strip()
            if not raw_slide:
                continue

            slide = self._parse_slide(raw_slide)
            if slide.elements:  # Only add non-empty slides
                presentation.slides.append(slide)

        return presentation

    def _parse_slide(self, content: str) -> Slide:
        """Parse a single slide's content."""
        slide = Slide()
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Empty lines - preserve them as blank_line elements
            if not line.strip():
                slide.elements.append(Element(type=ElementType.BLANK_LINE, content=""))
                i += 1
                continue

            # Hide progress bar directive: <!-- hideprogress -->
            hideprogress_match = re.match(
                r"^<!--\s*hideprogress\s*-->$", line.strip(), re.IGNORECASE
            )
            if hideprogress_match:
                slide.hide_progress = True
                i += 1
                continue

            # Global progress directive: <!-- showprogress: ... -->
            # Skip this line as it's handled globally in parse()
            if re.match(r"^<!--\s*showprogress:\s*(false|true)\s*-->$", line.strip(), re.IGNORECASE):
                i += 1
                continue

            # Speaker notes: <!-- notes: ... -->
            notes_match = re.match(r"^<!--\s*notes:\s*(.+?)\s*-->$", line.strip())
            if notes_match:
                slide.notes = notes_match.group(1)
                i += 1
                continue

            # Title: <title>...</title>
            title_match = re.match(r"^<title>\s*(.+?)\s*</title>$", line.strip())
            if title_match:
                slide.elements.append(
                    Element(type=ElementType.TITLE, content=title_match.group(1))
                )
                i += 1
                continue

            # Subtitle: <subtitle>...</subtitle>
            subtitle_match = re.match(
                r"^<subtitle>\s*(.+?)\s*</subtitle>$", line.strip()
            )
            if subtitle_match:
                slide.elements.append(
                    Element(type=ElementType.SUBTITLE, content=subtitle_match.group(1))
                )
                i += 1
                continue

            # Centered paragraph: <p align="center">...</p>
            centered_match = re.match(
                r'^<p\s+align=["\']center["\']>\s*(.+?)\s*</p>$',
                line.strip(),
                re.IGNORECASE,
            )
            if centered_match:
                slide.elements.append(
                    Element(
                        type=ElementType.CENTERED_PARAGRAPH,
                        content=centered_match.group(1),
                    )
                )
                i += 1
                continue

            # Generic HTML elements: <tag attrs>content</tag>
            # Check if line starts with an HTML opening tag
            html_start_match = re.match(
                r"^<(\w+)(\s+[^>]*)?>\s*(.*)$",
                line.strip(),
                re.IGNORECASE,
            )
            if html_start_match:
                tag = html_start_match.group(1).lower()
                attrs_str = html_start_match.group(2) or ""
                remaining_content = html_start_match.group(3)

                # Check if it's a supported HTML tag (including animate and h1-h6)
                if tag in SUPPORTED_HTML_TAGS:
                    # Look for closing tag </tag> within the same line or subsequent lines
                    closing_pattern = re.compile(rf"</{tag}>\s*$", re.IGNORECASE)

                    # Check if closing tag is on the same line
                    same_line_match = closing_pattern.search(remaining_content)
                    if same_line_match:
                        # Closing tag is on the same line
                        content_text = remaining_content[
                            : same_line_match.start()
                        ].strip()
                        attrs = parse_html_attrs(attrs_str)

                        # Special handling for <p> with align attribute (backward compatible)
                        if tag == "p" and attrs.get("align"):
                            align = attrs.get("align", "left").lower()
                            if align == "center":
                                slide.elements.append(
                                    Element(
                                        type=ElementType.CENTERED_PARAGRAPH,
                                        content=content_text,
                                    )
                                )
                            else:
                                # Other align values: left, right, justify
                                slide.elements.append(
                                    Element(
                                        type=ElementType.HTML_ELEMENT,
                                        content=content_text,
                                        html_tag=tag,
                                        html_attrs=attrs,
                                    )
                                )
                        else:
                            slide.elements.append(
                                Element(
                                    type=ElementType.HTML_ELEMENT,
                                    content=content_text,
                                    html_tag=tag,
                                    html_attrs=parse_html_attrs(attrs_str),
                                )
                            )
                        i += 1
                        continue

                    # Multi-line case: look for closing tag on subsequent lines
                    content_lines = [remaining_content]
                    j = i + 1
                    found_closing = False
                    full_line_closing_pattern = re.compile(
                        rf"^\s*</{tag}>\s*$", re.IGNORECASE
                    )

                    while j < len(lines):
                        current_line = lines[j]
                        if full_line_closing_pattern.match(current_line.strip()):
                            found_closing = True
                            break
                        content_lines.append(current_line)
                        j += 1

                    if found_closing:
                        # We found the complete HTML block
                        content_text = "\n".join(content_lines).strip()
                        attrs = parse_html_attrs(attrs_str)

                        # Special handling for <p> with align attribute (backward compatible)
                        if tag == "p" and attrs.get("align"):
                            align = attrs.get("align", "left").lower()
                            if align == "center":
                                slide.elements.append(
                                    Element(
                                        type=ElementType.CENTERED_PARAGRAPH,
                                        content=content_text,
                                    )
                                )
                            else:
                                # Other align values: left, right, justify
                                slide.elements.append(
                                    Element(
                                        type=ElementType.HTML_ELEMENT,
                                        content=content_text,
                                        html_tag=tag,
                                        html_attrs=attrs,
                                    )
                                )
                        else:
                            slide.elements.append(
                                Element(
                                    type=ElementType.HTML_ELEMENT,
                                    content=content_text,
                                    html_tag=tag,
                                    html_attrs=attrs,
                                )
                            )
                        i = j + 1  # Skip to after the closing tag
                        continue
                    # If no closing tag found, fall through to treat as regular content

            # Self-closing HTML tags: <br>, <br/>, etc.
            self_closing_match = re.match(
                r"^<(\w+)(\s+[^>]*)?\s*/?>$", line.strip(), re.IGNORECASE
            )
            if self_closing_match:
                tag = self_closing_match.group(1).lower()
                attrs_str = self_closing_match.group(2) or ""

                if tag in SUPPORTED_HTML_TAGS:
                    attrs = parse_html_attrs(attrs_str)
                    slide.elements.append(
                        Element(
                            type=ElementType.HTML_ELEMENT,
                            content="",
                            html_tag=tag,
                            html_attrs=attrs,
                        )
                    )
                    i += 1
                    continue

            # Heading
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                content_text = heading_match.group(2)
                slide.elements.append(
                    Element(type=ElementType.HEADING, content=content_text, level=level)
                )
                i += 1
                continue

            # Code block
            if line.startswith("```"):
                language = line[3:].strip()
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                i += 1  # Skip closing ```
                slide.elements.append(
                    Element(
                        type=ElementType.CODE_BLOCK,
                        content="\n".join(code_lines),
                        language=language,
                    )
                )
                continue

            # List (unordered)
            if re.match(r"^(\s*)[-*+]\s+", line):
                list_items = []
                while i < len(lines):
                    list_match = re.match(r"^(\s*)([-*+])\s+(.+)$", lines[i])
                    if not list_match:
                        # Check if it's an empty line or starts a new element
                        if not lines[i].strip() or re.match(r"^[^-\s]", lines[i]):
                            break
                        # Skip empty lines within list
                        i += 1
                        continue
                    indent = len(list_match.group(1))
                    # Convert indent spaces to level (2 spaces = 1 level)
                    level = indent // 2
                    text_content = list_match.group(3)
                    list_items.append((level, text_content))
                    i += 1
                slide.elements.append(
                    Element(
                        type=ElementType.LIST,
                        content="",
                        items=[],  # Keep for backward compatibility
                        list_items=list_items,
                    )
                )
                continue

            # List (ordered)
            if re.match(r"^(\s*)\d+\.\s+", line):
                list_items = []
                while i < len(lines):
                    list_match = re.match(r"^(\s*)(\d+)\.\s+(.+)$", lines[i])
                    if not list_match:
                        if not lines[i].strip() or re.match(r"^[^\d\s]", lines[i]):
                            break
                        i += 1
                        continue
                    indent = len(list_match.group(1))
                    level = indent // 2
                    text_content = list_match.group(3)
                    list_items.append((level, text_content))
                    i += 1
                slide.elements.append(
                    Element(
                        type=ElementType.ORDERED_LIST,
                        content="",
                        items=[],
                        list_items=list_items,
                    )
                )
                continue

            # Blockquote
            if line.startswith(">"):
                quote_lines = []
                while i < len(lines) and lines[i].startswith(">"):
                    quote_lines.append(lines[i][1:].strip())
                    i += 1
                slide.elements.append(
                    Element(type=ElementType.BLOCKQUOTE, content="\n".join(quote_lines))
                )
                continue

            # Image
            img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", line.strip())
            if img_match:
                slide.elements.append(
                    Element(
                        type=ElementType.IMAGE,
                        content=img_match.group(2),
                        items=[img_match.group(1)],  # alt text
                    )
                )
                i += 1
                continue

            # Horizontal rule
            if re.match(r"^[-*_]{3,}$", line.strip()):
                slide.elements.append(Element(type=ElementType.HR, content=""))
                i += 1
                continue

            # Table (starts with | character)
            if line.startswith("|"):
                table_lines = []
                while i < len(lines) and lines[i].startswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                slide.elements.append(self._parse_table(table_lines))
                continue

            # Paragraph (collect consecutive non-empty lines)
            para_lines = []
            while i < len(lines) and lines[i].strip():
                # Check if next line starts a new element
                next_line = lines[i]
                if (
                    re.match(r"^#{1,6}\s+", next_line)
                    or next_line.startswith("```")
                    or re.match(r"^[-*+]\s+", next_line)
                    or re.match(r"^\d+\.\s+", next_line)
                    or next_line.startswith(">")
                    or re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", next_line.strip())
                    or re.match(r"^[-*_]{3,}$", next_line.strip())
                ):
                    break
                para_lines.append(next_line)
                i += 1

            if para_lines:
                slide.elements.append(
                    Element(type=ElementType.PARAGRAPH, content="\n".join(para_lines))
                )

        return slide

    def _parse_table(self, lines: list[str]) -> Element:
        """Parse markdown table into Element."""
        if not lines:
            return Element(type=ElementType.TABLE, content="")

        rows = []
        for line in lines:
            # Skip separator lines: only contains |, -, :, and spaces
            # e.g., |---|---| or |:---:|:---| etc.
            stripped = line.replace("|", "").strip()
            if stripped and all(c in "-: " for c in stripped):
                continue
            # Parse cells: | cell1 | cell2 | cell3 |
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if cells:
                rows.append(cells)

        return Element(type=ElementType.TABLE, content="", rows=rows)


def parse_html_attrs(attr_string: str) -> dict:
    """Parse HTML attribute string into a dictionary.

    Examples:
        'align="center"' -> {'align': 'center'}
        'href="https://example.com" target="_blank"' -> {'href': 'https://example.com', 'target': '_blank'}
    """
    attrs = {}
    # Match attr="value" or attr='value' or attr (boolean attributes)
    pattern = r'(\w+)(?:\s*=\s*["\']([^"\']*)["\'])?'
    for match in re.finditer(pattern, attr_string):
        attr_name = match.group(1)
        attr_value = match.group(2) if match.group(2) is not None else True
        attrs[attr_name] = attr_value
    return attrs


# Supported HTML tags for rendering
SUPPORTED_HTML_TAGS = {
    "div",
    "span",
    "a",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "code",
    "ul",
    "ol",
    "li",
    "blockquote",
    "p",
    "animate",
    "h1", "h2", "h3", "h4", "h5", "h6",
}


def parse_file(filepath: str) -> Presentation:
    """Parse a markdown file into a Presentation."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    parser = MarkdownParser(content)
    return parser.parse()
