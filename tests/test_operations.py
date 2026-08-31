from datetime import datetime, timezone

from simulator.metadata.models import (
    Operation,
    OperationStatus,
    OperationType,
    SourceType,
    SyncStatus,
)
from simulator.operations.log import OperationLog


def create_operation(
    operation_id="OP-000001",
    card_number="TEST-CARD-001",
    driver_id="DRIVER-001",
    file_id="FILE-000001",
):
    return Operation(
        operation_id=operation_id,
        operation_type=OperationType.CARD_DOWNLOAD,
        timestamp=datetime.now(timezone.utc),
        source_type=SourceType.DRIVER_CARD,
        status=OperationStatus.COMPLETED,
        card_number=card_number,
        driver_id=driver_id,
        driver_name="Juan García",
        file_id=file_id,
        sync_status=SyncStatus.SYNCED,
    )


def test_operation_log_starts_empty(tmp_path):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    assert log.all() == []


def test_operation_log_can_append_operation(tmp_path):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    operation = create_operation()

    log.append(operation)

    operations = log.all()

    assert len(operations) == 1
    assert operations[0]["operation_id"] == "OP-000001"
    assert operations[0]["card_number"] == "TEST-CARD-001"
    assert operations[0]["driver_id"] == "DRIVER-001"
    assert operations[0]["file_id"] == "FILE-000001"


def test_operation_log_preserves_enum_values(tmp_path):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    operation = create_operation()

    log.append(operation)

    saved = log.all()[0]

    assert saved["operation_type"] == "CARD_DOWNLOAD"
    assert saved["status"] == "COMPLETED"
    assert saved["source_type"] == "DRIVER_CARD"
    assert saved["sync_status"] == "SYNCED"


def test_operation_log_can_find_by_file_id(tmp_path):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    log.append(
        create_operation(
            operation_id="OP-001",
            file_id="FILE-001",
        )
    )

    log.append(
        create_operation(
            operation_id="OP-002",
            file_id="FILE-002",
        )
    )

    results = log.find_by_file_id("FILE-001")

    assert len(results) == 1
    assert results[0]["operation_id"] == "OP-001"


def test_operation_log_can_find_by_card_number(tmp_path):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    log.append(
        create_operation(
            operation_id="OP-001",
            card_number="CARD-001",
        )
    )

    log.append(
        create_operation(
            operation_id="OP-002",
            card_number="CARD-002",
        )
    )

    results = log.find_by_card_number("CARD-001")

    assert len(results) == 1
    assert results[0]["operation_id"] == "OP-001"


def test_operation_log_can_find_by_driver_id(tmp_path):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    log.append(
        create_operation(
            operation_id="OP-001",
            driver_id="DRIVER-001",
        )
    )

    log.append(
        create_operation(
            operation_id="OP-002",
            driver_id="DRIVER-002",
        )
    )

    results = log.find_by_driver_id("DRIVER-001")

    assert len(results) == 1
    assert results[0]["operation_id"] == "OP-001"


def test_operation_log_persists_between_instances(tmp_path):
    path = tmp_path / "operations.json"

    log = OperationLog(path)

    log.append(
        create_operation()
    )

    new_log = OperationLog(path)

    operations = new_log.all()

    assert len(operations) == 1
    assert operations[0]["operation_id"] == "OP-000001"


def test_operation_log_does_not_modify_ddd_file(tmp_path):
    ddd_path = tmp_path / "TEST.DDD"

    original_data = b"ORIGINAL_DDD_DATA"

    ddd_path.write_bytes(original_data)

    log = OperationLog(
        tmp_path / "operations.json"
    )

    operation = create_operation()

    log.append(operation)

    assert ddd_path.read_bytes() == original_data


def test_operation_log_can_find_by_status(tmp_path):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    completed = create_operation(
        operation_id="OP-001"
    )

    failed = Operation(
        operation_id="OP-002",
        operation_type=OperationType.CARD_DOWNLOAD,
        timestamp=datetime.now(timezone.utc),
        source_type=SourceType.DRIVER_CARD,
        status=OperationStatus.FAILED,
        error_message="Error de prueba",
    )

    log.append(completed)
    log.append(failed)

    results = log.find_by_status("FAILED")

    assert len(results) == 1
    assert results[0]["operation_id"] == "OP-002"


def test_operation_log_can_find_by_sync_status(tmp_path):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    synced = create_operation(
        operation_id="OP-001"
    )

    local_only = Operation(
        operation_id="OP-002",
        operation_type=OperationType.CARD_DOWNLOAD,
        timestamp=datetime.now(timezone.utc),
        source_type=SourceType.DRIVER_CARD,
        status=OperationStatus.COMPLETED,
        sync_status=SyncStatus.LOCAL_ONLY,
    )

    log.append(synced)
    log.append(local_only)

    results = log.find_by_sync_status("LOCAL_ONLY")

    assert len(results) == 1
    assert results[0]["operation_id"] == "OP-002"


def test_operation_log_can_find_by_operation_type(tmp_path):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    operation = create_operation()

    log.append(operation)

    results = log.find_by_operation_type(
        "CARD_DOWNLOAD"
    )

    assert len(results) == 1
    assert results[0]["operation_id"] == operation.operation_id


def test_operation_log_can_find_by_source_type(tmp_path):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    operation = create_operation()

    log.append(operation)

    results = log.find_by_source_type(
        "DRIVER_CARD"
    )

    assert len(results) == 1
    assert results[0]["operation_id"] == operation.operation_id
