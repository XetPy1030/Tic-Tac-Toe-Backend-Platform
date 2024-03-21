from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.consumers import GameConsumer
from app.logic.enums import WinStatus
from app.logic.storages import PlayerStorage

if TYPE_CHECKING:
    from app.logic.game import Game


class Player:
    def __init__(self, storage: PlayerStorage, game_id: UUID):
        self.storage = storage
        self.game_id = game_id

    async def on_connect(self):
        await self.send_message(
            {
                "player": {
                    "id": self.id,
                    "name": self.name,
                    "symbol": self.symbol,
                    "is_turn": self.game.current_player == self,
                    "win_status": self.storage.win_status,
                },
                "map": self.game.map,
            }, "syncronize"
        )

    async def on_start_turn(self):
        await self.send_message(
            {
                "is_turn": self.is_turn
            }, "start_turn"
        )

    async def on_end_game(self):
        await self.send_message(
            {
                "win_status": self.storage.win_status,
            }, "end_game"
        )

    async def attack(self, data: dict):
        self.check_game()

        attack = self.game.attack_point(
            data['coordinate'],
            self.symbol
        )
        await self.receive_message(attack)

        if self.game.check_winner() != WinStatus.UNKNOWN:
            await self.game.on_end_game()
            return

        await self.game.next_player()

    def check_game(self):
        if self.game.is_end:
            raise ValueError("Игра завершена!")

        if self.game.current_player != self:
            raise ValueError("Ходит другой игрок!")

    async def send_message(self, message: dict, action: str | None = None):
        consumer = self.consumer
        if not consumer:
            return
        await consumer.send_message(message, action)

    async def receive_message(self, message: dict, action: str | None = None):
        consumer = self.consumer
        if not consumer:
            return
        await consumer.receive_game_players(self.game, message, action)

    @property
    def consumer(self):
        return GameConsumer.connects.get((self.game.id, self.id))

    @property
    def is_turn(self) -> bool:
        return self.game.current_player == self

    @property
    def symbol(self) -> str:
        return self.storage.symbol

    @property
    def id(self):
        return self.storage.id

    @property
    def name(self):
        return self.storage.name

    @property
    def game(self) -> "Game":
        from app.logic.game import Game
        return Game.games[self.game_id]

    @classmethod
    def create_player(
        cls,
        symbol: str,
        game_id: UUID,
        player_id: UUID | None = None,
        name: str | None = None,
    ) -> "Player":
        player_id = player_id or uuid4()
        name = name or f"Player {symbol}"
        storage = PlayerStorage(
            id=player_id,
            name=name,
            symbol=symbol,
        )
        return cls(storage=storage, game_id=game_id)

    def __repr__(self):
        return repr(self.storage)
