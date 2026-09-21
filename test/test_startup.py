import pytest
from expidite_rpi import RpiCore
from expidite_rpi.core.edge_orchestrator import EdgeOrchestrator

from VibeRig.configs.fleet_config_lab import INVENTORY
from VibeRig.controller import vibe_controller


def test_monitor_and_controller_startup_configuration() -> None:
    """Validate the monitor and controller device configurations without hardware."""
    is_valid, errors = RpiCore().test_configuration(fleet_config=INVENTORY)

    assert is_valid, errors
    assert not errors, errors


def test_rpi_core_starts_and_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start and stop the RpiCore lifecycle without starting physical sensors."""
    started = False
    stopped = False

    def start_orchestrator() -> None:
        nonlocal started
        started = True

    class OrchestratorStub:
        def stop_all(self: object) -> None:
            nonlocal stopped
            stopped = True

    def get_orchestrator() -> OrchestratorStub:
        return OrchestratorStub()

    monkeypatch.setattr(EdgeOrchestrator, "start_all_with_watchdog", start_orchestrator)
    monkeypatch.setattr(EdgeOrchestrator, "get_instance", get_orchestrator)

    rpi_core = RpiCore()
    rpi_core.start()
    rpi_core.stop()

    assert started
    assert stopped


def test_installed_controller_config_can_be_loaded_by_name() -> None:
    """Load a bundled controller config without relying on the current directory."""
    tone_configs = vibe_controller.get_tone_config_list("config_test_5_knocks.csv")

    assert tone_configs


def test_alsa_settings_are_discovered(monkeypatch: pytest.MonkeyPatch) -> None:
    """Select a playback card and common mixer control from ALSA command output."""
    command_output: dict[tuple[str, ...], str] = {
        ("aplay", "-l"): (
            "card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]\n"
            "card 1: DAC [USB Audio DAC], device 0: USB Audio DAC [USB Audio DAC]"
        ),
        ("amixer", "-c", "0", "scontrols"): "Simple mixer control 'Headphone',0",
        ("amixer", "-c", "1", "scontrols"): "Simple mixer control 'Master',0",
    }

    def run(command: list[str], **kwargs: object) -> object:
        class CompletedProcess:
            stdout = command_output[tuple(command)]

        return CompletedProcess()

    monkeypatch.setattr(vibe_controller.subprocess, "run", run)

    assert vibe_controller.discover_alsa_settings() == ("plughw:1,0", "Master")
