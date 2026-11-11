from datetime import date

from simulator.application import TachographApplication
from simulator.card.driver_card import DriverCard
from simulator.metadata.models import (
    OperationStatus,
    OperationType,
    SyncStatus,
)


def create_card(
    card_number: str = "CARD-001",
) -> DriverCard:
    return DriverCard(
        card_number=card_number,
        driver_id="DRIVER-001",
        issuing_country="ES",
        valid_from=date(2025, 1, 1),
        valid_until=date(2030, 12, 31),
    )


def test_complete_card_flow_download_verify_and_sync(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=True,
    )

    operation = app.download_card(
        create_card()
    )

    assert operation.status == OperationStatus.COMPLETED
    assert operation.file_id is not None

    metadata = app.file_service.get_file(
        operation.file_id
    )

    assert metadata is not None
    assert metadata.filename.endswith(".DDD")
    assert metadata.source_type.value == "DRIVER_CARD"

    assert app.file_service.verify_file(
        operation.file_id
    ) is True

    uploaded = app.server.get_file(
        operation.file_id
    )

    assert uploaded is not None
    assert uploaded.file_id == operation.file_id


def test_card_download_server_offline_then_sync(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=False,
    )

    operation = app.download_card(
        create_card()
    )

    assert operation.status == OperationStatus.COMPLETED
    assert operation.file_id is not None
    assert operation.sync_status == SyncStatus.LOCAL_ONLY

    metadata = app.file_service.get_file(
        operation.file_id
    )

    assert metadata is not None

    assert app.server.get_file(
        operation.file_id
    ) is None

    app.server.online = True

    results = app.sync_pending()

    assert results

    uploaded = app.server.get_file(
        operation.file_id
    )

    assert uploaded is not None
    assert uploaded.file_id == operation.file_id


def test_tachograph_complete_flow(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=True,
    )

    app.tachograph.connect()
    app.tachograph.authenticate()

    operation = app.download_tachograph()

    app.tachograph.disconnect()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.file_id is not None
    assert operation.operation_type == OperationType.TACHOGRAPH_DOWNLOAD

    metadata = app.file_service.get_file(
        operation.file_id
    )

    assert metadata is not None
    assert metadata.filename.endswith(".DDD")
    assert metadata.source_type.value == "TACHOGRAPH"

    assert app.file_service.verify_file(
        operation.file_id
    ) is True


def test_modified_file_fails_integrity_check(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=True,
    )

    operation = app.download_card(
        create_card()
    )

    assert operation.status == OperationStatus.COMPLETED
    assert operation.file_id is not None

    metadata = app.file_service.get_file(
        operation.file_id
    )

    assert metadata is not None

    path = tmp_path / metadata.filename

    path.write_bytes(
        b"MODIFIED_DATA"
    )

    assert app.file_service.verify_file(
        operation.file_id
    ) is False


def test_deleted_file_fails_integrity_check(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=True,
    )

    operation = app.download_card(
        create_card()
    )

    assert operation.status == OperationStatus.COMPLETED
    assert operation.file_id is not None

    metadata = app.file_service.get_file(
        operation.file_id
    )

    assert metadata is not None

    path = tmp_path / metadata.filename

    path.unlink()

    assert app.file_service.verify_file(
        operation.file_id
    ) is False


def test_multiple_downloads_are_recorded(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=True,
    )

    first = app.download_card(
        create_card("CARD-001")
    )

    assert first.status == OperationStatus.COMPLETED

    app.reader.remove_card()

    second = app.download_card(
        create_card("CARD-002")
    )

    assert second.status == OperationStatus.COMPLETED

    assert first.file_id is not None
    assert second.file_id is not None

    assert first.file_id != second.file_id

    files = app.storage.list_metadata()

    assert len(files) == 2

    operations = app.operation_log.all()

    card_operations = [
        operation
        for operation in operations
        if operation.get("operation_type") == "CARD_DOWNLOAD"
    ]

    assert len(card_operations) == 2


def test_sync_retry_after_server_recovery(tmp_path):
    app = TachographApplication(
        storage_path=tmp_path,
        server_online=False,
    )

    operation = app.download_card(
        create_card()
    )

    assert operation.status == OperationStatus.COMPLETED
    assert operation.file_id is not None
    assert operation.sync_status == SyncStatus.LOCAL_ONLY

    assert app.server.get_file(
        operation.file_id
    ) is None

    app.server.online = True

    results = app.sync_pending()

    assert results

    uploaded = app.server.get_file(
        operation.file_id
    )

    assert uploaded is not None

    metadata = app.file_service.get_file(
        operation.file_id
    )

    assert metadata is not None

    assert uploaded.sha256 == metadata.sha256