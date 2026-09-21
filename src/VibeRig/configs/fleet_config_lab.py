import logging
from dataclasses import dataclass

from expidite_rpi import DeviceCfg, WifiClient

from VibeRig.configs import my_device_recipes

wifi_clients: list[WifiClient] = [
    WifiClient(
        ssid="bee-ops",
        pw="abcdabcd",
        priority=100,
    ),
    WifiClient(
        ssid="bee-ops-zone",
        pw="abcdabcd",
        priority=80,
    ),
    WifiClient(
        ssid="bee-ops-eero",
        pw="abcdabcd",
        priority=80,
    ),
    WifiClient(
        ssid="GNX103510",
        pw="XQSX3SSAPSPH",
        priority=80,
    ),
]


@dataclass
class DefaultDevice(DeviceCfg):
    log_level: int = logging.DEBUG
    wifi_clients: list[WifiClient] = wifi_clients


##############################################################################################################
# Define per-device configuration for the fleet of devices
##############################################################################################################
INVENTORY: list[DeviceCfg] = [
    DeviceCfg(
        name="Vibe-rig-controller",
        device_id="d83add4fc38b",
        notes="Vibe rig controller in Whytam lab",
        dp_trees_create_method=my_device_recipes.create_vibe_rig_controller,
    ),
    DeviceCfg(
        name="Vibe-rig-monitor",
        device_id="d83addf7857a",
        notes="Vibe rig monitor in Whytam lab",
        dp_trees_create_method=my_device_recipes.create_vibe_rig_monitor,
    ),
]
