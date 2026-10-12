"""
ANSI terminal styling and color utilities with fallback detection.

Design Rationale:
- Enhances CLI readability through subtle, consistent color cues.
- Automatically detects terminal capabilities, disabling ANSI escape codes if:
  1. Output is piped to a file or non-interactive stream.
  2. The standard 'NO_COLOR' environment variable is present.
"""

import os
import sys


def _should_enable_color() -> bool:
    """Determine whether ANSI color output should be enabled."""
    if "NO_COLOR" in os.environ:
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    # Windows terminal support setup
    if sys.platform == "win32":
        try:
            # Enable VT100 sequences on Windows 10/11
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
                return True
        except Exception:
            return False

    return True


COLOR_ENABLED = _should_enable_color()


class Style:
    """ANSI escape sequences."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


def paint(text: str, color: str = "", bold: bool = False, dim: bool = False) -> str:
    """
    Apply ANSI styles to text if colors are enabled, otherwise return text unmodified.
    """
    if not COLOR_ENABLED:
        return text

    prefix = ""
    if bold:
        prefix += Style.BOLD
    if dim:
        prefix += Style.DIM
    if color:
        prefix += color

    if not prefix:
        return text

    return f"{prefix}{text}{Style.RESET}"


def success(text: str) -> str:
    return paint(text, Style.BRIGHT_GREEN, bold=True)


def error(text: str) -> str:
    return paint(text, Style.BRIGHT_RED, bold=True)


def warning(text: str) -> str:
    return paint(text, Style.BRIGHT_YELLOW, bold=True)


def info(text: str) -> str:
    return paint(text, Style.BRIGHT_CYAN)


def dim(text: str) -> str:
    return paint(text, dim=True)


def bold(text: str) -> str:
    return paint(text, bold=True)
