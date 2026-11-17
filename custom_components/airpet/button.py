import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Met en place le bouton de commande Air Pet."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        AirPetCleanButton(coordinator, entry)
    ])

class AirPetCleanButton(CoordinatorEntity, ButtonEntity):
    """Représentation du bouton pour lancer le nettoyage."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Lancer le nettoyage de la litière"
        self._attr_unique_id = f"{entry.entry_id}_clean_button"
        self._attr_icon = "mdi:broom"

    async def async_press(self) -> None:
        """Action exécutée lorsque l'on clique sur le bouton dans Home Assistant."""
        await self.coordinator.async_send_command("start_clean")