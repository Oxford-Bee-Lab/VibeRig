from expidite_rpi import RpiCore

from VibeRig.configs.fleet_config_lab import INVENTORY


def test_monitor_and_controller_startup_configuration() -> None:
    """Validate the monitor and controller device configurations without hardware."""
    is_valid, errors = RpiCore().test_configuration(fleet_config=INVENTORY)

    assert is_valid, errors
