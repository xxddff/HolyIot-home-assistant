"""The HolyIot Bluetooth integration."""

from __future__ import annotations

import logging

from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .ble_device import HolyIotBluetoothDeviceData, HolyIotUpdate
from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


type HolyIotConfigEntry = ConfigEntry[
    PassiveBluetoothProcessorCoordinator[HolyIotUpdate]
]


async def async_setup_entry(hass: HomeAssistant, entry: HolyIotConfigEntry) -> bool:
    """Set up HolyIot BLE device from a config entry."""
    address = entry.data.get(CONF_ADDRESS) or entry.unique_id
    if address is None:
        return False

    data = HolyIotBluetoothDeviceData()
    coordinator: PassiveBluetoothProcessorCoordinator[HolyIotUpdate]
    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        update_method=data.update,
        connectable=False,
    )

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Only start after all platforms have had a chance to subscribe
    entry.async_on_unload(coordinator.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HolyIotConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
