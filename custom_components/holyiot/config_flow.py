"""Config flow for HolyIot BLE integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .ble_device import HolyIotBluetoothDeviceData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
ERROR_DISCOVERY_INFO_NOT_SET = "Discovery info not set"


class HolyIotConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HolyIot BLE devices."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._device: HolyIotBluetoothDeviceData | None = None
        self._discovered_devices: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        address = discovery_info.address
        current_ids = self._async_current_ids(include_ignore=False)
        if address in current_ids:
            _LOGGER.debug("HolyIot discovery %s ignored: already configured", address)
            return self.async_abort(reason="already_configured")

        device = HolyIotBluetoothDeviceData()
        if not device.supported(discovery_info):
            _LOGGER.debug(
                "HolyIot discovery %s ignored: not supported by parser", address
            )
            return self.async_abort(reason="not_supported")
        _LOGGER.debug("HolyIot discovered %s", address)

        self._discovery_info = discovery_info
        self._device = device
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery from bluetooth step."""
        if self._discovery_info is None:
            raise RuntimeError(ERROR_DISCOVERY_INFO_NOT_SET)

        name = self._discovery_info.name or self._discovery_info.address
        if user_input is not None:
            return self.async_create_entry(
                title=name, data={CONF_ADDRESS: self._discovery_info.address}
            )

        placeholders = {"name": name}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=placeholders,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered_devices[address], data={CONF_ADDRESS: address}
            )

        current_ids = self._async_current_ids(include_ignore=False)
        for service_info in async_discovered_service_info(self.hass):
            address = service_info.address
            if address in current_ids or address in self._discovered_devices:
                continue

            device = HolyIotBluetoothDeviceData()
            if not device.supported(service_info):
                _LOGGER.debug(
                    "HolyIot cached candidate %s ignored: not supported by parser",
                    address,
                )
                continue

            name = service_info.name or address
            self._discovered_devices[address] = name
            _LOGGER.debug(
                "HolyIot cached discovery %s (%s) added to user selection",
                address,
                name,
            )

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(self._discovered_devices)}
            ),
        )
