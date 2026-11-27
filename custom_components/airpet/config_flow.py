import asyncio
import hashlib
import logging
import uuid

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, API_HOST, APP_ID

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
        vol.Required("serial_number"): str,
    }
)


class CannotConnect(Exception):
    """Serveur injoignable ou réponse inattendue."""


class InvalidAuth(Exception):
    """Identifiants refusés."""


async def async_authenticate_user(
    hass: HomeAssistant, email: str, password: str, device_id: str
) -> dict:
    """Se connecte à l'API cloud et retourne token, refresh_token et expire_at."""
    url = f"https://{API_HOST}/user-service-rest/v2/user/login"
    payload = {
        "account": email,
        "accountType": "1",
        "appId": APP_ID,
        "areaCode": "FR",
        "password": hashlib.md5(password.encode()).hexdigest(),
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "CatLitterBoxYibai/2.1.8 (com.yibainetwork.airpet; build:734; iOS 27.2.1) Alamofire/5.5.0",
        "language": "fr",
        "X-UBT-AppId": APP_ID,
        "X-UBT-DeviceId": device_id,
        "X-UBT-Language": "fr",
    }
    session = async_get_clientsession(hass)

    try:
        async with session.put(
            url,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            _LOGGER.debug("Login Air Pet : HTTP %s", response.status)
            if response.status != 200:
                body = (await response.text())[:500]
                _LOGGER.warning(
                    "Login Air Pet refusé : HTTP %s, corps : %s",
                    response.status,
                    body,
                )
                if response.status in (401, 403):
                    raise InvalidAuth(f"HTTP {response.status}")
                raise CannotConnect(f"HTTP {response.status}")
            data = await response.json(content_type=None)
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        raise CannotConnect(f"{type(err).__name__}: {err}") from err

    inner = data.get("data") if isinstance(data.get("data"), dict) else {}
    # On logue tout sauf les valeurs de "data" (qui contient le jeton)
    _LOGGER.debug(
        "Réponse login Air Pet (hors data) : %s",
        {k: v for k, v in data.items() if k != "data"},
    )
    _LOGGER.debug("Clés présentes dans data : %s", list(inner.keys()))

    token_info = inner.get("token") or data.get("token")
    if isinstance(token_info, dict):
        token = token_info.get("token")
        refresh_token = token_info.get("refreshToken")
        expire_at = token_info.get("expireAt")
    else:
        token, refresh_token, expire_at = token_info, None, None

    if not token or not isinstance(token, str):
        raise InvalidAuth("Jeton introuvable dans la réponse")
    return {"token": token, "refresh_token": refresh_token, "expire_at": expire_at}


class AirPetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            serial = user_input["serial_number"].strip()
            await self.async_set_unique_id(serial)
            self._abort_if_unique_id_configured()

            device_id = str(uuid.uuid4()).upper()
            try:
                auth = await async_authenticate_user(
                    self.hass, user_input["email"], user_input["password"], device_id
                )
            except InvalidAuth as err:
                _LOGGER.warning("Air Pet : authentification refusée (%s)", err)
                errors["base"] = "invalid_auth"
            except CannotConnect as err:
                _LOGGER.warning("Air Pet : connexion impossible (%s)", err)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Air Pet : erreur inattendue")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Litière Air Pet ({serial})",
                    data={
                        "auth_token": auth["token"],
                        "refresh_token": auth["refresh_token"],
                        "expire_at": auth["expire_at"],
                        "serial_number": serial,
                        "device_id": device_id,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )