import asyncio
import json
from traceback import print_exc
from typing import ClassVar, TYPE_CHECKING
from uuid import UUID

from channels.consumer import AsyncConsumer
from django.core.serializers.json import DjangoJSONEncoder

from app.auth import validate_token

if TYPE_CHECKING:
    from app.logic.game import Game
    from app.logic.player import Player


class BaseConsumer(AsyncConsumer):
    def __init__(self):
        super().__init__()

        self.is_connected = False
        self.action: str = "root"

    async def receive(self, data: dict):
        self.action = data['action']
        handler = getattr(self, f'handle_{self.action}')
        await handler(data.get('data'))

    async def error_catcher(self, error):
        raise error

    async def dispatch(self, message):
        try:
            await super().dispatch(message)
        except Exception as ex:
            await self.error_catcher(ex)

    async def accept_connection(self):
        await self.send({
            "type": "websocket.accept"
        })

    async def send_message(
        self,
        message: dict | str,
        action: str | None = None,
        is_success: bool = True
    ):
        action = action or self.action
        data = json.dumps({
            "action": action,
            "data": message,
            "is_success": is_success
        }, ensure_ascii=False, cls=DjangoJSONEncoder)

        await self.send({
            "type": "websocket.send",
            "text": data
        })

    async def close_connection(self, event):
        await self.send({
            "type": "websocket.close"
        })

    async def websocket_connect(self, event):
        await self.accept_connection()
        self.is_connected = True

    async def websocket_receive(self, event):
        text_data = event.get("text")
        await self.receive(json.loads(text_data))

    async def websocket_disconnect(self, event):
        self.is_connected = False


class GameConsumer(BaseConsumer):
    connects: ClassVar[dict[tuple[UUID, UUID], "GameConsumer"]] = {}

    def __init__(self):
        super().__init__()
        self.game_id: UUID | None = None
        self.player_id: UUID | None = None
        self.is_registered: bool = False

    async def on_registered(self):

        _, player = self.get_game_and_player()
        await player.on_connect()

    async def handle_auth(self, data: dict):
        if self.is_registered:
            raise ValueError("Вы уже зарегестрированы")

        token = validate_token(data.get('token'))
        self.player_id = token.sub
        await self.attempt_register()

    async def handle_attack(self, data: dict):
        game, player = self.get_game_and_player()
        await player.attack(data)

    async def receive_game_players(
        self, game: "Game", data: dict, action: str | None = None
    ):
        action = action or self.action

        coros = []
        for player in game.players:
            ws = self.connects.get((game.id, player.id))
            if not ws:
                continue

            coros.append(ws.send_message(data, action))

        await asyncio.gather(*coros)

    async def error_catcher(self, error):
        await self.send_message({
            "type": "Ошибка",
            "detail": str(error)
        }, is_success=False)

        print_exc()
        print(f"Произошла ошибка при запросе {self.action}")

    async def attempt_register(self) -> bool:
        if self.is_registered:
            raise ValueError('Вы уже зарегестрированы')

        key = self.get_game_key()
        if all(key):
            self.get_game_and_player(is_auth_required=False)

            if key in self.connects:
                raise ValueError('Вы уже подключены')

            self.connects[key] = self
            self.is_registered = True
            await self.on_registered()
            return True

        return False

    def get_game_and_player(
        self, is_auth_required: bool = True
    ) -> tuple["Game", "Player"]:
        if is_auth_required and not self.is_registered:
            raise ValueError("Не зарегестрирован")

        if not all(self.get_game_key()):
            raise ValueError("Не все данные")

        from app.logic.game import Game

        game = Game.get_game_by_id(self.game_id)
        player = game.get_player_by_id(self.player_id)
        return game, player

    async def websocket_connect(self, event):
        await super().websocket_connect(event)

        kwargs = self.scope.get('url_route', {}).get('kwargs', {})
        self.game_id = kwargs.get('game_id')
        self.player_id = kwargs.get('player_id')
        await self.attempt_register()

    async def websocket_disconnect(self, event):
        await super().websocket_disconnect(event)
        self.connects.pop(self.get_game_key(), None)

    def get_game_key(self):
        return self.game_id, self.player_id
