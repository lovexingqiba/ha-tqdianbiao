"""TQ 电表传感器 - 显示 payInfo 原始响应。"""
from __future__ import annotations

import json

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import TqCoordinator

DOMAIN = "tqdianbiao"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TqCoordinator = entry.runtime_data
    async_add_entities([TqPayInfoSensor(coordinator)])


class TqPayInfoSensor(CoordinatorEntity[TqCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_unique_id = f"{DOMAIN}_payinfo"
    _attr_name = "payInfo 响应"
    _attr_icon = "mdi:transmission-tower"

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return "无数据"
        sc = self.coordinator.data.get("status_code", 0)
        return f"HTTP {sc}"

    @property
    def extra_state_attributes(self) -> dict:
        if self.coordinator.data is None:
            return {}
        return {
            "status_code": self.coordinator.data.get("status_code"),
            "body": self.coordinator.data.get("body", "")[:800],
        }
