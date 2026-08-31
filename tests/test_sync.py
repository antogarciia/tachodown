import hashlib

from simulator.metadata.models import SourceType, SyncStatus
from simulator.server.simulator import SimulatedServer
from simulator.storage.local_storage import LocalStorage
from simulator.sync.service import SyncService


def test_sync_uploads_local_file(tmp_path):
    storage = LocalStorage(tmp_path)
    server = SimulatedServer()
    service = SyncService(server)

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="TEST.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    status = service.sync_file(metadata)

    assert status == SyncStatus.SYNCED

    uploaded = server.get_file(metadata.file_id)

    assert uploaded is not None
    assert uploaded.data == b"ORIGINAL_DDD_DATA"


def test_sync_preserves_original_bytes(tmp_path):
    storage = LocalStorage(tmp_path)
    server = SimulatedServer()
    service = SyncService(server)

    data = b"ORIGINAL_DDD_DATA"

    metadata = storage.save(
        data=data,
        filename="TEST.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    service.sync_file(metadata)

    uploaded = server.get_file(metadata.file_id)

    assert uploaded is not None
    assert uploaded.data == data
    assert hashlib.sha256(uploaded.data).hexdigest() == metadata.sha256


def test_sync_stays_local_when_server_is_offline(tmp_path):
    storage = LocalStorage(tmp_path)
    server = SimulatedServer()
    server.online = False

    service = SyncService(server)

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="TEST.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    status = service.sync_file(metadata)

    assert status == SyncStatus.LOCAL_ONLY
    assert server.get_file(metadata.file_id) is None


def test_sync_rejects_modified_local_file(tmp_path):
    storage = LocalStorage(tmp_path)
    server = SimulatedServer()
    service = SyncService(server)

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="TEST.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    path = tmp_path / "TEST.DDD"
    path.write_bytes(b"MODIFIED_DDD_DATA")

    status = service.sync_file(metadata)

    assert status == SyncStatus.LOCAL_ONLY
    assert server.get_file(metadata.file_id) is None


def test_sync_can_retry_after_server_returns_online(tmp_path):
    storage = LocalStorage(tmp_path)
    server = SimulatedServer()
    service = SyncService(server)

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="TEST.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    server.online = False

    first_status = service.sync_file(metadata)

    assert first_status == SyncStatus.LOCAL_ONLY

    server.online = True

    second_status = service.sync_file(metadata)

    assert second_status == SyncStatus.SYNCED
    assert server.get_file(metadata.file_id) is not None
    
    
from simulator.operations.log import OperationLog
from simulator.metadata.models import (
    OperationStatus,
    OperationType,
)


def test_sync_records_completed_operation(tmp_path):
    storage = LocalStorage(tmp_path)
    server = SimulatedServer()

    operation_log = OperationLog(
        tmp_path / "operations.json"
    )

    service = SyncService(
        server,
        operation_log,
    )

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="TEST.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    status = service.sync_file(metadata)

    assert status == SyncStatus.SYNCED

    operations = operation_log.all()

    assert len(operations) == 1

    operation = operations[0]

    assert operation["operation_type"] == "SYNC"
    assert operation["status"] == "COMPLETED"
    assert operation["source_type"] == "DRIVER_CARD"
    assert operation["file_id"] == metadata.file_id
    assert operation["sync_status"] == "SYNCED"
    assert operation["error_message"] is None


def test_sync_records_failed_operation_when_server_offline(
    tmp_path,
):
    storage = LocalStorage(tmp_path)
    server = SimulatedServer()
    server.online = False

    operation_log = OperationLog(
        tmp_path / "operations.json"
    )

    service = SyncService(
        server,
        operation_log,
    )

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="TEST.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    status = service.sync_file(metadata)

    assert status == SyncStatus.LOCAL_ONLY

    operations = operation_log.all()

    assert len(operations) == 1

    operation = operations[0]

    assert operation["operation_type"] == "SYNC"
    assert operation["status"] == "FAILED"
    assert operation["source_type"] == "DRIVER_CARD"
    assert operation["file_id"] == metadata.file_id
    assert operation["sync_status"] == "LOCAL_ONLY"
    assert operation["error_message"] == (
        "Servidor no disponible"
    )


def test_sync_records_modified_file_failure(tmp_path):
    storage = LocalStorage(tmp_path)
    server = SimulatedServer()

    operation_log = OperationLog(
        tmp_path / "operations.json"
    )

    service = SyncService(
        server,
        operation_log,
    )

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="TEST.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    path = tmp_path / "TEST.DDD"
    path.write_bytes(b"MODIFIED_DDD_DATA")

    status = service.sync_file(metadata)

    assert status == SyncStatus.LOCAL_ONLY

    operations = operation_log.all()

    assert len(operations) == 1

    operation = operations[0]

    assert operation["operation_type"] == "SYNC"
    assert operation["status"] == "FAILED"
    assert operation["file_id"] == metadata.file_id
    assert operation["sync_status"] == "LOCAL_ONLY"
    assert operation["error_message"] == (
        "El archivo local ha sido modificado"
    )