import asyncio
import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, API_HOST

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


async def async_authenticate_user(hass: HomeAssistant, email: str, password: str) -> str:
    url = f"https://{API_HOST}/user-service-rest/v2/user/login"
    payload = {"account": email, "password": password}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "CatLitterBoxYibai/2.1.8 (com.yibainetwork.airpet; build:734; iOS 27.2.1) Alamofire/5.5.0",
        "X-UBT-AppId": "970010086",
    }
    session = async_get_clientsession(hass)

    try:
        async with session.post(
            url,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            _LOGGER.debug("Login Air Pet : HTTP %s", response.status)
            if response.status in (400, 401, 403):
                raise InvalidAuth(f"HTTP {response.status}")
            if response.status != 200:
                raise CannotConnect(f"HTTP {response.status}")
            data = await response.json(content_type=None)
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        raise CannotConnect(str(err)) from err

    # On logue tout sauf "data" (qui contient le jeton) : code/message d'erreur de l'API
    _LOGGER.debug(
        "Réponse login Air Pet (hors data) : %s",
        {k: v for k, v in data.items() if k != "data"},
    )

    token = (data.get("data") or {}).get("token") or data.get("token")
    if not token:
        raise InvalidAuth("Jeton introuvable dans la réponse")
    return token


class AirPetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            serial = user_input["serial_number"].strip()
            await self.async_set_unique_id(serial)
            self._abort_if_unique_id_configured()

            try:
                token = await async_authenticate_user(
                    self.hass, user_input["email"], user_input["password"]
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
                    data={"auth_token": token, "serial_number": serial},
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )