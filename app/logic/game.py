import asyncio
import random
from typing import ClassVar
from uuid import UUID, uuid4

from app import hr_platform
from app.logic.enums import WinStatus
from app.logic.player import Player
from app.logic.storages import GameStorage


class Game:
    games: ClassVar[dict[UUID, "Game"]] = {}

    storage: GameStorage
    players: list["Player"]

    def __init__(
        self, storage: GameStorage
    ):
        self.storage = storage
        self.players = [
            Player(player_storage, self.id)
            for player_storage in storage.players
        ]
        self.coros = []

    async def on_end_game(self):
        await asyncio.gather(*[player.on_end_game() for player in self.players])

        if self.storage.is_external_created:
            await hr_platform.add_results(self)

    def attack_point(self, coordinate: int, symbol: str):
        if self.storage.map[coordinate] is not None:
            raise ValueError("Координата занята")

        self.storage.map[coordinate] = symbol

        return {
            "coordinate": coordinate,
            "symbol": symbol,
        }

    async def finish_game(self):
        self.storage.is_end = True
        self.distribute_win_status_by_role(WinStatus.DRAW)
        await self.on_end_game()

    def check_winner(self) -> WinStatus:
        win_status = self.check_map_winner()

        if win_status != WinStatus.UNKNOWN:
            self.storage.is_end = True
            self.distribute_win_status_by_role(win_status)

        return win_status

    def distribute_win_status_by_role(self, win_status: WinStatus):
        if win_status == WinStatus.WIN:
            self.current_player.storage.win_status = WinStatus.WIN
            self.get_next_player().storage.win_status = WinStatus.LOSE
        else:
            for player in self.players:
                player.storage.win_status = WinStatus.DRAW

    def check_map_winner(self):
        map = self.map

        for i in range(3):
            if map[i] == map[i + 3] == map[i + 6] is not None:
                return WinStatus.WIN

            if map[i * 3] == map[i * 3 + 1] == map[i * 3 + 2] is not None:
                return WinStatus.WIN

        if map[0] == map[4] == map[8] is not None:
            return WinStatus.WIN

        if map[2] == map[4] == map[6] is not None:
            return WinStatus.WIN

        if all(map):
            return WinStatus.DRAW

        return WinStatus.UNKNOWN

    def get_next_player(self):
        return self.players[
            (self.players.index(self.current_player) + 1) % 2
        ]

    async def next_player(self):
        next_player = self.get_next_player()

        self.storage.current_player_id = next_player.id
        await self.current_player.on_start_turn()

    def get_player_by_id(self, player_id: UUID) -> "Player":
        for player in self.players:
            if player.id == player_id:
                return player

        raise ValueError("Игрок не найден")

    @property
    def current_player(self):
        return self.get_player_by_id(
            self.storage.current_player_id
        )

    @property
    def id(self):
        return self.storage.id

    @property
    def is_end(self):
        return self.storage.is_end

    @property
    def map(self):
        return self.storage.map

    @classmethod
    def get_game_by_id(cls, game_id: UUID) -> "Game":
        game = cls.games.get(game_id)
        if not game:
            raise ValueError('Игра не найдена')
        return game

    @classmethod
    def create_game(
        cls,
        game_id: UUID | None = None,
        player_ids: list[UUID] | None = None,
        player_names: list[str] | None = None,
        symbols: tuple[str, str] | None = None,
        is_external_created: bool = False,
    ) -> "Game":
        symbols = symbols or ("X", "O")

        game_id = game_id or uuid4()
        player_ids = player_ids or [uuid4() for _ in range(2)]

        players = []
        for num_player in range(2):
            players.append(
                Player.create_player(
                    symbol=symbols[num_player],
                    player_id=player_ids[num_player],
                    game_id=game_id,
                    name=player_names[num_player] if player_names else None,
                )
            )

        current_player: Player = random.choice(players)

        storage = GameStorage(
            id=game_id,
            players=[player.storage for player in players],
            current_player_id=current_player.id,
            map=[None] * 9,
            is_external_created=is_external_created,
        )

        instance = cls(storage=storage)
        cls.games[game_id] = instance
        return instance

    def __repr__(self):
        return repr(self.storage)
