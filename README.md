# HolyIot BLE for Home Assistant

HolyIot BLE is a Home Assistant custom integration that passively listens to Bluetooth broadcast data from HolyIot devices and exposes sensor entities in Home Assistant, such as battery level.

Currently the integration is based on passive Bluetooth scanning and only creates battery level sensors.

## Features

- Passively scans BLE broadcast data from HolyIot devices.
- Automatically discovers and creates battery level sensors:
	- Entity type: `sensor`
	- Device class: `battery`
	- Unit: `%`
	- State class: `measurement`

## Installation

### Install via HACS (recommended)

Add the repository as a **Custom repository**.

1. In Home Assistant open **HACS → Integrations**.
2. Click the top-right menu and select **Custom repositories**.
3. Enter this repository URL:

		```text
		https://github.com/xxddff/HolyIot-home-assistant
		```

4. Choose `Integration` as the Category and click **Add**.
5. Return to **HACS → Integrations**, click the `+` button at the bottom right, search for `HolyIot BLE` or `holyiot` and install.
6. After installation, restart Home Assistant as prompted.

## Configuration

### Discovery and setup

HolyIot devices are discovered by Home Assistant via Bluetooth broadcasts:

1. Make sure your host has Bluetooth enabled and the Home Assistant Bluetooth integration is configured properly.
2. After installation and restart, when a HolyIot device broadcasts, Home Assistant will show a new device discovery notification or list the device under **Settings → Devices & Services** for configuration.
3. Follow the prompts to add the device (no manual address is usually required; just confirm the discovered device).

After configuration, the system will automatically create corresponding battery sensor entities, for example:

- `sensor.holyiot_battery` (the actual entity_id may vary by device).

## Development & Testing

The repository includes scripts and configuration for development:

- Use the Dev Container (VS Code) to quickly start a development environment.
- From the repository root run:

		```bash
		./scripts/develop
		```

		This starts a Home Assistant instance with the integration for local debugging.

## Feedback & Support

- Issues and suggestions: please open a GitHub Issue: <https://github.com/xxddff/HolyIot-home-assistant/issues>

PRs are welcome to help improve the HolyIot BLE integration.