import logging
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, API_HOST

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
        vol.Required("serial_number"): str,
    }
)

async def async_authenticate_and_get_token(hass: HomeAssistant, email: str, password: str) -> str:
    """Se connecte à l'API Airrobo en utilisant la route et les headers exacts capturés."""
    url = f"https://{API_HOST}/v1/ubtechinc-im-manager/im/login"
    
    # Le corps de la requête (payload) contenant l'e-mail et le mot de passe
    payload = {
        "email": email,
        "password": password
    }
    
    # Les en-têtes requis par l'application mobile pour authentifier la requête
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "CatLitterBoxYibai/2.1.8 (com.yibainetwork.airpet; build:734; iOS 27.2.1) Alamofire/5.5.0",
        "X-UBT-AppId": "970010086",
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers, timeout=10) as response:
            if response.status != 200:
                raise ValueError(f"Erreur HTTP: {response.status}")
            data = await response.json()
            
            # Récupération du jeton (Authorization) renvoyé par l'API
            token = data.get("data", {}).get("token") or data.get("token")
            if not token:
                raise ValueError("Token introuvable dans la réponse de l'API")
            return token

class AirPetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration de l'intégration Air Pet."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Gère l'étape initiale de configuration par l'utilisateur."""
        errors = {}

        if user_input is not None:
            try:
                auth_token = await async_authenticate_and_get_token(
                    self.hass, user_input["email"], user_input["password"]
                )
                
                if not auth_token:
                    raise ValueError("Token introuvable")

                data = {
                    "auth_token": auth_token,
                    "serial_number": user_input["serial_number"]
                }
                
                return self.async_create_entry(
                    title=f"Litière Air Pet ({user_input['serial_number']})",
                    data=data,
                )
            except Exception as e:
                _LOGGER.error("Erreur de connexion Air Pet: %s", e)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )