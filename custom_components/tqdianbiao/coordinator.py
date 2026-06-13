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
    """TQ 电表数据协调器。"""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self._api = TqApi(
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )

    def _fetch(self) -> dict[str, Any]:
        """同步获取所有数据（在线程池中执行）。"""
        try:
            return self._api.fetch_all()
        except Exception as exc:
            # 如果 token 过期，重新登录重试一次
            if "token" in str(exc).lower():
                self._api.login()
                return self._api.fetch_all()
            raise exc

    async def _async_update_data(self) -> dict[str, Any]:
        """由定时器或手动触发调用。"""
        try:
            return await self.hass.async_add_executor_job(self._fetch)
        except Exception as exc:
            raise UpdateFailed(f"获取电表数据失败: {exc}") from exc
