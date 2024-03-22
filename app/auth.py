import logging
from datetime import datetime

import jwt
import pydantic
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from jwt import PyJWKSet
from jwt.exceptions import InvalidAudienceError, InvalidTokenError, ExpiredSignatureError, MissingRequiredClaimError
from keycloak import KeycloakOpenID
from rest_framework import exceptions

from rest_framework.authentication import BaseAuthentication

from app.serializations import JWTContents, JWTHeader


def get_auth_header(request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    return auth.removeprefix("Bearer ")


class ExternalApiAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = get_auth_header(request)
        if auth != settings.EXTERNAL_API_KEY:
            raise exceptions.AuthenticationFailed("Invalid API key")
        return None, None


def validate_token(
    token: str,
    error_cls: type[Exception] = exceptions.AuthenticationFailed
) -> JWTContents:
    """
    Функция для валидации токена
    Проверяет наличие токена, его префикс и валидность в Keycloak

    :param token: Токен с префиксом Bearer
    :param error_cls: Класс ошибки для выброса
    """

    prefix = "Bearer "

    if not token.startswith(prefix):
        raise error_cls("Invalid token header. No credentials provided.")

    token = token.removeprefix(prefix)
    jwks = JWKeyCache.instance()

    try:
        header = JWTHeader.model_validate(
            jwt.get_unverified_header(token)
        )
        pub_key = jwks.get_key_by_id(header.kid)

        jwt_decoded = JWTContents.model_validate(
            jwt.decode(
                token,
                pub_key,
                algorithms=["RS256"],
                audience=settings.HR_AUDIENCE,
                options={
                    "verify_aud": False,
                    "verify_iat": False,
                    "verify_exp": settings.VERIFY_EXPIRATION,
                },
            )
        )
    except KeyError:
        raise error_cls("JWKS key id not found")
    except MissingRequiredClaimError as e:
        raise error_cls(str(e))
    except ExpiredSignatureError:
        raise error_cls("Signature expired")
    except InvalidAudienceError:
        raise error_cls("JWT audience mismatch")
    except InvalidTokenError:
        raise error_cls("JWT decode error")
    except pydantic.ValidationError as e:
        raise error_cls(f"Token content is invalid: {e}")

    return jwt_decoded


class JWKeyCache:
    """Кэш ключей для проверки аутентификации живых игроков."""

    THROTTLE_TIME = 5
    __instance = None

    def __init__(self) -> None:
        """Создает экземпляр клиента keycloak и кэш ключей."""

        self._keycloak_client = KeycloakOpenID(
            server_url=settings.KEYCLOAK_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
        )
        self._last_update: datetime | None = None
        self._keys: dict[str, str] = {}

    def _update_keys(self) -> None:
        """Обновляет кэш ключей с сервера JWKS."""

        if self._last_update is not None:
            time_since = datetime.now() - self._last_update

            if time_since.total_seconds() < self.THROTTLE_TIME:
                logging.debug("Too many JWKS updates")
                return

        self._last_update = datetime.now()

        certs = self._keycloak_client.certs()
        jset = PyJWKSet.from_dict(certs)

        self._keys = {
            key.key_id: key.key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")
            for key in jset.keys
            if key.key_type == "RSA"
        }

    def get_key_by_id(self, key_id: str) -> str:
        """Получить ключ по key_id."""

        key: str | None = self._keys.get(key_id)

        if key is not None:
            return key

        logging.debug(f"Key_id {key_id} not found in cache, updating...")

        self._update_keys()

        return self._keys[key_id]

    @classmethod
    def instance(cls):
        """Возвращает разделяемый instance."""

        if cls.__instance is None:
            cls.__instance = JWKeyCache()

        return cls.__instance

