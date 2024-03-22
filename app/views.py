import asyncio
from uuid import UUID

from rest_framework.response import Response
from rest_framework.views import APIView

from app.auth import ExternalApiAuthentication
from app.hr_platform import meta_dict
from app.logic.game import Game


class CreateView(APIView):
    def post(self, request):
        game = Game.create_game()
        return Response({
            "game_id": game.id,
            "players": [
                {"player_id": player.id, "symbol": player.symbol}
                for player in game.players
            ]
        })


class ExternalMetaView(APIView):
    def get(self, request):
        return Response(meta_dict)


class ExternalCreateView(APIView):
    authentication_classes = [ExternalApiAuthentication]

    def post(self, request):
        data = request.data
        game_id = UUID(data["assessment_id"])

        player_ids = []
        player_names = []
        players = data["players"]
        for player in players:
            player_ids.append(UUID(player["uid"]))
            player_names.append(player["name"])

        params = data["params"]
        symbols = (params["symbol_player_1"], params["symbol_player_2"])
        if players[0]["role"] == "player_2":
            symbols = symbols[::-1]

        Game.create_game(
            game_id=game_id,
            player_ids=player_ids,
            player_names=player_names,
            symbols=symbols,
            is_external_created=True
        )

        return Response()


class ExternalFinishView(APIView):
    authentication_classes = [ExternalApiAuthentication]

    def post(self, request, game_id):
        game = Game.get_game_by_id(UUID(game_id))
        asyncio.create_task(game.finish_game())
        return Response()
