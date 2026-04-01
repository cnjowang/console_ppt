"""Configuration management for console-ppt."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ThemeColors:
    """Theme color configuration."""
    title: str = "bold cyan"  # H1
    heading_h2: str = "bold dark_orange"  # H2
    heading_h3: str = "bold yellow"  # H3
    heading_h4: str = "bold bright_white"  # H4+
    code: str = "green"
    code_bg: str = "#1e1e1e"
    quote: str = "italic dim"
    list_bullet: str = "cyan"
    progress_done: str = "grey23"
    progress_todo: str = "grey15"


@dataclass
class KeyBindings:
    """Key binding configuration."""
    next_slide: str = "right"
    prev_slide: str = "left"
    next_slide_alt: str = "space"
    first_slide: str = "home"
    last_slide: str = "end"
    goto: str = "g"
    search: str = "slash"
    overview: str = "o"
    notes: str = "n"
    help: str = "question_mark"
    quit: str = "q"


# Default configuration values
DEFAULT_CONFIG = {
    'theme': {
        'title': 'bold cyan',
        'heading_h2': 'bold dark_orange',
        'heading_h3': 'bold yellow',
        'heading_h4': 'bold bright_white',
        'code': 'green',
        'code_bg': '#1e1e1e',
        'quote': 'italic dim',
        'list_bullet': 'cyan',
        'progress_done': 'grey23',
        'progress_todo': 'grey15',
    },
    'show_line_numbers': False,
    'code_highlight': True,
    'enable_animations': True,
    'animation_duration': 0.5,
    'display_width': 120,
    'display_height': 40,
}


@dataclass
class Config:
    """Application configuration."""
    theme: ThemeColors = field(default_factory=ThemeColors)
    keys: KeyBindings = field(default_factory=KeyBindings)
    show_line_numbers: bool = False
    code_highlight: bool = True
    enable_animations: bool = True
    animation_duration: float = 1.0
    # Display area settings
    display_width: Optional[int] = 120
    display_height: Optional[int] = 40

    @classmethod
    def from_file(cls, filepath: str) -> "Config":
        """Load configuration from a YAML file."""
        path = Path(filepath)
        if not path.exists():
            return cls()

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        config = cls()

        # Load theme
        if 'theme' in data:
            theme_data = data['theme']
            config.theme = ThemeColors(
                title=theme_data.get('title', config.theme.title),
                heading_h2=theme_data.get('heading_h2', config.theme.heading_h2),
                heading_h3=theme_data.get('heading_h3', config.theme.heading_h3),
                heading_h4=theme_data.get('heading_h4', config.theme.heading_h4),
                code=theme_data.get('code', config.theme.code),
                code_bg=theme_data.get('code_bg', config.theme.code_bg),
                quote=theme_data.get('quote', config.theme.quote),
                list_bullet=theme_data.get('list_bullet', config.theme.list_bullet),
                progress_done=theme_data.get('progress_done', config.theme.progress_done),
                progress_todo=theme_data.get('progress_todo', config.theme.progress_todo),
            )

        # Load key bindings
        if 'keys' in data:
            keys_data = data['keys']
            config.keys = KeyBindings(
                next_slide=keys_data.get('next_slide', config.keys.next_slide),
                prev_slide=keys_data.get('prev_slide', config.keys.prev_slide),
                next_slide_alt=keys_data.get('next_slide_alt', config.keys.next_slide_alt),
                first_slide=keys_data.get('first_slide', config.keys.first_slide),
                last_slide=keys_data.get('last_slide', config.keys.last_slide),
                goto=keys_data.get('goto', config.keys.goto),
                search=keys_data.get('search', config.keys.search),
                overview=keys_data.get('overview', config.keys.overview),
                notes=keys_data.get('notes', config.keys.notes),
                help=keys_data.get('help', config.keys.help),
                quit=keys_data.get('quit', config.keys.quit),
            )

        # Load other settings
        config.show_line_numbers = data.get('show_line_numbers', config.show_line_numbers)
        config.code_highlight = data.get('code_highlight', config.code_highlight)
        config.enable_animations = data.get('enable_animations', config.enable_animations)
        config.animation_duration = data.get('animation_duration', config.animation_duration)
        config.display_width = data.get('display_width', config.display_width)
        config.display_height = data.get('display_height', config.display_height)

        return config


def get_default_config_path() -> Path:
    """Get the default config path (~/.console_ppt/config.yaml)."""
    return Path.home() / ".console_ppt" / "config.yaml"


def find_config(config_path: Optional[str] = None) -> Optional[str]:
    """Find config file.

    Priority:
    1. If config_path is specified (via -c flag), use it
    2. Otherwise, use ~/.console_ppt/config.yaml if exists
    """
    if config_path:
        return config_path

    default_path = get_default_config_path()
    if default_path.exists():
        return str(default_path)

    return None
