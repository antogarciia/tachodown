from datetime import date

from simulator.card.driver_card import DriverCard
from simulator.card.reader import CardReader
from simulator.download.card_download import CardDownloadService
from simulator.metadata.models import (
    OperationStatus,
    OperationType,
    SourceType,
    SyncStatus,
)
from simulator.server.simulator import SimulatedServer
from simulator.storage.local_storage import LocalStorage
from simulator.sync.service import SyncService
from simulator.operations.log import OperationLog


def create_valid_card():
    return DriverCard(
        card_number="TEST-CARD-001",
        driver_id="DRIVER-001",
        issuing_country="ES",
        valid_from=date(2026, 1, 1),
        valid_until=date(2030, 12, 31),
    )


def test_card_download_saves_ddd_and_creates_metadata(tmp_path):
    card = create_valid_card()

    reader = CardReader()
    reader.insert_card(card)

    storage = LocalStorage(tmp_path)
    service = CardDownloadService(reader, storage)

    operation = service.download()

    assert operation.operation_type == OperationType.CARD_DOWNLOAD
    assert operation.status == OperationStatus.COMPLETED
    assert operation.source_type == SourceType.DRIVER_CARD
    assert operation.card_number == "TEST-CARD-001"
    assert operation.driver_id == "DRIVER-001"
    assert operation.file_id is not None
    assert operation.sync_status == SyncStatus.LOCAL_ONLY

    files = list(tmp_path.glob("*.DDD"))
    assert len(files) == 1


def test_card_download_preserves_original_data(tmp_path):
    card = create_valid_card()

    reader = CardReader()
    reader.insert_card(card)

    storage = LocalStorage(tmp_path)
    service = CardDownloadService(reader, storage)

    operation = service.download()

    saved_file = next(tmp_path.glob("*.DDD"))

    assert saved_file.read_bytes() == b"SIMULATED_DRIVER_CARD_DATA"
    assert operation.file_id is not None


def test_card_download_requires_inserted_card(tmp_path):
    reader = CardReader()
    storage = LocalStorage(tmp_path)
    service = CardDownloadService(reader, storage)

    operation = service.download()

    assert operation.operation_type == OperationType.CARD_DOWNLOAD
    assert operation.status == OperationStatus.FAILED
    assert operation.source_type == SourceType.DRIVER_CARD
    assert operation.file_id is None
    assert operation.sync_status is None
    assert operation.error_message is not None


def test_two_card_downloads_create_different_files(tmp_path):
    card = create_valid_card()

    reader = CardReader()
    reader.insert_card(card)

    storage = LocalStorage(tmp_path)
    service = CardDownloadService(reader, storage)

    first = service.download()
    second = service.download()

    assert first.status == OperationStatus.COMPLETED
    assert second.status == OperationStatus.COMPLETED

    assert first.file_id != second.file_id

    files = list(tmp_path.glob("*.DDD"))
    assert len(files) == 2

    assert files[0].read_bytes() == b"SIMULATED_DRIVER_CARD_DATA"
    assert files[1].read_bytes() == b"SIMULATED_DRIVER_CARD_DATA"



def test_card_download_syncs_when_server_is_online(tmp_path):
    card = create_valid_card()

    reader = CardReader()
    reader.insert_card(card)

    storage = LocalStorage(tmp_path)
    server = SimulatedServer()
    sync_service = SyncService(server)

    service = CardDownloadService(
        reader,
        storage,
        sync_service,
    )

    operation = service.download()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.sync_status == SyncStatus.SYNCED
    assert operation.file_id is not None

    uploaded = server.get_file(operation.file_id)

    assert uploaded is not None
    assert uploaded.data == b"SIMULATED_DRIVER_CARD_DATA"


def test_card_download_stays_local_when_server_is_offline(tmp_path):
    card = create_valid_card()

    reader = CardReader()
    reader.insert_card(card)

    storage = LocalStorage(tmp_path)
    server = SimulatedServer()
    server.online = False

    sync_service = SyncService(server)

    service = CardDownloadService(
        reader,
        storage,
        sync_service,
    )

    operation = service.download()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.sync_status == SyncStatus.LOCAL_ONLY
    assert operation.file_id is not None

    assert server.get_file(operation.file_id) is None

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 1
    assert files[0].read_bytes() == b"SIMULATED_DRIVER_CARD_DATA"

def test_card_download_records_operation(tmp_path):
    card = create_valid_card()

    reader = CardReader()
    reader.insert_card(card)

    storage = LocalStorage(tmp_path)

    operation_log = OperationLog(
        tmp_path / "operations.json"
    )

    service = CardDownloadService(
        reader,
        storage,
        operation_log=operation_log,
    )

    operation = service.download()

    operations = operation_log.all()

    assert len(operations) == 1

    saved = operations[0]

    assert saved["operation_id"] == operation.operation_id
    assert saved["operation_type"] == "CARD_DOWNLOAD"
    assert saved["status"] == "COMPLETED"
    assert saved["card_number"] == card.card_number
    assert saved["driver_id"] == card.driver_id
    assert saved["file_id"] == operation.file_id


def test_failed_card_download_is_recorded(tmp_path):
    reader = CardReader()

    storage = LocalStorage(tmp_path)

    operation_log = OperationLog(
        tmp_path / "operations.json"
    )

    service = CardDownloadService(
        reader,
        storage,
        operation_log=operation_log,
    )

    operation = service.download()

    assert operation.status == OperationStatus.FAILED

    operations = operation_log.all()

    assert len(operations) == 1
    assert operations[0]["operation_id"] == operation.operation_id
    assert operations[0]["status"] == "FAILED"
    assert operations[0]["error_message"] == (
        "No hay ninguna tarjeta insertada"
    )

