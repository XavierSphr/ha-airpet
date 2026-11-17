import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configuration de l'intégration Air Pet."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Déchargement de l'intégration."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor", "button"])