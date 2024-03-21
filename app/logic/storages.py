from dataclasses import dataclass
from uuid import UUID

from app.logic.enums import WinStatus


@dataclass
class GameStorage:
    id: UUID
    players: list["PlayerStorage"]
    current_player_id: UUID
    map: list[str | None]
    is_end: bool = False
    is_external_created: bool = False


@dataclass
class PlayerStorage:
    id: UUID
    name: str
    symbol: str
    win_status: WinStatus = WinStatus.UNKNOWN
