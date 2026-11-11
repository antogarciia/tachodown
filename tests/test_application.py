from datetime import date

from simulator.application import TachographApplication
from simulator.card.driver_card import DriverCard
from simulator.metadata.models import (
    OperationStatus,
    OperationType,
    SyncStatus,
)


def create_card():
    return DriverCard(
        card_number="APP-CARD-001",
        driver_id="APP-DRIVER-001",
        issuing_country="ES",
        valid_from=date(2026, 1, 1),
        valid_until=date(2030, 12, 31),
    )


def test_application_can_download_driver_card(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
    )

    card = create_card()

    operation = app.download_card(card)

    assert operation.status == OperationStatus.COMPLETED
    assert operation.file_id is not None
    assert operation.sync_status == SyncStatus.SYNCED


def test_application_creates_ddd_file(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
    )

    operation = app.download_card(
        create_card()
    )

    assert operation.status == OperationStatus.COMPLETED

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 1

    assert files[0].read_bytes() == (
        b"SIMULATED_DRIVER_CARD_DATA"
    )


def test_application_can_work_offline(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=False,
    )

    operation = app.download_card(
        create_card()
    )

    assert operation.status == OperationStatus.COMPLETED
    assert operation.sync_status == SyncStatus.LOCAL_ONLY
    assert operation.file_id is not None


def test_application_exposes_device_state(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
    )

    assert app.device.state.value == "IDLE"

    app.download_card(create_card())

    assert app.device.state.value == "IDLE"


def test_application_exposes_server(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
    )

    assert app.server.online is True


def test_application_exposes_operation_log(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
    )

    operation = app.download_card(
        create_card()
    )

    operations = app.operation_log.all()

    assert len(operations) >= 1

    assert any(
        item["operation_id"] == operation.operation_id
        for item in operations
    )


def test_application_can_sync_pending_files_after_server_returns_online(
    tmp_path,
):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=False,
    )

    operation = app.download_card(create_card())

    assert operation.status == OperationStatus.COMPLETED
    assert operation.sync_status == SyncStatus.LOCAL_ONLY

    assert app.server.get_file(operation.file_id) is None

    app.server.online = True

    results = app.sync_pending()

    assert len(results) == 1
    assert results[0].file_id == operation.file_id
    assert results[0].sync_status == SyncStatus.SYNCED

    uploaded = app.server.get_file(operation.file_id)

    assert uploaded is not None


def test_application_sync_pending_preserves_original_file(
    tmp_path,
):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=False,
    )

    operation = app.download_card(create_card())

    saved_file = next(tmp_path.glob("*.DDD"))
    original_data = saved_file.read_bytes()

    assert operation.file_id is not None

    app.server.online = True

    app.sync_pending()

    assert saved_file.read_bytes() == original_data


def test_application_sync_pending_does_nothing_when_nothing_is_pending(
    tmp_path,
):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=True,
    )

    results = app.sync_pending()

    assert results == []


def test_application_sync_pending_records_new_sync_operation(
    tmp_path,
):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=False,
    )

    operation = app.download_card(create_card())

    app.server.online = True

    results = app.sync_pending()

    assert len(results) == 1

    sync_operation = results[0]

    assert sync_operation.operation_type == OperationType.SYNC
    assert sync_operation.status == OperationStatus.COMPLETED
    assert sync_operation.sync_status == SyncStatus.SYNCED
    assert sync_operation.file_id == operation.file_id

    operations = app.operation_log.all()

    sync_operations = [
        item
        for item in operations
        if item["operation_type"] == "SYNC"
    ]

    assert len(sync_operations) == 2