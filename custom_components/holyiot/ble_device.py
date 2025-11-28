"""HolyIot BLE device parsing helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Final

_LOGGER = logging.getLogger(__name__)

# HolyIot uses a 16-bit service UUID 0x5242 in service data.
HOLYIOT_SERVICE_UUID: Final[str] = "00005242-0000-1000-8000-00805f9b34fb"
# For the HolyIot device variant we target here, ESPHome
# examples indicate that the battery percentage is stored at
# index 1 of the service data (x[1]). Require at least two
# bytes so that index 1 is always present.
HOLYIOT_MIN_PAYLOAD_LENGTH: Final[int] = 2
HOLYIOT_BATTERY_UNKNOWN: Final[int] = 0xFF


@dataclass(slots=True)
class HolyIotUpdate:
    """
    Representation of a single HolyIot BLE update.

    Only the battery field is exposed for now, but the
    structure is ready for future extensions (temperature,
    humidity, etc.).
    """

    address: str
    battery: int | None


class HolyIotBluetoothDeviceData:
    """
    Parse HolyIot BLE advertisements.

    The implementation is inspired by ble_monitor's HolyIot
    parser, but only keeps the bits we currently need.
    """

    def supported(self, service_info: Any) -> bool:
        """Return True if this service_info looks like a HolyIot device."""
        if HOLYIOT_SERVICE_UUID not in service_info.service_data:
            return False

        payload = service_info.service_data[HOLYIOT_SERVICE_UUID]
        if len(payload) < HOLYIOT_MIN_PAYLOAD_LENGTH:
            _LOGGER.debug(
                "HolyIot advertisement from %s ignored: payload too short (%d bytes)",
                getattr(service_info, "address", "unknown"),
                len(payload),
            )
            return False

        # No further structural checks: we only care that the UUID
        # matches and there is at least one byte for the battery
        # field at index 1.
        return True

    def update(self, service_info: Any) -> HolyIotUpdate | None:
        """
        Parse a BluetoothServiceInfoBleak into a HolyIotUpdate.

        Returns None if the data does not match the expected
        HolyIot format.
        """
        if HOLYIOT_SERVICE_UUID not in service_info.service_data:
            return None

        payload = service_info.service_data[HOLYIOT_SERVICE_UUID]
        if len(payload) < HOLYIOT_MIN_PAYLOAD_LENGTH:
            _LOGGER.debug(
                "HolyIot update from %s ignored: payload too short (%d bytes)",
                getattr(service_info, "address", "unknown"),
                len(payload),
            )
            return None

        # For this HolyIot variant, battery is stored at index 1,
        # matching ESPHome examples that use x[1].
        battery = payload[1]
        if battery == HOLYIOT_BATTERY_UNKNOWN:
            # 0xFF is treated as "unknown" battery.
            battery_value: int | None = None
        else:
            battery_value = int(battery)

        _LOGGER.debug(
            "HolyIot update %s: battery=%s (raw=0x%02x)",
            getattr(service_info, "address", "unknown"),
            battery_value,
            battery,
        )

        return HolyIotUpdate(address=service_info.address, battery=battery_value)
