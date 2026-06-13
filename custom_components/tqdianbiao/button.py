"""TQ 电表按钮实体。"""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import TqCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tqdianbiao"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置按钮实体。"""
    coordinator: TqCoordinator = entry.runtime_data
    async_add_entities([TqRefreshButton(coordinator)])


class TqRefreshButton(CoordinatorEntity[TqCoordinator], ButtonEntity):
    """刷新抄表按钮。"""

    _attr_has_entity_name = True
    _attr_unique_id = f"{DOMAIN}_refresh"
    _attr_translation_key = "refresh"
    _attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """点击按钮时触发刷新抄表并立即拉取新数据。"""
        try:
            await self.hass.async_add_executor_job(
                self.coordinator.trigger_refresh
            )
            await self.coordinator.async_request_refresh()
        except Exception as exc:
            _LOGGER.error("刷新抄表失败: %s", exc)
