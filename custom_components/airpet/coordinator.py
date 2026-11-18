import logging
import aiohttp
import asyncio
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from .const import DOMAIN, API_HOST

_LOGGER = logging.getLogger(__name__)

class AirPetDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinateur pour récupérer l'état de la litière Air Pet."""

    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession, auth_token: str, serial_number: str) -> None:
        self.session = session
        self.auth_token = auth_token
        self.serial_number = serial_number
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self):
        """Récupère les données depuis l'API cloud."""
        url = f"https://{API_HOST}/catbox-server/box/config/allConfig?serialNumber={self.serial_number}"
        
        headers = {
            "Authorization": self.auth_token,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "CatLitterBoxYibai/2.1.8 (com.yibainetwork.airpet; build:734; iOS 27.2.1) Alamofire/5.5.0",
            "X-UBT-AppId": "970010086",
        }

        try:
            async with self.session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Erreur HTTP: {response.status}")
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            raise UpdateFailed(
                f"Erreur de communication avec l'API Air Pet : {error}"
            ) from error

        _LOGGER.debug(
            "allConfig Air Pet : clés=%s, hors data=%s",
            list(data.keys()),
            {k: v for k, v in data.items() if k != "data"},
        )
        return data

    async def async_send_command(self, action: str) -> bool:
        """Envoie une commande à la litière (ex: lancer le nettoyage)."""
        url = f"https://{API_HOST}/catbox-server/box/action/clean" 
        
        headers = {
            "Authorization": self.auth_token,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "CatLitterBoxYibai/2.1.8 (com.yibainetwork.airpet; build:734; iOS 27.2.1) Alamofire/5.5.0",
            "X-UBT-AppId": "970010086",
        }
        
        payload = {
            "serialNumber": self.serial_number,
            "action": action
        }

        try:
            async with self.session.post(url, headers=headers, json=payload, timeout=10) as response:
                if response.status == 200:
                    await self.async_request_refresh()
                    return True
                _LOGGER.error("Erreur lors de l'envoi de la commande: %s", response.status)
                return False
        except Exception as error:
            _LOGGER.error("Exception lors de l'envoi de la commande: %s", error)
            return False