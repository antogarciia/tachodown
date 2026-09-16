from datetime import datetime, timezone

from simulator.files.service import FileService
from simulator.metadata.models import (
    Operation,
    OperationStatus,
    OperationType,
    SourceType,
    SyncStatus,
)
from simulator.operations.log import OperationLog
from simulator.storage.local_storage import LocalStorage


def create_download_operation(
    operation_id="OP-001",
    file_id="FILE-001",
    operation_type=OperationType.CARD_DOWNLOAD,
    card_number="CARD-001",
):
    return Operation(
        operation_id=operation_id,
        operation_type=operation_type,
        timestamp=datetime.now(timezone.utc),
        source_type=SourceType.DRIVER_CARD,
        status=OperationStatus.COMPLETED,
        card_number=card_number,
        file_id=file_id,
        sync_status=SyncStatus.LOCAL_ONLY,
    )


def test_file_service_get_file_returns_metadata(tmp_path):
    storage = LocalStorage(tmp_path)

    data = b"DDD_CONTENT"

    metadata = storage.save(
        data=data,
        filename="CARD-001_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    log = OperationLog(
        tmp_path / "operations.json"
    )

    log.append(
        create_download_operation(
            file_id=metadata.file_id,
            card_number="CARD-001",
        )
    )

    service = FileService(
        storage_path=tmp_path,
        operation_log=log,
    )

    result = service.get_file(
        metadata.file_id
    )

    assert result is not None
    assert result.file_id == metadata.file_id
    assert result.filename == metadata.filename
    assert result.size_bytes == len(data)
    assert result.sha256 == metadata.sha256
    assert result.source_type == SourceType.DRIVER_CARD


def test_file_service_get_file_returns_none_for_unknown_file(
    tmp_path,
):
    log = OperationLog(
        tmp_path / "operations.json"
    )

    service = FileService(
        storage_path=tmp_path,
        operation_log=log,
    )

    result = service.get_file(
        "FILE-UNKNOWN"
    )

    assert result is None


def test_file_service_list_files_returns_known_files(
    tmp_path,
):
    storage = LocalStorage(tmp_path)

    first = storage.save(
        data=b"FIRST_DDD",
        filename="CARD-A_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    second = storage.save(
        data=b"SECOND_DDD",
        filename="CARD-B_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    log = OperationLog(
        tmp_path / "operations.json"
    )

    log.append(
        create_download_operation(
            operation_id="OP-001",
            file_id=first.file_id,
            card_number="CARD-A",
        )
    )

    log.append(
        create_download_operation(
            operation_id="OP-002",
            file_id=second.file_id,
            card_number="CARD-B",
        )
    )

    service = FileService(
        storage_path=tmp_path,
        operation_log=log,
    )

    results = service.list_files()

    assert len(results) == 2

    file_ids = {
        item.file_id
        for item in results
    }

    assert file_ids == {
        first.file_id,
        second.file_id,
    }


def test_file_service_verify_file_returns_true_for_unchanged_file(
    tmp_path,
):
    storage = LocalStorage(tmp_path)

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="CARD-001_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    log = OperationLog(
        tmp_path / "operations.json"
    )

    log.append(
        create_download_operation(
            file_id=metadata.file_id,
            card_number="CARD-001",
        )
    )

    service = FileService(
        storage_path=tmp_path,
        operation_log=log,
    )

    assert service.verify_file(
        metadata.file_id
    ) is True


def test_file_service_detects_modified_file(
    tmp_path,
):
    storage = LocalStorage(tmp_path)

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="CARD-001_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    log = OperationLog(
        tmp_path / "operations.json"
    )

    log.append(
        create_download_operation(
            file_id=metadata.file_id,
            card_number="CARD-001",
        )
    )

    path = tmp_path / metadata.filename

    path.write_bytes(
        b"MODIFIED_DDD_DATA"
    )

    service = FileService(
        storage_path=tmp_path,
        operation_log=log,
    )

    assert service.verify_file(
        metadata.file_id
    ) is False


def test_file_service_detects_deleted_file(
    tmp_path,
):
    storage = LocalStorage(tmp_path)

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="CARD-001_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    log = OperationLog(
        tmp_path / "operations.json"
    )

    log.append(
        create_download_operation(
            file_id=metadata.file_id,
            card_number="CARD-001",
        )
    )

    path = tmp_path / metadata.filename
    path.unlink()

    service = FileService(
        storage_path=tmp_path,
        operation_log=log,
    )

    assert service.get_file(
        metadata.file_id
    ) is None

    assert service.verify_file(
        metadata.file_id
    ) is False


def test_file_service_does_not_modify_original_file(
    tmp_path,
):
    storage = LocalStorage(tmp_path)

    original_data = b"ORIGINAL_DDD_DATA"

    metadata = storage.save(
        data=original_data,
        filename="CARD-001_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    log = OperationLog(
        tmp_path / "operations.json"
    )

    log.append(
        create_download_operation(
            file_id=metadata.file_id,
            card_number="CARD-001",
        )
    )

    service = FileService(
        storage_path=tmp_path,
        operation_log=log,
    )

    service.verify_file(
        metadata.file_id
    )

    path = tmp_path / metadata.filename

    assert path.read_bytes() == original_data