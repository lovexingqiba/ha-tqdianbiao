"""TQ 电表数据协调器 - 最简版：只保存 token。"""
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
SCAN_INTERVAL = timedelta(hours=24)


class TqCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self._api = TqApi(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
        self._token = ""

    async def _async_update_data(self) -> dict[str, Any]:
        """每 24 小时重新登录一次刷新 token"""
        try:
            token = await self.hass.async_add_executor_job(self._api.login)
            self._token = token
            return {"token": token}
        except Exception as exc:
            raise UpdateFailed(f"登录失败: {exc}") from exc
