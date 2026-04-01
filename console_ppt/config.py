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
    bg: str = "#1e1e1e"
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
    help: str = "h"
    quit: str = "q"


@dataclass
class Config:
    """Application configuration."""
    theme: ThemeColors = field(default_factory=ThemeColors)
    keys: KeyBindings = field(default_factory=KeyBindings)
    show_line_numbers: bool = False
    show_progress: bool = True
    code_highlight: bool = True
    enable_animations: bool = True
    animation_duration: float = 0.5
    transition_type: str = "fall"  # "fall" or "glitch"
    # Display area settings
    display_width: Optional[int] = 120
    display_height: Optional[int] = 40

    @classmethod
    def from_file(cls, filepath: str) -> "Config":
        """Load configuration from a YAML file."""
        path = Path(filepath)
        if not path.exists():
            print(f"DEBUG: Config file not found at {filepath}")
            return cls()

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"DEBUG: Error reading config file: {e}")
            return cls()

        config = cls()

        # Load theme
        if 'theme' in data:
            theme_data = data['theme']
            for field_name in config.theme.__dataclass_fields__:
                if field_name in theme_data:
                    setattr(config.theme, field_name, theme_data[field_name])

        # Load key bindings
        if 'keys' in data:
            keys_data = data['keys']
            for field_name in config.keys.__dataclass_fields__:
                if field_name in keys_data:
                    setattr(config.keys, field_name, keys_data[field_name])

        # Load other settings
        for field_name in config.__dataclass_fields__:
            if field_name in data and field_name not in ('theme', 'keys'):
                setattr(config, field_name, data[field_name])

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
