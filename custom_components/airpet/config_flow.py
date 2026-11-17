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
    """Se connecte à l'API Airrobo pour récupérer le jeton d'authentification."""
    url = f"https://{API_HOST}/catbox-server/web/user/login"  # Remplacez par l'URL exacte de login capturée si besoin
    payload = {
        "email": email,
        "password": password
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=10) as response:
            if response.status != 200:
                raise ValueError("Identifiants invalides ou erreur serveur")
            data = await response.json()
            # Adaptez le chemin selon la structure JSON de la réponse de connexion
            return data.get("data", {}).get("token")

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
                # Récupère automatiquement le token grâce à l'email et au mot de passe
                auth_token = await async_authenticate_and_get_token(
                    self.hass, user_input["email"], user_input["password"]
                )
                
                if not auth_token:
                    raise ValueError("Token introuvable dans la réponse")

                # On stocke le token et le numéro de série pour le coordinateur
                data = {
                    "auth_token": auth_token,
                    "serial_number": user_input["serial_number"]
                }
                
                return self.async_create_entry(
                    title=f"Litière Air Pet ({user_input['serial_number']})",
                    data=data,
                )
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )