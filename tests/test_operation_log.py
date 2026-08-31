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
    operation_id="OP-001",
    status=OperationStatus.COMPLETED,
    operation_type=OperationType.CARD_DOWNLOAD,
    card_number="CARD-001",
    driver_id="DRIVER-001",
    file_id="FILE-001",
    sync_status=SyncStatus.SYNCED,
):
    return Operation(
        operation_id=operation_id,
        operation_type=operation_type,
        timestamp=datetime.now(timezone.utc),
        source_type=SourceType.DRIVER_CARD,
        status=status,
        card_number=card_number,
        driver_id=driver_id,
        file_id=file_id,
        sync_status=sync_status,
    )


def test_operation_log_finds_by_operation_id(tmp_path):
    log = OperationLog(tmp_path / "operations.json")

    operation = create_operation(
        operation_id="OP-123",
    )

    log.append(operation)

    results = log.find_by_operation_id("OP-123")

    assert len(results) == 1
    assert results[0]["operation_id"] == "OP-123"


def test_operation_log_returns_empty_for_unknown_operation_id(tmp_path):
    log = OperationLog(tmp_path / "operations.json")

    log.append(create_operation())

    results = log.find_by_operation_id("OP-UNKNOWN")

    assert results == []


def test_operation_log_can_find_multiple_operations_by_card(tmp_path):
    log = OperationLog(tmp_path / "operations.json")

    log.append(
        create_operation(
            operation_id="OP-001",
            card_number="CARD-A",
        )
    )

    log.append(
        create_operation(
            operation_id="OP-002",
            card_number="CARD-B",
        )
    )

    log.append(
        create_operation(
            operation_id="OP-003",
            card_number="CARD-A",
        )
    )

    results = log.find_by_card_number("CARD-A")

    assert len(results) == 2

    ids = {
        operation["operation_id"]
        for operation in results
    }

    assert ids == {"OP-001", "OP-003"}


def test_operation_log_can_find_failed_operations(tmp_path):
    log = OperationLog(tmp_path / "operations.json")

    log.append(
        create_operation(
            operation_id="OP-001",
            status=OperationStatus.COMPLETED,
        )
    )

    log.append(
        create_operation(
            operation_id="OP-002",
            status=OperationStatus.FAILED,
        )
    )

    results = log.find_by_status("FAILED")

    assert len(results) == 1
    assert results[0]["operation_id"] == "OP-002"


def test_operation_log_can_find_sync_operations(tmp_path):
    log = OperationLog(tmp_path / "operations.json")

    log.append(
        create_operation(
            operation_id="OP-001",
            operation_type=OperationType.CARD_DOWNLOAD,
        )
    )

    log.append(
        create_operation(
            operation_id="OP-002",
            operation_type=OperationType.SYNC,
        )
    )

    results = log.find_by_operation_type("SYNC")

    assert len(results) == 1
    assert results[0]["operation_id"] == "OP-002"


def test_operation_log_preserves_sync_status(tmp_path):
    log = OperationLog(tmp_path / "operations.json")

    operation = create_operation(
        sync_status=SyncStatus.LOCAL_ONLY,
    )

    log.append(operation)

    results = log.find_by_sync_status("LOCAL_ONLY")

    assert len(results) == 1
    assert results[0]["sync_status"] == "LOCAL_ONLY"


def test_operation_log_preserves_timestamp_as_iso_string(tmp_path):
    log = OperationLog(tmp_path / "operations.json")

    operation = create_operation()

    log.append(operation)

    results = log.all()

    assert len(results) == 1

    timestamp = results[0]["timestamp"]

    assert isinstance(timestamp, str)
    assert "T" in timestamp


def test_operation_log_persists_between_instances(tmp_path):
    path = tmp_path / "operations.json"

    first_log = OperationLog(path)

    first_log.append(
        create_operation(
            operation_id="OP-PERSISTED",
        )
    )

    second_log = OperationLog(path)

    results = second_log.find_by_operation_id(
        "OP-PERSISTED"
    )

    assert len(results) == 1
    assert results[0]["operation_id"] == "OP-PERSISTED"