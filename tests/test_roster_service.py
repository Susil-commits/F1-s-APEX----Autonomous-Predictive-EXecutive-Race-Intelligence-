"""Unit tests for APEX Dynamic Driver Roster Service."""
import pytest
from core.data.roster_service import DriverRosterService, DriverProfile, DEFAULT_DRIVER_ROSTER


def test_roster_service_initialization(tmp_path):
    storage = str(tmp_path / "roster_test.json")
    svc = DriverRosterService(persistence_file=storage)
    drivers = svc.get_all_drivers(active_only=True)
    assert len(drivers) >= 20
    assert any(d["code"] == "VER" for d in drivers)
    assert any(d["code"] == "NOR" for d in drivers)


def test_roster_service_get_driver(tmp_path):
    storage = str(tmp_path / "roster_test.json")
    svc = DriverRosterService(persistence_file=storage)
    ver = svc.get_driver("ver")  # Case insensitive
    assert ver is not None
    assert ver["name"] == "Max Verstappen"
    assert ver["number"] == 1


def test_roster_service_update_profile(tmp_path):
    storage = str(tmp_path / "roster_test.json")
    svc = DriverRosterService(persistence_file=storage)
    new_profile = DriverProfile(
        code="ROO",
        name="Rookie Driver",
        first_name="Rookie",
        last_name="DRIVER",
        team="Apex Racing",
        number=99,
        color="#00FFCC",
        country="🇬🇧",
        default_grid=5,
        photo="/f1/drivers/ROO.webp",
        pts_share=0.15,
        rolling_avg=4.5,
        starts=2,
        is_active=True,
    )
    svc.update_driver(new_profile)

    fetched = svc.get_driver("ROO")
    assert fetched is not None
    assert fetched["name"] == "Rookie Driver"
    assert fetched["team"] == "Apex Racing"

    # Reload from disk to verify persistence
    svc_reloaded = DriverRosterService(persistence_file=storage)
    assert svc_reloaded.get_driver("ROO") is not None
