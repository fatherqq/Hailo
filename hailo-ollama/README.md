# Hailo Local LLM Add-on
## Prerequisites
1. Hardware: Raspberry Pi 5 development board + AI HAT+ 2 (with Hailo-10H AI accelerator chip)
2. System environment: Home Assistant OS is running, and the Hailo driver has been deployed
3. Driver verification: The device node /dev/hailo0 exists in the system, indicating that the driver is loaded correctly
## Usage
1. Install this Add‑on in Home Assistant and start the service.
2. Go to the Add‑on’s Logs page and confirm that the service started successfully and is running without errors.
3. Install the companion conversation integration via HACS:
- Open the HACS management page, click the three‑dot menu in the upper right corner, and select Custom repositories.
- Enter the repository URL https://github.com/sgeorgakis/hailo-ollama-hass and select Integration as the category, then confirm to add.
- Find Hailo Ollama in the HACS integration list and click to download and install it.
- After installation, restart Home Assistant to apply the integration.
4. Complete the integration configuration:
- Go to Settings → Devices & Services, click Add Integration, search for and select Hailo Ollama, then follow the on‑screen guide to complete the configuration parameters such as service connection and model selection.