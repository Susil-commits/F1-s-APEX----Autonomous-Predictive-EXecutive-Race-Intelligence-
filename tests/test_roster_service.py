"""Unit tests for APEX Dynamic Driver Roster Service."""
from core.data.roster_service import DriverRosterService, DriverProfile


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


def test_roster_service_sync_from_jolpica(tmp_path):
    """Verifies dynamic standings sync updates active lineup and constructor points share."""
    from unittest.mock import MagicMock, patch

    storage = str(tmp_path / "roster_sync.json")
    svc = DriverRosterService(persistence_file=storage)

    mock_driver_resp = MagicMock()
    mock_driver_resp.json.return_value = {
        "MRData": {
            "StandingsTable": {
                "StandingsLists": [
                    {
                        "DriverStandings": [
                            {
                                "position": "1",
                                "Driver": {"code": "ANT", "givenName": "Andrea Kimi", "familyName": "Antonelli", "permanentNumber": "12"},
                                "Constructors": [{"name": "Mercedes"}],
                            },
                            {
                                "position": "2",
                                "Driver": {"code": "NOR", "givenName": "Lando", "familyName": "Norris", "permanentNumber": "4"},
                                "Constructors": [{"name": "McLaren"}],
                            },
                        ]
                    }
                ]
            }
        }
    }
    mock_constructor_resp = MagicMock()
    mock_constructor_resp.json.return_value = {
        "MRData": {
            "StandingsTable": {
                "StandingsLists": [
                    {
                        "ConstructorStandings": [
                            {"Constructor": {"name": "Mercedes"}, "points": "600"},
                            {"Constructor": {"name": "McLaren"}, "points": "400"},
                        ]
                    }
                ]
            }
        }
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.side_effect = [mock_driver_resp, mock_constructor_resp]

    with patch("httpx.Client", return_value=mock_client):
        res = svc.sync_from_jolpica(year=2026)

    assert res["year"] == 2026
    assert res["synced_drivers"] == 2
    ant = svc.get_driver("ANT")
    assert ant is not None
    assert ant["pts_share"] == 0.5  # clamped from 0.60
    assert ant["default_grid"] == 1
    ric = svc.get_driver("RIC")
    assert ric is not None and ric["is_active"] is False
