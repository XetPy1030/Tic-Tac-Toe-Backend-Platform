"""Модели описания меты"""
from enum import Enum, StrEnum

from pydantic import AnyUrl, BaseModel, Field, constr

IdString = constr(
    pattern="^[0-9a-z_]*$",
    strict=True
)

ResultKey = constr(
    pattern="^[a-zA-Z][a-zA-Z0-9_]+",
    strict=True
)

RoleMultiKey = constr(
    pattern="^[a-zA-Z][a-zA-Z0-9_]+",
    strict=True
)


class AlabugaMeta(StrEnum):
    """Версия меты"""

    field_1_4 = "1.4"


class TypeName(StrEnum):
    """Типы"""

    integer = "integer"
    boolean = "boolean"
    string = "string"
    array = "array"


class Format(StrEnum):
    """Формат полей"""

    int32 = "int32"
    int64 = "int64"


class LocalizedStr255(BaseModel):
    """Строка на 255 символов"""

    ru: str = Field(max_length=255)
    en: str | None = Field(default=None, max_length=255)


class LocalizedStr1024(BaseModel):
    """Строка на 1024 символа"""

    ru: str = Field(max_length=1024)
    en: str | None = Field(default=None, max_length=1024)


class LocalizedUrl(BaseModel):
    """Поля-ссылки"""

    ru: AnyUrl | str | None
    en: AnyUrl | str | None = None


class ParamBase(BaseModel):
    """Базовая модель для описания полей"""

    type: TypeName
    required: bool
    title: LocalizedStr255
    desc: LocalizedStr1024 | None = None


class ParamInteger(ParamBase):
    """Числовое поле"""

    type: TypeName = Field(TypeName.integer)
    default: int | None = None
    format: Format | None = None
    min: int | None = None
    max: int | None = None


class ParamBool(ParamBase):
    """Булевое поле"""

    type: TypeName = Field(TypeName.boolean)
    default: bool | None = None


class ParamIntArrayItems(BaseModel):
    """Элементы списка"""

    type: TypeName = Field(TypeName.integer)
    default: int
    format: Format | None = None
    min: int
    max: int
    max_items: int = Field(default=360000, alias="maxItems")

    class Config:
        """Конфигурация"""

        populate_by_name = True


class ParamIntArray(ParamBase):
    """Список"""

    type: TypeName = Field(TypeName.array)
    items: ParamIntArrayItems


class ParamString(ParamBase):
    """Строковое поле"""

    type: TypeName = Field(TypeName.string)
    default: str | None = None


Param = ParamBool | ParamInteger | ParamString | ParamIntArray | ParamBase


class RoleMulti(BaseModel):
    """
    Модель описания роли.
    """

    title: LocalizedStr255
    description: LocalizedStr1024 | None = Field(
        serialization_alias="desc",
        default=None,
    )
    min_players: int = Field(
        serialization_alias="minPlayers",
        description="Минимальное количество игроков на эту роль",
        ge=0,
        le=1000,
    )
    max_players: int = Field(
        serialization_alias="maxPlayers",
        description="Максимальное количество игроков на эту роль",
        ge=0,
        le=1000,
    )


class ResultTypeEnum(StrEnum):
    """
    Типы результата.
    """

    string = "string"
    integer = "integer"
    number = "number"
    boolean = "boolean"


class Result(BaseModel):
    """
    Модель описания результата.
    """

    title: LocalizedStr255 = Field(
        description="Название"
    )
    description: LocalizedStr255 | None = Field(
        serialization_alias="desc",
        description="Описание",
        default=None,
    )
    type: ResultTypeEnum = Field(
        description="Тип"
    )


class ResultModel(BaseModel):
    """
    Модель результата.
    """

    live_num_entities: Result = Field(description="Количество живых сущностей")


class GtSolo(BaseModel):
    """Настройки для solo игры"""

    min_players: int = Field(
        serialization_alias="minPlayers",
        description="Минимальное количество игроков",
        ge=2,
        le=1000,
    )
    max_players: int = Field(
        serialization_alias="maxPlayers",
        description="Максимальное количество игроков",
        ge=2,
        le=1000,
    )
    supported: bool = Field(
        description="Игра поддерживает данный режим"
    )
    params: dict[IdString, Param] | None = None  # type: ignore[valid-type]
    results: ResultModel | dict = Field(description="Результаты игры")
    roles: dict[RoleMultiKey, RoleMulti]  # type: ignore[valid-type]


class GameTypes(BaseModel):
    """Игровые режимы"""

    solo: GtSolo
    # team = 'team'


class Info(BaseModel):
    """Основная информация о симуляции"""

    title: LocalizedStr255 = Field(
        description="Название игры",
    )
    description: LocalizedStr1024 = Field(
        serialization_alias="desc",
        description="Описание игры",
    )
    logo_url: LocalizedUrl = Field(
        serialization_alias="logoUrl",
        description="Ссылка на логотип игры",
    )
    background_color: str | None = Field(
        serialization_alias="backColor",
        description="HEX RGB цвет фона",
        pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
        examples=["#FFFFFF"],
        default=None
    )
    version: str = Field(
        description="Версия игры",
        max_length=255,
    )


class MetaUrls(BaseModel):
    """
    Модель описания URL's меты.
    """

    create_url: LocalizedUrl = Field(
        description="The Game Create Url", serialization_alias="createUrl"
    )
    play_url: LocalizedUrl = Field(
        description="The Game Play Url", serialization_alias="playUrl"
    )
    finish_url: LocalizedUrl = Field(
        description="The Game Finish Url", serialization_alias="finishUrl"
    )


class MetaModel(BaseModel):
    """
    Модель описания меты.
    """

    version: str = Field(
        serialization_alias="alabugaMeta",
        description="Версия мета-данных для платформы",
    )
    info: Info = Field(
        description="Информация о игре",
    )
    game_urls: MetaUrls | None = Field(
        description="URLs: createUrl, playUrl, finishUrl",
        default=None,
    )
    game_types: GameTypes = Field(
        serialization_alias="gameTypes",
        description="Режимы игры",
    )
