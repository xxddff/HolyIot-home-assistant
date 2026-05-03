"""HolyIot BLE device parsing helpers."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

_LOGGER = logging.getLogger(__name__)

# HolyIot classic beacon payload (0x5242) with battery at index 1.
HOLYIOT_SERVICE_UUID: Final[str] = "00005242-0000-1000-8000-00805f9b34fb"
HOLYIOT_MIN_PAYLOAD_LENGTH: Final[int] = 2

# NexBeacon Pro advertises service data for device information (0x180A)
# where battery percentage is carried in the last byte.
NEXBEACON_PRO_SERVICE_UUID: Final[str] = "0000180a-0000-1000-8000-00805f9b34fb"
NEXBEACON_PRO_MIN_PAYLOAD_LENGTH: Final[int] = 1
HOLYIOT_BATTERY_UNKNOWN: Final[int] = 0xFF


@dataclass(frozen=True, slots=True)
class _BatteryParser:
    """Parser definition for a specific HolyIot-compatible payload format."""

    service_uuid: str
    min_payload_length: int
    parser_name: str
    extractor: Callable[[bytes], int]


def _extract_classic_battery(payload: bytes) -> int:
    """Extract battery value from classic HolyIot payload."""
    return payload[1]


def _extract_nexbeacon_pro_battery(payload: bytes) -> int:
    """Extract battery value from NexBeacon Pro payload."""
    return payload[-1]


BATTERY_PARSERS: Final[tuple[_BatteryParser, ...]] = (
    _BatteryParser(
        service_uuid=HOLYIOT_SERVICE_UUID,
        min_payload_length=HOLYIOT_MIN_PAYLOAD_LENGTH,
        parser_name="classic",
        extractor=_extract_classic_battery,
    ),
    _BatteryParser(
        service_uuid=NEXBEACON_PRO_SERVICE_UUID,
        min_payload_length=NEXBEACON_PRO_MIN_PAYLOAD_LENGTH,
        parser_name="NexBeacon Pro",
        extractor=_extract_nexbeacon_pro_battery,
    ),
)


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
        for parser in BATTERY_PARSERS:
            payload = service_info.service_data.get(parser.service_uuid)
            if payload is None:
                continue

            if len(payload) >= parser.min_payload_length:
                return True

            _LOGGER.debug(
                "HolyIot advertisement from %s ignored: %s payload too short (%d bytes)",
                getattr(service_info, "address", "unknown"),
                parser.parser_name,
                len(payload),
            )

        return False

    def update(self, service_info: Any) -> HolyIotUpdate | None:
        """
        Parse a BluetoothServiceInfoBleak into a HolyIotUpdate.

        Returns None if the data does not match the expected
        HolyIot format.
        """
        battery: int | None = None
        for parser in BATTERY_PARSERS:
            payload = service_info.service_data.get(parser.service_uuid)
            if payload is None or len(payload) < parser.min_payload_length:
                continue
            battery = parser.extractor(payload)
            break

        if battery is None:
            _LOGGER.debug(
                "HolyIot update from %s ignored: no supported battery payload",
                getattr(service_info, "address", "unknown"),
            )
            return None

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
