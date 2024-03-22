from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class JWTHeader(BaseModel):
    """Часть JWT, которую надо парсить перед проверкой подписи.

    Security note: это не значит, что она не защищена подписью. Подделка этого
        блока всё равно в итоге сделает весь токен невалидным.
    """

    kid: str


class JWTPermissions(StrEnum):
    """Разрешения, которые могут быть выданы входящему клиенту."""

    PLAY = "assessment-connect-play"


class RolesConfig(BaseModel):
    """Общий набор разрешений, перечисленный в JWT.

    Известные нам разрешения парсятся в JWTPermissions, неизвестные остаются
    в виде строк.
    """

    roles: set[JWTPermissions | str]


class JWTContents(BaseModel):
    """Основное содержимое JWT, парсящееся после проверки подписи."""

    sub: UUID
    resource_access: dict[str, RolesConfig]
    given_name: str
    family_name: str
