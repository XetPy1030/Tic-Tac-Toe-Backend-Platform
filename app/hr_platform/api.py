import json
from typing import TYPE_CHECKING

import httpx
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from app.logic.enums import WinStatus

if TYPE_CHECKING:
    from app.logic.player import Player
    from app.logic.game import Game

default_headers = {
    "Authorization": f"Bearer {settings.EXTERNAL_API_KEY}",
    "Content-Type": "application/json",
}


def decode_data(data: dict):
    return json.dumps(data, ensure_ascii=False, cls=DjangoJSONEncoder)


async def quit_player(player: "Player"):
    async with httpx.AsyncClient() as httpx_client:
        response = await httpx_client.post(
            f"{settings.EXTERNAL_API_URL}/assessment/{player.game_id}/quit",
            content=decode_data({"uid": player.id}),
            headers=default_headers,
        )
        response.raise_for_status()


async def add_results(game: "Game"):
    async with httpx.AsyncClient() as httpx_client:
        response = await httpx_client.post(
            f"{settings.EXTERNAL_API_URL}/assessment/{game.id}/add",
            content=decode_data(get_results(game)),
            headers=default_headers
        )
        response.raise_for_status()


def get_results(game: "Game"):
    win_status_positions = {
        WinStatus.WIN: 1,
        WinStatus.DRAW: 2,
        WinStatus.LOSE: 2,
        WinStatus.UNKNOWN: 3,
    }
    return {
        "players": [
            {
                "uid": player.id,
                "position": win_status_positions[player.storage.win_status],
                "results": {
                    "win": player.storage.win_status == WinStatus.WIN,
                    "draw": player.storage.win_status == WinStatus.DRAW,
                },
            }
            for player in game.players
        ]
    }
