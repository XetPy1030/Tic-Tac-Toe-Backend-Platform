from app.hr_platform.meta_model import *

meta_dict = MetaModel(
    version=AlabugaMeta.field_1_4,
    info=Info(
        title=LocalizedStr255(
            ru="Крестики-Нолики",
            en="Tic-Tac-Toe"
        ),
        description=LocalizedStr1024(
            ru="Игра в крестики-нолики",
            en="Tic-tac-toe game"
        ),
        logo_url=LocalizedUrl(
            ru="https://all-t-shirts.ru/goods_images/1720/1883/ru111798/ru111798II00065bdbeb3ad858e74b0c3cb4474261599.jpg",
            en="https://all-t-shirts.ru/goods_images/1720/1883/ru111798/ru111798II00065bdbeb3ad858e74b0c3cb4474261599.jpg"
        ),
        background_color="#63df9c",
        version="1.0.0",
    ),
    game_types=GameTypes(
        solo=GtSolo(
            params={
                IdString("symbol_player_1"): ParamString(
                    required=True,
                    title=LocalizedStr255(
                        ru="Символ игрока 1",
                        en="Player 1 symbol"
                    ),
                    desc=LocalizedStr1024(
                        ru="Символ, которым играет игрок 1",
                        en="Symbol that player 1 plays with"
                    ),
                    default="X"
                ),
                IdString("symbol_player_2"): ParamString(
                    required=True,
                    title=LocalizedStr255(
                        ru="Символ игрока 2",
                        en="Player 2 symbol"
                    ),
                    desc=LocalizedStr1024(
                        ru="Символ, которым играет игрок 2",
                        en="Symbol that player 2 plays with"
                    ),
                    default="O"
                ),
            },
            min_players=2,
            max_players=2,
            supported=True,
            results={
                "win": Result(
                    title=LocalizedStr255(
                        ru="Победа",
                        en="Win"
                    ),
                    type=ResultTypeEnum.boolean
                ),
                "draw": Result(
                    title=LocalizedStr255(
                        ru="Ничья",
                        en="Draw"
                    ),
                    type=ResultTypeEnum.boolean
                ),
            },
            roles={
                RoleMultiKey("player_1"): RoleMulti(
                    title=LocalizedStr255(
                        ru="Игрок 1",
                        en="Player 1"
                    ),
                    description=LocalizedStr1024(
                        ru="Игрок 1",
                        en="Player 1"
                    ),
                    min_players=1,
                    max_players=1,
                ),
                RoleMultiKey("player_2"): RoleMulti(
                    title=LocalizedStr255(
                        ru="Игрок 2",
                        en="Player 2"
                    ),
                    description=LocalizedStr1024(
                        ru="Игрок 2",
                        en="Player 2"
                    ),
                    min_players=1,
                    max_players=1,
                ),
            },
        )
    )
).model_dump(by_alias=True, exclude_none=True)
