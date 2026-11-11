from simulator.device.controller import (
    DeviceController,
    DeviceState,
    InvalidTransition,
)


def test_device_starts_in_idle():
    device = DeviceController()

    assert device.state == DeviceState.IDLE
    assert device.card is None


def test_device_can_detect_card():
    device = DeviceController()

    card = object()

    device.detect_card(card)

    assert device.state == DeviceState.CARD_DETECTED
    assert device.card is card


def test_device_can_complete_full_state_flow():
    device = DeviceController()

    device.detect_card(object())

    device.transition_to(DeviceState.AUTHENTICATING)
    device.transition_to(DeviceState.DOWNLOADING)
    device.transition_to(DeviceState.VERIFYING)
    device.transition_to(DeviceState.STORED_LOCAL)
    device.transition_to(DeviceState.SYNC_PENDING)
    device.transition_to(DeviceState.SYNCED)

    assert device.state == DeviceState.SYNCED


def test_device_can_return_to_idle_after_sync():
    device = DeviceController()

    device.detect_card(object())

    device.transition_to(DeviceState.AUTHENTICATING)
    device.transition_to(DeviceState.DOWNLOADING)
    device.transition_to(DeviceState.VERIFYING)
    device.transition_to(DeviceState.STORED_LOCAL)
    device.transition_to(DeviceState.SYNC_PENDING)
    device.transition_to(DeviceState.SYNCED)
    device.transition_to(DeviceState.IDLE)

    assert device.state == DeviceState.IDLE


def test_device_can_enter_error_from_card_detected():
    device = DeviceController()

    device.detect_card(object())
    device.transition_to(DeviceState.ERROR)

    assert device.state == DeviceState.ERROR


def test_device_can_recover_from_error():
    device = DeviceController()

    device.detect_card(object())
    device.transition_to(DeviceState.ERROR)
    device.transition_to(DeviceState.IDLE)

    assert device.state == DeviceState.IDLE


def test_invalid_transition_is_rejected():
    device = DeviceController()

    try:
        device.transition_to(DeviceState.SYNCED)
    except InvalidTransition:
        pass
    else:
        raise AssertionError("Se esperaba InvalidTransition")


def test_device_cannot_detect_second_card():
    device = DeviceController()

    first_card = object()
    second_card = object()

    device.detect_card(first_card)

    try:
        device.detect_card(second_card)
    except InvalidTransition:
        pass
    else:
        raise AssertionError("Se esperaba InvalidTransition")

    assert device.card is first_card
    assert device.state == DeviceState.CARD_DETECTED


def test_device_cannot_skip_required_states():
    device = DeviceController()

    device.detect_card(object())

    try:
        device.transition_to(DeviceState.DOWNLOADING)
    except InvalidTransition:
        pass
    else:
        raise AssertionError("Se esperaba InvalidTransition")

    assert device.state == DeviceState.CARD_DETECTED


from datetime import date

from simulator.card.driver_card import DriverCard
from simulator.card.reader import CardReader
from simulator.download.card_download import CardDownloadService
from simulator.metadata.models import (
    OperationStatus,
    SyncStatus,
)
from simulator.server.simulator import SimulatedServer
from simulator.storage.local_storage import LocalStorage
from simulator.sync.service import SyncService


def create_valid_card():
    return DriverCard(
        card_number="TEST-CARD-001",
        driver_id="DRIVER-001",
        issuing_country="ES",
        valid_from=date(2026, 1, 1),
        valid_until=date(2030, 12, 31),
    )


def create_device(
    tmp_path,
    server_online=True,
):
    card = create_valid_card()

    reader = CardReader()
    reader.insert_card(card)

    storage = LocalStorage(tmp_path)

    server = SimulatedServer()
    server.online = server_online

    sync_service = SyncService(server)

    download_service = CardDownloadService(
        reader,
        storage,
        sync_service,
    )

    device = DeviceController(
        reader=reader,
        download_service=download_service,
    )

    return device, server


def test_device_controller_downloads_card_successfully(
    tmp_path,
):
    device, server = create_device(tmp_path)

    device.detect_card()

    operation = device.download_card()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.sync_status == SyncStatus.SYNCED
    assert operation.file_id is not None

    assert device.state == DeviceState.IDLE
    assert device.card is not None

    uploaded = server.get_file(operation.file_id)

    assert uploaded is not None
    assert uploaded.data == (
        b"SIMULATED_DRIVER_CARD_DATA"
    )


def test_device_controller_keeps_file_pending_when_server_offline(
    tmp_path,
):
    device, server = create_device(
        tmp_path,
        server_online=False,
    )

    device.detect_card()

    operation = device.download_card()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.sync_status == SyncStatus.LOCAL_ONLY
    assert operation.file_id is not None

    assert server.get_file(operation.file_id) is None

    assert device.state == DeviceState.SYNC_PENDING


def test_device_controller_records_last_operation(
    tmp_path,
):
    device, _ = create_device(tmp_path)

    device.detect_card()

    operation = device.download_card()

    assert device.last_operation is operation


def test_device_controller_requires_card_before_download(
    tmp_path,
):
    device, _ = create_device(tmp_path)

    try:
        device.download_card()
    except InvalidTransition:
        pass
    else:
        raise AssertionError(
            "Se esperaba InvalidTransition"
        )


def test_device_controller_enters_error_when_download_fails(
    tmp_path,
):
    reader = CardReader()

    storage = LocalStorage(tmp_path)

    class FailingDownloadService:
        def download(self):
            return type(
                "FailedOperation",
                (),
                {
                    "status": OperationStatus.FAILED,
                    "sync_status": None,
                },
            )()

    service = FailingDownloadService()

    device = DeviceController(
        reader=reader,
        download_service=service,
    )

    device.detect_card(object())

    operation = device.download_card()

    assert operation.status == OperationStatus.FAILED
    assert device.state == DeviceState.ERROR


def test_device_controller_can_recover_after_download_failure(
    tmp_path,
):
    class FailingDownloadService:
        def download(self):
            return type(
                "FailedOperation",
                (),
                {
                    "status": OperationStatus.FAILED,
                    "sync_status": None,
                },
            )()

    device = DeviceController(
        download_service=FailingDownloadService(),
    )

    device.detect_card(object())

    operation = device.download_card()

    assert operation.status == OperationStatus.FAILED
    assert device.state == DeviceState.ERROR

    device.reset()

    assert device.state == DeviceState.IDLE
    assert device.card is None
    assert device.last_operation is None