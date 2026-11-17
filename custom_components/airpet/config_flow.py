import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("auth_token"): str,
        vol.Required("serial_number"): str,
    }
)

async def async_validate_input(hass: HomeAssistant, data: dict) -> None:
    """Valide les identifiants saisis par l'utilisateur."""
    # Vous pouvez ajouter ici une vérification si besoin, 
    # ou simplement valider la présence des champs.
    pass

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
                await async_validate_input(self.hass, user_input)
                
                # Crée l'entrée dans Home Assistant avec les données saisies
                return self.async_create_entry(
                    title=f"Litière Air Pet ({user_input['serial_number']})",
                    data=user_input,
                )
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )