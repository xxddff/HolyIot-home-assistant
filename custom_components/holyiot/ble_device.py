"""HolyIot BLE device parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

# HolyIot uses a 16-bit service UUID 0x5242 in service data.
HOLYIOT_SERVICE_UUID: Final[str] = "00005242-0000-1000-8000-00805f9b34fb"
HOLYIOT_PAYLOAD_LENGTH: Final[int] = 17
HOLYIOT_MAC_LENGTH: Final[int] = 6
HOLYIOT_BATTERY_UNKNOWN: Final[int] = 0xFF


@dataclass(slots=True)
class HolyIotUpdate:
    """Representation of a single HolyIot BLE update.

    Only the battery field is exposed for now, but the
    structure is ready for future extensions (temperature,
    humidity, etc.).
    """

    address: str
    battery: int | None


class HolyIotBluetoothDeviceData:
    """Parse HolyIot BLE advertisements.

    The implementation is inspired by ble_monitor's HolyIot
    parser, but only keeps the bits we currently need.
    """

    def supported(self, service_info: BluetoothServiceInfoBleak) -> bool:
        """Return True if this service_info looks like a HolyIot device."""
        if HOLYIOT_SERVICE_UUID not in service_info.service_data:
            return False

        payload = service_info.service_data[HOLYIOT_SERVICE_UUID]
        # HolyIot payload should be 17 bytes, matching ble_monitor.
        if len(payload) != HOLYIOT_PAYLOAD_LENGTH:
            return False

        # Validate embedded MAC against the advertisement address when possible.
        # payload[6:12] is the MAC, address is in "AA:BB:CC:DD:EE:FF" format.
        embedded_mac = payload[6:12]
        address = service_info.address
        if len(embedded_mac) == HOLYIOT_MAC_LENGTH and ":" in address:
            # Compare by stripping colons and normalising case.
            addr_bytes = bytes.fromhex(address.replace(":", ""))
            if addr_bytes != embedded_mac:
                return False

        return True

    def update(self, service_info: BluetoothServiceInfoBleak) -> HolyIotUpdate | None:
        """Parse a BluetoothServiceInfoBleak into a HolyIotUpdate.

        Returns None if the data does not match the expected
        HolyIot format.
        """
        if HOLYIOT_SERVICE_UUID not in service_info.service_data:
            return None

        payload = service_info.service_data[HOLYIOT_SERVICE_UUID]
        if len(payload) != HOLYIOT_PAYLOAD_LENGTH:
            return None

        embedded_mac = payload[6:12]
        address = service_info.address
        if len(embedded_mac) == HOLYIOT_MAC_LENGTH and ":" in address:
            try:
                addr_bytes = bytes.fromhex(address.replace(":", ""))
            except ValueError:
                return None
            if addr_bytes != embedded_mac:
                return None

        # Battery percentage is at index 5 in the payload.
        battery = payload[5]
        if battery == HOLYIOT_BATTERY_UNKNOWN:
            # 0xFF is treated as "unknown" battery.
            battery_value: int | None = None
        else:
            battery_value = int(battery)

        return HolyIotUpdate(address=address, battery=battery_value)
