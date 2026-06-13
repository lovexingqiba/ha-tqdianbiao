"""TQ 电表数据协调器。"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TqApi

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tqdianbiao"
SCAN_INTERVAL = timedelta(minutes=30)


class TqCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self._api = TqApi(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])

    async def _async_update_data(self) -> dict[str, Any]:
        """先登录（executor），再获取数据（executor），分两次调用。"""
        try:
            await self.hass.async_add_executor_job(self._api.login)
            return await self.hass.async_add_executor_job(self._api.fetch_all)
        except Exception as exc:
            raise UpdateFailed(str(exc)) from exc
