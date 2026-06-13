"""TQ 电表传感器 - 最简版：只显示 token。"""
from __future__ import annotations

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
    async_add_entities([TqTokenSensor(coordinator)])


class TqTokenSensor(CoordinatorEntity[TqCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_unique_id = f"{DOMAIN}_token"
    _attr_name = "Token"
    _attr_icon = "mdi:key"

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("token", "")
