from simulator.application import TachographApplication
from simulator.metadata.models import (
    OperationStatus,
    OperationType,
    SourceType,
    SyncStatus,
)
from simulator.tachograph.simulator import SimulatedTachograph


def create_tachograph():
    tachograph = SimulatedTachograph()

    tachograph.connect()
    tachograph.authenticate()

    return tachograph


def test_application_can_download_tachograph(tmp_path):
    tachograph = create_tachograph()

    app = TachographApplication(
        storage_path=tmp_path,
        tachograph=tachograph,
    )

    operation = app.download_tachograph()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.operation_type == OperationType.TACHOGRAPH_DOWNLOAD
    assert operation.source_type == SourceType.TACHOGRAPH
    assert operation.file_id is not None
    assert operation.sync_status == SyncStatus.SYNCED


def test_application_creates_tachograph_ddd_file(tmp_path):
    tachograph = create_tachograph()

    app = TachographApplication(
        storage_path=tmp_path,
        tachograph=tachograph,
    )

    operation = app.download_tachograph()

    assert operation.status == OperationStatus.COMPLETED

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 1
    assert files[0].read_bytes() == (
        b"SIMULATED_TACHOGRAPH_DATA"
    )


def test_application_can_download_tachograph_offline(
    tmp_path,
):
    tachograph = create_tachograph()

    app = TachographApplication(
        storage_path=tmp_path,
        tachograph=tachograph,
        server_online=False,
    )

    operation = app.download_tachograph()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.sync_status == SyncStatus.LOCAL_ONLY
    assert operation.file_id is not None


def test_application_exposes_tachograph(tmp_path):
    tachograph = create_tachograph()

    app = TachographApplication(
        storage_path=tmp_path,
        tachograph=tachograph,
    )

    assert app.tachograph is tachograph


def test_application_tachograph_download_records_operation(
    tmp_path,
):
    tachograph = create_tachograph()

    app = TachographApplication(
        storage_path=tmp_path,
        tachograph=tachograph,
    )

    operation = app.download_tachograph()

    operations = app.operation_log.all()

    tachograph_operations = [
        item
        for item in operations
        if item["operation_type"]
        == OperationType.TACHOGRAPH_DOWNLOAD.value
    ]

    assert len(tachograph_operations) == 1

    assert any(
        item["operation_id"] == operation.operation_id
        for item in tachograph_operations
    )


def test_application_tachograph_preserves_identity(
    tmp_path,
):
    tachograph = SimulatedTachograph(
        tachograph_id="TACHO-APP-123",
        vehicle_id="VEHICLE-APP-456",
        vehicle_registration="7777-APP",
    )

    tachograph.connect()
    tachograph.authenticate()

    app = TachographApplication(
        storage_path=tmp_path,
        tachograph=tachograph,
    )

    operation = app.download_tachograph()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.tachograph_id == "TACHO-APP-123"
    assert operation.vehicle_id == "VEHICLE-APP-456"
    assert operation.vehicle_registration == "7777-APP"