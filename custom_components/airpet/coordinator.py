import asyncio
import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_HOST, APP_ID

_LOGGER = logging.getLogger(__name__)

PRODUCT_ID = "97001"  # en-tête "product" envoyé par l'app sur les routes catbox-server

USER_AGENT = (
    "CatLitterBoxYibai/2.1.8 (com.yibainetwork.airpet; build:734; iOS 27.2.1) "
    "Alamofire/5.5.0"
)


class AirPetDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinateur pour récupérer l'état de la litière Air Pet."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        auth_token: str,
        serial_number: str,
        device_id: str,
    ) -> None:
        self.session = session
        self.auth_token = auth_token
        self.serial_number = serial_number
        self.device_id = device_id
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )

    def _headers(self) -> dict[str, str]:
        """En-têtes communs, calqués sur ceux de l'app officielle."""
        return {
            "Authorization": self.auth_token,
            "Accept": "application/json",
            "Accept-Language": "fr-FR;q=1.0",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": USER_AGENT,
            "product": PRODUCT_ID,
            "X-UBT-AppId": APP_ID,
            "X-UBT-DeviceId": self.device_id,
            "X-UBT-Language": "fr",
        }

    async def _async_update_data(self):
        """Récupère les données depuis l'API cloud."""
        url = (
            f"https://{API_HOST}/catbox-server/box/config/allConfig"
            f"?serialNumber={self.serial_number}"
        )

        try:
            async with self.session.get(
                url,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    body = await response.text()
                    _LOGGER.warning(
                        "allConfig Air Pet : HTTP %s, réponse : %s",
                        response.status,
                        body[:300],
                    )
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
        """Envoie une commande à la litière.

        ATTENTION : l'URL et le corps ci-dessous ne sont pas encore vérifiés
        avec une capture de l'app officielle.
        """
        url = f"https://{API_HOST}/catbox-server/box/action/clean"
        payload = {"serialNumber": self.serial_number, "action": action}

        try:
            async with self.session.post(
                url,
                headers=self._headers(),
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    await self.async_request_refresh()
                    return True
                body = await response.text()
                _LOGGER.error(
                    "Commande Air Pet : HTTP %s, réponse : %s",
                    response.status,
                    body[:300],
                )
                return False
        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            _LOGGER.error("Exception lors de l'envoi de la commande: %s", error)
            return False