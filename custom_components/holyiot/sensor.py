"""HolyIot BLE battery sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorCoordinator,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE

from .ble_device import HolyIotUpdate

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

BATTERY_SENSOR_DESCRIPTION = SensorEntityDescription(
    key="battery",
    device_class=SensorDeviceClass.BATTERY,
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
)


def _battery_update_to_bluetooth_data_update(
    sensor_update: HolyIotUpdate,
) -> PassiveBluetoothDataUpdate:
    """Convert a HolyIotUpdate into a bluetooth data update."""
    entity_key = PassiveBluetoothEntityKey("battery", None)

    return PassiveBluetoothDataUpdate(
        devices={},
        entity_descriptions={entity_key: BATTERY_SENSOR_DESCRIPTION},
        entity_data={entity_key: sensor_update.battery},
        entity_names={entity_key: None},
    )


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the HolyIot BLE battery sensor platform."""
    coordinator: PassiveBluetoothProcessorCoordinator[HolyIotUpdate] = (
        entry.runtime_data
    )
    processor: PassiveBluetoothDataProcessor[int | None, HolyIotUpdate]
    processor = PassiveBluetoothDataProcessor(_battery_update_to_bluetooth_data_update)

    entry.async_on_unload(
        processor.async_add_entities_listener(
            HolyIotBluetoothSensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(
        coordinator.async_register_processor(processor, SensorEntityDescription)
    )


class HolyIotBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[
        PassiveBluetoothDataProcessor[int | None, HolyIotUpdate]
    ],
    SensorEntity,
):
    """Representation of a HolyIot BLE battery sensor."""

    @property
    def native_value(self) -> int | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)
