import logging
from homeassistant.components.sensor import SensorEntity
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
    """Met en place les capteurs Air Pet à partir d'une entrée de configuration."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        AirPetStatusSensor(coordinator, entry),
    ]
    
    async_add_entities(entities)

class AirPetStatusSensor(CoordinatorEntity, SensorEntity):
    """Représentation du capteur d'état principal de la litière Air Pet."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Litière Air Pet Statut"
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_icon = "mdi:cat"

    @property
    def native_value(self):
        """Retourne l'état actuel de la litière basé sur les données reçues de l'API."""
        if self.coordinator.data is None:
            return "Inconnu"
        
        # Extrait l'état de la réponse JSON (à adapter selon la structure exacte renvoyée par l'API)
        return self.coordinator.data.get("data", {}).get("status", "En ligne")