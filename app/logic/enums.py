from enum import StrEnum


class WinStatus(StrEnum):
    """WinStatus enumeration."""
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"
    UNKNOWN = "unknown"
