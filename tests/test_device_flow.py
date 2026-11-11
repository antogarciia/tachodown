from datetime import date

from simulator.card.driver_card import DriverCard
from simulator.card.reader import CardReader
from simulator.device.controller import (
    DeviceController,
    DeviceState,
)
from simulator.download.card_download import CardDownloadService
from simulator.metadata.models import (
    OperationStatus,
    SyncStatus,
)
from simulator.operations.log import OperationLog
from simulator.server.simulator import SimulatedServer
from simulator.storage.local_storage import LocalStorage
from simulator.sync.service import SyncService


def create_valid_card():
    return DriverCard(
        card_number="FLOW-CARD-001",
        driver_id="FLOW-DRIVER-001",
        issuing_country="ES",
        valid_from=date(2026, 1, 1),
        valid_until=date(2030, 12, 31),
    )


def create_device(tmp_path, server_online=True):
    card = create_valid_card()

    reader = CardReader()
    reader.insert_card(card)

    storage = LocalStorage(tmp_path)

    server = SimulatedServer()
    server.online = server_online

    operation_log = OperationLog(
        tmp_path / "operations.json"
    )

    sync_service = SyncService(
        server,
        operation_log,
    )

    download_service = CardDownloadService(
        reader,
        storage,
        sync_service,
        operation_log,
    )

    device = DeviceController(
        reader=reader,
        download_service=download_service,
    )

    return device, reader, server, operation_log


def test_complete_device_flow_syncs_file(tmp_path):
    device, reader, server, operation_log = create_device(
        tmp_path,
        server_online=True,
    )

    device.detect_card()

    assert device.state == DeviceState.CARD_DETECTED
    assert device.card is not None

    operation = device.download_card()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.sync_status == SyncStatus.SYNCED

    assert device.state == DeviceState.IDLE
    assert device.card is not None

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 1

    uploaded = server.get_file(operation.file_id)

    assert uploaded is not None
    assert uploaded.data == files[0].read_bytes()

    operations = operation_log.all()

    assert len(operations) == 2

    assert operations[0]["operation_type"] == "SYNC"
    assert operations[0]["status"] == "COMPLETED"

    assert operations[1]["operation_type"] == "CARD_DOWNLOAD"
    assert operations[1]["status"] == "COMPLETED"


def test_complete_device_flow_stays_local_when_server_offline(
    tmp_path,
):
    device, reader, server, operation_log = create_device(
        tmp_path,
        server_online=False,
    )

    device.detect_card()

    operation = device.download_card()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.sync_status == SyncStatus.LOCAL_ONLY

    assert device.state == DeviceState.SYNC_PENDING

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 1

    assert files[0].read_bytes() == (
        b"SIMULATED_DRIVER_CARD_DATA"
    )

    assert server.get_file(operation.file_id) is None


def test_device_reset_clears_card_after_successful_sync(
    tmp_path,
):
    device, reader, server, operation_log = create_device(
        tmp_path,
        server_online=True,
    )

    device.detect_card()

    operation = device.download_card()

    assert operation.status == OperationStatus.COMPLETED
    assert device.state == DeviceState.IDLE

    device.reset()

    assert device.state == DeviceState.IDLE
    assert device.card is None
    assert device.last_operation is None


def test_device_can_download_again_after_reset(tmp_path):
    device, reader, server, operation_log = create_device(
        tmp_path,
        server_online=True,
    )

    device.detect_card()

    first = device.download_card()

    assert first.status == OperationStatus.COMPLETED
    assert device.state == DeviceState.IDLE

    device.reset()

    reader.insert_card(create_valid_card())

    device.detect_card()

    second = device.download_card()

    assert second.status == OperationStatus.COMPLETED
    assert second.file_id != first.file_id

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 2


def test_device_download_failure_enters_error_state(tmp_path):
    device, reader, server, operation_log = create_device(
        tmp_path,
        server_online=True,
    )

    device.detect_card()

    # Quitamos la tarjeta después de detectarla para provocar
    # un fallo real durante la descarga.
    reader.remove_card()

    operation = device.download_card()

    assert operation.status == OperationStatus.FAILED
    assert device.state == DeviceState.ERROR

    assert operation.file_id is None

    files = list(tmp_path.glob("*.DDD"))

    assert files == []


def test_device_can_recover_from_download_error(tmp_path):
    device, reader, server, operation_log = create_device(
        tmp_path,
        server_online=True,
    )

    device.detect_card()

    reader.remove_card()

    operation = device.download_card()

    assert operation.status == OperationStatus.FAILED
    assert device.state == DeviceState.ERROR

    device.reset()

    assert device.state == DeviceState.IDLE
    assert device.card is None
    assert device.last_operation is None


def test_device_download_requires_detected_card(tmp_path):
    device, reader, server, operation_log = create_device(
        tmp_path,
        server_online=True,
    )

    try:
        device.download_card()
    except Exception:
        pass
    else:
        raise AssertionError(
            "Se esperaba una excepción"
        )

    assert device.state == DeviceState.IDLE


def test_device_detects_card_from_reader(tmp_path):
    device, reader, server, operation_log = create_device(
        tmp_path,
        server_online=True,
    )

    assert device.card is None

    device.detect_card()

    assert device.state == DeviceState.CARD_DETECTED
    assert device.card is reader.read_card()