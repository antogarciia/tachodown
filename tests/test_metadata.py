from datetime import datetime

import pytest

from simulator.metadata.models import (
    FileMetadata,
    Operation,
    OperationStatus,
    OperationType,
    SourceType,
    SyncStatus,
)


def test_operation_can_be_created():
    operation = Operation(
        operation_id="OP-000001",
        operation_type=OperationType.CARD_DOWNLOAD,
        timestamp=datetime.now(),
        source_type=SourceType.DRIVER_CARD,
        status=OperationStatus.COMPLETED,
        card_number="TEST-CARD-001",
        driver_id="DRIVER-001",
        driver_name="Juan García",
        file_id="FILE-000001",
        sync_status=SyncStatus.SYNCED,
    )

    assert operation.operation_id == "OP-000001"
    assert operation.operation_type == OperationType.CARD_DOWNLOAD
    assert operation.driver_name == "Juan García"
    assert operation.file_id == "FILE-000001"
    assert operation.sync_status == SyncStatus.SYNCED


def test_operation_is_immutable():
    operation = Operation(
        operation_id="OP-000001",
        operation_type=OperationType.CARD_DOWNLOAD,
        timestamp=datetime.now(),
        source_type=SourceType.DRIVER_CARD,
        status=OperationStatus.COMPLETED,
    )

    with pytest.raises(Exception):
        operation.status = OperationStatus.FAILED


def test_file_metadata_can_be_created():
    file_metadata = FileMetadata(
        file_id="FILE-000001",
        filename="CARD_001_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
        created_at=datetime.now(),
        size_bytes=131072,
        sha256="abc123",
        storage_path="local/files/CARD_001_20260830.DDD",
    )

    assert file_metadata.file_id == "FILE-000001"
    assert file_metadata.filename == "CARD_001_20260830.DDD"
    assert file_metadata.size_bytes == 131072
    assert file_metadata.sha256 == "abc123"


def test_file_metadata_is_immutable():
    file_metadata = FileMetadata(
        file_id="FILE-000001",
        filename="CARD_001_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
        created_at=datetime.now(),
        size_bytes=131072,
        sha256="abc123",
        storage_path="local/files/CARD_001_20260830.DDD",
    )

    with pytest.raises(Exception):
        file_metadata.sha256 = "otro_hash"