import pytest
from expidite_rpi import RpiCore
from expidite_rpi.core.edge_orchestrator import EdgeOrchestrator

from VibeRig.configs.fleet_config_lab import INVENTORY


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

    monkeypatch.setattr(EdgeOrchestrator, "start_all_with_watchdog", start_orchestrator)
    monkeypatch.setattr(EdgeOrchestrator, "get_instance", lambda: OrchestratorStub())

    rpi_core = RpiCore()
    rpi_core.start()
    rpi_core.stop()

    assert started
    assert stopped
