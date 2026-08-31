import pytest

from simulator.tachograph.simulator import (
    SimulatedTachograph,
    TachographError,
)


def test_tachograph_starts_disconnected():
    tachograph = SimulatedTachograph()

    assert tachograph.connected is False
    assert tachograph.authenticated is False


def test_tachograph_can_connect():
    tachograph = SimulatedTachograph()

    tachograph.connect()

    assert tachograph.connected is True


def test_tachograph_cannot_authenticate_without_connection():
    tachograph = SimulatedTachograph()

    with pytest.raises(TachographError):
        tachograph.authenticate()


def test_tachograph_can_authenticate_after_connect():
    tachograph = SimulatedTachograph()

    tachograph.connect()
    tachograph.authenticate()

    assert tachograph.authenticated is True


def test_tachograph_cannot_download_without_authentication():
    tachograph = SimulatedTachograph()

    tachograph.connect()

    with pytest.raises(TachographError):
        tachograph.download()


def test_tachograph_can_download_after_authentication():
    tachograph = SimulatedTachograph()

    tachograph.connect()
    tachograph.authenticate()

    data = tachograph.download()

    assert data == b"SIMULATED_TACHOGRAPH_DATA"


def test_tachograph_cannot_connect_twice():
    tachograph = SimulatedTachograph()

    tachograph.connect()

    with pytest.raises(TachographError):
        tachograph.connect()


def test_tachograph_disconnect_clears_session():
    tachograph = SimulatedTachograph()

    tachograph.connect()
    tachograph.authenticate()
    tachograph.disconnect()

    assert tachograph.connected is False
    assert tachograph.authenticated is False
    
    
def test_tachograph_has_identity():
    tachograph = SimulatedTachograph(
        tachograph_id="TACHO-123",
        vehicle_id="VEHICLE-456",
        vehicle_registration="9999-XYZ",
    )

    assert tachograph.tachograph_id == "TACHO-123"
    assert tachograph.vehicle_id == "VEHICLE-456"
    assert tachograph.vehicle_registration == "9999-XYZ"
    
    
def test_tachograph_identity_is_available_after_download():
    tachograph = SimulatedTachograph(
        tachograph_id="TACHO-123",
        vehicle_id="VEHICLE-456",
        vehicle_registration="9999-XYZ",
    )

    tachograph.connect()
    tachograph.authenticate()

    data = tachograph.download()

    assert data == b"SIMULATED_TACHOGRAPH_DATA"
    assert tachograph.tachograph_id == "TACHO-123"
    assert tachograph.vehicle_id == "VEHICLE-456"
    assert tachograph.vehicle_registration == "9999-XYZ"