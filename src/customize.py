"""
customize.py
Holds mutable chart-appearance state (palette, seaborn style, marker,
context) shared across all plots, plus small setter functions the GUI's
customize panel calls into.
"""

VALID_PALETTES = ["viridis", "mako", "flare", "crest", "rocket", "Set2", "coolwarm", "magma"]
VALID_STYLES = ["darkgrid", "whitegrid", "dark", "white", "ticks"]
VALID_CONTEXTS = ["notebook", "talk", "paper", "poster"]
VALID_MARKERS = ["o", "s", "D", "^", "x", "*"]


class ChartStyle:
    """Container for the current seaborn/matplotlib styling preferences."""

    def __init__(self):
        self.palette = "viridis"
        self.style = "darkgrid"
        self.context = "notebook"
        self.marker = "o"

    def as_dict(self) -> dict:
        return {
            "palette": self.palette,
            "style": self.style,
            "context": self.context,
            "marker": self.marker,
        }


def change_palette(style: ChartStyle, palette: str) -> None:
    if palette in VALID_PALETTES:
        style.palette = palette


def change_style(style: ChartStyle, sns_style: str) -> None:
    if sns_style in VALID_STYLES:
        style.style = sns_style


def change_context(style: ChartStyle, context: str) -> None:
    if context in VALID_CONTEXTS:
        style.context = context


def change_marker(style: ChartStyle, marker: str) -> None:
    if marker in VALID_MARKERS:
        style.marker = marker
