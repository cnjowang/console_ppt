"""Main application for console-ppt."""

import sys
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Static

from .config import Config, find_config
from .parser import Presentation, parse_file
from .widgets import (
    HelpOverlay,
    OverviewOverlay,
    ProgressBar,
    SearchOverlay,
    SlideWidget,
)


class ConsolePPT(App):
    """A terminal-based PPT presentation tool."""

    CSS = """
    Screen {
        background: $surface;
        align: center middle;
        layers: base overlay;
    }

    #presentation-frame {
        background: $surface;
        layer: base;
    }

    #main-container {
        height: 100%;
    }

    #slide-container {
        height: 1fr;
        layout: vertical;
    }

    #speaker-notes {
        height: auto;
        max-height: 20%;
        background: $surface;
        color: $text-disabled;
        padding: 1 2;
        display: none;
    }

    #progress-bar {
        height: 1;
        dock: bottom;
        display: block;
    }

    #page-info {
        height: 1;
        dock: bottom;
        background: $surface-darken-1;
        padding: 0 1;
        text-align: right;
        display: block;
    }

    HelpOverlay, SearchOverlay, OverviewOverlay {
        layer: overlay;
    }
    """

    BINDINGS = [
        Binding("right,space", "next_slide", "Next", show=False),
        Binding("left", "prev_slide", "Prev", show=False),
        Binding("home", "first_slide", "First", show=False),
        Binding("end", "last_slide", "Last", show=False),
        Binding("g", "goto_mode", "Go to", show=False),
        Binding("slash", "search", "Search", show=False),
        Binding("o", "overview", "Overview", show=False),
        Binding("n", "toggle_notes", "Notes", show=False),
        Binding("question_mark", "toggle_help", "Help", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    current_slide: int = 0
    show_notes: bool = False
    goto_mode: bool = False
    goto_buffer: str = ""

    def __init__(self, presentation: Presentation, config: Config | None = None):
        super().__init__()
        self.presentation = presentation
        self.config = config or Config()
        # Calculate non-title slides for progress tracking
        self.content_slides = [
            i for i, s in enumerate(presentation.slides) if not s.is_title_slide()
        ]
        self.content_slide_count = len(self.content_slides)

    def compose(self) -> ComposeResult:
        # Determine display dimensions
        display_width = self.config.display_width
        display_height = self.config.display_height

        # Build dynamic CSS for presentation frame
        frame_styles = []
        if display_width:
            frame_styles.append(f"width: {display_width};")
        if display_height:
            frame_styles.append(f"height: {display_height};")

        if frame_styles:
            self.stylesheet.add_source(f"""
            #presentation-frame {{
                {" ".join(frame_styles)}
            }}
            """)

        with Container(id="presentation-frame"):
            with Container(id="main-container"):
                with Container(id="slide-container"):
                    yield SlideWidget(self.config, id="slide-widget")
                    yield Static("", id="speaker-notes")
                yield Static("", id="page-info")
                yield ProgressBar(self.config, id="progress-bar")
        yield HelpOverlay(id="help-overlay")
        yield SearchOverlay(id="search-overlay")
        yield OverviewOverlay(id="overview-overlay")

    def _on_mount(self) -> None:
        """Initialize the display."""
        self._update_display()

    def _update_display(self, animate: bool = False) -> None:
        """Update the current slide display."""
        if not self.presentation.slides:
            return

        slide = self.presentation.slides[self.current_slide]
        is_title = slide.is_title_slide()

        # Update slide widget
        slide_widget = self.query_one("#slide-widget", SlideWidget)
        if animate and self.config.enable_animations:
            slide_widget.animate_to_slide(slide, self.show_notes)
        else:
            slide_widget.update_slide(slide, self.show_notes)

        # Update speaker notes
        notes_widget = self.query_one("#speaker-notes", Static)
        if self.show_notes and slide.notes:
            notes_widget.update(f"📝 {slide.notes}")
            notes_widget.styles.display = "block"
        else:
            notes_widget.styles.display = "none"

        # Update progress bar and page info (hidden for title slides or when hide_progress is set)
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        page_info = self.query_one("#page-info", Static)

        # Check if progress bar should be hidden (global setting, title slide or hide_progress directive)
        hide_progress = not self.presentation.show_progress or is_title or slide.hide_progress

        if hide_progress:
            # Hide progress bar and page info
            progress_bar.styles.display = "none"
            page_info.styles.display = "none"
        else:
            progress_bar.styles.display = "block"
            page_info.styles.display = "block"
            # Calculate current position in content slides
            content_index = (
                self.content_slides.index(self.current_slide)
                if self.current_slide in self.content_slides
                else 0
            )
            progress_bar.update_progress(content_index + 1, self.content_slide_count)
            page_info.update(f"{content_index + 1}/{self.content_slide_count} ")

    def action_next_slide(self) -> None:
        """Go to the next slide."""
        if self.current_slide < len(self.presentation) - 1:
            self.current_slide += 1
            self._update_display(animate=True)

    def action_prev_slide(self) -> None:
        """Go to the previous slide."""
        if self.current_slide > 0:
            self.current_slide -= 1
            self._update_display(animate=True)

    def action_first_slide(self) -> None:
        """Go to the first slide."""
        self.current_slide = 0
        self._update_display(animate=True)

    def action_last_slide(self) -> None:
        """Go to the last slide."""
        self.current_slide = len(self.presentation) - 1
        self._update_display(animate=True)

    def action_goto_mode(self) -> None:
        """Enter goto mode."""
        self.goto_mode = True
        self.goto_buffer = ""
        self.notify("Enter slide number...", title="Go to slide")

    def action_search(self) -> None:
        """Toggle search overlay."""
        search = self.query_one("#search-overlay", SearchOverlay)
        search.toggle()

    def action_overview(self) -> None:
        """Show overview of all slides."""
        overview = self.query_one("#overview-overlay", OverviewOverlay)
        overview.update_slides(self.presentation.slides, self.current_slide)
        overview.toggle()

    @on(OverviewOverlay.SlideSelected)
    def on_overview_overlay_slide_selected(self, message: OverviewOverlay.SlideSelected) -> None:
        """Handle slide selection from overview."""
        self.current_slide = message.index
        self._update_display(animate=True)

    def action_toggle_notes(self) -> None:
        """Toggle speaker notes display."""
        self.show_notes = not self.show_notes
        self._update_display()
        status = "on" if self.show_notes else "off"
        self.notify(f"Speaker notes: {status}", title="Notes")

    def action_toggle_help(self) -> None:
        """Toggle help overlay."""
        help_overlay = self.query_one("#help-overlay", HelpOverlay)
        help_overlay.toggle()

    def _on_key(self, event) -> None:
        """Handle key events."""
        if self.goto_mode:
            if event.key.isdigit():
                self.goto_buffer += event.key
            elif event.key == "enter":
                try:
                    slide_num = int(self.goto_buffer)
                    if 1 <= slide_num <= len(self.presentation):
                        self.current_slide = slide_num - 1
                        self._update_display(animate=True)
                    else:
                        self.notify(
                            f"Invalid slide number (1-{len(self.presentation)})"
                        )
                except ValueError:
                    pass
                self.goto_mode = False
                self.goto_buffer = ""
            elif event.key == "escape":
                self.goto_mode = False
                self.goto_buffer = ""
            event.stop()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="console-ppt", description="Terminal-based PPT presentation from Markdown"
    )
    parser.add_argument("file", type=str, help="Markdown file to present")
    parser.add_argument("-c", "--config", type=str, help="Path to config file")

    args = parser.parse_args()

    # Check file exists
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Load config
    config_path = find_config(args.config)
    if config_path:
        config = Config.from_file(config_path)
    else:
        config = Config()

    # Parse presentation
    try:
        presentation = parse_file(str(filepath))
    except Exception as e:
        print(f"Error parsing file: {e}", file=sys.stderr)
        sys.exit(1)

    if not presentation.slides:
        print("Error: No slides found in file", file=sys.stderr)
        sys.exit(1)

    # Run app
    app = ConsolePPT(presentation, config)
    app.run()


if __name__ == "__main__":
    main()
