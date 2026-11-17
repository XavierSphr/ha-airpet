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

async def async_authenticate_user(hass: HomeAssistant, email: str, password: str) -> str:
    """Authentifie l'utilisateur via l'API cloud et récupère le jeton."""
    # Endpoint officiel de connexion cloud pour les comptes Airrobo / Ubtech
    url = f"https://{API_HOST}/user-service-rest/v2/user/login"
    
    payload = {
        "account": email,
        "password": password,  # Si l'API attend un mot de passe hashé en MD5, appliquez-le ici
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "CatLitterBoxYibai/2.1.8 (com.yibainetwork.airpet; build:734; iOS 27.2.1) Alamofire/5.5.0",
        "X-UBT-AppId": "970010086",
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers, timeout=10) as response:
            if response.status != 200:
                raise ValueError(f"Erreur d'authentification (HTTP {response.status})")
            data = await response.json()
            
            # Extraction du token depuis la réponse de l'API
            token = data.get("data", {}).get("token") or data.get("token")
            if not token:
                raise ValueError("Jeton d'accès introuvable dans la réponse")
            return token

class AirPetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration pour HACS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors = {}

        if user_input is not None:
            try:
                # Étape 1 : Récupération du token via l'e-mail et le mot de passe saisis
                auth_token = await async_authenticate_user(
                    self.hass, user_input["email"], user_input["password"]
                )
                
                data = {
                    "auth_token": auth_token,
                    "serial_number": user_input["serial_number"].strip()
                }
                
                return self.async_create_entry(
                    title=f"Litière Air Pet ({user_input['serial_number']})",
                    data=data,
                )
            except Exception as e:
                _LOGGER.error("Échec de connexion Air Pet: %s", e)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )