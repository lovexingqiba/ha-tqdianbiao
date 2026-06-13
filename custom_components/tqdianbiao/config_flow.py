"""TQ 电表配置流。"""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .api import TqApi

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tqdianbiao"
CONF_DEVICE_NAME = "device_name"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_DEVICE_NAME, default="乐和园电表"): str,
    }
)


class TqConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                api = TqApi(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                await self.hass.async_add_executor_job(api.login)
            except Exception as exc:
                _LOGGER.exception("登录失败: %s", exc)
                errors["base"] = "cannot_connect"
            else:
                device_name = user_input.get(CONF_DEVICE_NAME, "乐和园电表")
                await self.async_set_unique_id(
                    f"tqdianbiao_{user_input[CONF_USERNAME]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=device_name,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, user_input: dict | None = None
    ) -> FlowResult:
        return await self.async_step_user(user_input)
