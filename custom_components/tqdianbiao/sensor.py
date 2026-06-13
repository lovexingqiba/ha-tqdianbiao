"""TQ 电表传感器实体，挂载到「乐和园电表」设备下。"""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import TqCoordinator
from .config_flow import CONF_DEVICE_NAME

DOMAIN = "tqdianbiao"

SENSOR_DEFINITIONS: list[dict[str, Any]] = [
    {
        "key": "balance",
        "name": "电费余额",
        "device_class": SensorDeviceClass.MONETARY,
        "unit": "CNY",
        "icon": "mdi:currency-cny",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "key": "total_usage",
        "name": "累计用电量",
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:lightning-bolt",
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    {
        "key": "yesterday_usage",
        "name": "昨日用电量",
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:lightning-bolt-outline",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "key": "yesterday_fee",
        "name": "昨日电费",
        "device_class": SensorDeviceClass.MONETARY,
        "unit": "CNY",
        "icon": "mdi:cash-remove",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "key": "update_time",
        "name": "抄表时间",
        "device_class": SensorDeviceClass.TIMESTAMP,
        "unit": None,
        "icon": "mdi:clock-outline",
        "state_class": None,
    },
    {
        "key": "latest_pay_amount",
        "name": "最近充值金额",
        "device_class": SensorDeviceClass.MONETARY,
        "unit": "CNY",
        "icon": "mdi:cash-plus",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "key": "latest_pay_date",
        "name": "最近充值日期",
        "device_class": SensorDeviceClass.TIMESTAMP,
        "unit": None,
        "icon": "mdi:calendar",
        "state_class": None,
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TqCoordinator = entry.runtime_data
    async_add_entities(
        TqSensor(coordinator, definition, entry) for definition in SENSOR_DEFINITIONS
    )


class TqSensor(CoordinatorEntity[TqCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TqCoordinator,
        definition: dict[str, Any],
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._key = definition["key"]
        self._attr_unique_id = f"{DOMAIN}_{self._key}"
        self._attr_translation_key = self._key
        self._attr_device_class = definition["device_class"]
        self._attr_native_unit_of_measurement = definition["unit"]
        self._attr_icon = definition["icon"]
        self._attr_state_class = definition["state_class"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get(CONF_DEVICE_NAME, "乐和园电表"),
            manufacturer="拓强",
            model="单相远程预付费",
            sw_version="1.0.0",
        )

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)
