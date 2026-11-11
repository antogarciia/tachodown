from pathlib import Path

from simulator.download.tachograph_download import (
    TachographDownloadService,
)
from simulator.metadata.models import (
    OperationStatus,
    OperationType,
    SourceType,
    SyncStatus,
)
from simulator.operations.log import OperationLog
from simulator.storage.local_storage import LocalStorage
from simulator.tachograph.simulator import SimulatedTachograph


def create_tachograph():
    tachograph = SimulatedTachograph()

    tachograph.connect()
    tachograph.authenticate()

    return tachograph


def test_tachograph_download_saves_ddd_and_creates_metadata(
    tmp_path,
):
    tachograph = create_tachograph()

    storage = LocalStorage(tmp_path)

    service = TachographDownloadService(
        tachograph,
        storage,
    )

    operation = service.download()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.operation_type == (
        OperationType.TACHOGRAPH_DOWNLOAD
    )
    assert operation.source_type == SourceType.TACHOGRAPH
    assert operation.file_id is not None
    assert operation.sync_status == SyncStatus.LOCAL_ONLY

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 1
    assert files[0].read_bytes() == (
        b"SIMULATED_TACHOGRAPH_DATA"
    )


def test_tachograph_download_preserves_original_data(
    tmp_path,
):
    tachograph = create_tachograph()

    storage = LocalStorage(tmp_path)

    service = TachographDownloadService(
        tachograph,
        storage,
    )

    operation = service.download()

    assert operation.file_id is not None

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 1

    saved_data = files[0].read_bytes()

    assert saved_data == b"SIMULATED_TACHOGRAPH_DATA"


def test_tachograph_download_requires_authentication(
    tmp_path,
):
    tachograph = SimulatedTachograph()
    tachograph.connect()

    storage = LocalStorage(tmp_path)

    service = TachographDownloadService(
        tachograph,
        storage,
    )

    operation = service.download()

    assert operation.status == OperationStatus.FAILED
    assert operation.operation_type == (
        OperationType.TACHOGRAPH_DOWNLOAD
    )
    assert operation.source_type == SourceType.TACHOGRAPH
    assert operation.file_id is None

    files = list(tmp_path.glob("*.DDD"))

    assert files == []


def test_two_tachograph_downloads_create_different_files(
    tmp_path,
):
    tachograph = create_tachograph()

    storage = LocalStorage(tmp_path)

    service = TachographDownloadService(
        tachograph,
        storage,
    )

    first = service.download()
    second = service.download()

    assert first.status == OperationStatus.COMPLETED
    assert second.status == OperationStatus.COMPLETED

    assert first.file_id != second.file_id

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 2


def test_tachograph_download_records_operation(
    tmp_path,
):
    tachograph = create_tachograph()

    storage = LocalStorage(tmp_path)

    log = OperationLog(
        tmp_path / "operations.json"
    )

    service = TachographDownloadService(
        tachograph,
        storage,
        log,
    )

    operation = service.download()

    operations = log.all()

    assert len(operations) == 1
    assert operations[0]["operation_id"] == (
        operation.operation_id
    )
    assert operations[0]["operation_type"] == (
        "TACHOGRAPH_DOWNLOAD"
    )
    assert operations[0]["source_type"] == (
        "TACHOGRAPH"
    )
    assert operations[0]["file_id"] == (
        operation.file_id
    )


def test_failed_tachograph_download_is_recorded(
    tmp_path,
):
    tachograph = SimulatedTachograph()
    tachograph.connect()

    storage = LocalStorage(tmp_path)

    log = OperationLog(
        tmp_path / "operations.json"
    )

    service = TachographDownloadService(
        tachograph,
        storage,
        log,
    )

    operation = service.download()

    assert operation.status == OperationStatus.FAILED

    operations = log.all()

    assert len(operations) == 1
    assert operations[0]["operation_id"] == (
        operation.operation_id
    )
    assert operations[0]["status"] == "FAILED"
    assert operations[0]["source_type"] == (
        "TACHOGRAPH"
    )
    
    
def test_tachograph_download_records_tachograph_identity(
    tmp_path,
):
    tachograph = SimulatedTachograph(
        tachograph_id="TACHO-123",
        vehicle_id="VEHICLE-456",
        vehicle_registration="9999-XYZ",
    )

    tachograph.connect()
    tachograph.authenticate()

    storage = LocalStorage(tmp_path)

    service = TachographDownloadService(
        tachograph,
        storage,
    )

    operation = service.download()

    assert operation.status == OperationStatus.COMPLETED
    assert operation.tachograph_id == "TACHO-123"
    assert operation.vehicle_id == "VEHICLE-456"
    assert operation.vehicle_registration == "9999-XYZ"
    
    
def test_tachograph_download_persists_identity_in_operation_log(
    tmp_path,
):
    tachograph = SimulatedTachograph(
        tachograph_id="TACHO-123",
        vehicle_id="VEHICLE-456",
        vehicle_registration="9999-XYZ",
    )

    tachograph.connect()
    tachograph.authenticate()

    storage = LocalStorage(tmp_path)

    log = OperationLog(
        tmp_path / "operations.json"
    )

    service = TachographDownloadService(
        tachograph,
        storage,
        log,
    )

    service.download()

    operations = log.all()

    assert len(operations) == 1

    saved = operations[0]

    assert saved["tachograph_id"] == "TACHO-123"
    assert saved["vehicle_id"] == "VEHICLE-456"
    assert saved["vehicle_registration"] == "9999-XYZ"
    
    
def test_tachograph_download_requires_connection(
    tmp_path,
):
    tachograph = SimulatedTachograph()

    storage = LocalStorage(tmp_path)

    service = TachographDownloadService(
        tachograph,
        storage,
    )

    operation = service.download()

    assert operation.status == OperationStatus.FAILED
    assert operation.file_id is None
    assert operation.error_message is not None

    assert list(tmp_path.glob("*.DDD")) == []


def test_tachograph_download_failure_preserves_identity(
    tmp_path,
):
    tachograph = SimulatedTachograph(
        tachograph_id="TACHO-ERROR",
        vehicle_id="VEHICLE-ERROR",
        vehicle_registration="ERROR-123",
    )

    tachograph.connect()

    storage = LocalStorage(tmp_path)

    service = TachographDownloadService(
        tachograph,
        storage,
    )

    operation = service.download()

    assert operation.status == OperationStatus.FAILED
    assert operation.tachograph_id == "TACHO-ERROR"
    assert operation.vehicle_id == "VEHICLE-ERROR"
    assert operation.vehicle_registration == "ERROR-123"
    assert operation.file_id is None


def test_tachograph_download_storage_failure_is_recorded(
    tmp_path,
):
    tachograph = SimulatedTachograph(
        tachograph_id="TACHO-123",
        vehicle_id="VEHICLE-456",
        vehicle_registration="9999-XYZ",
    )

    tachograph.connect()
    tachograph.authenticate()

    class FailingStorage:
        def save(self, *args, **kwargs):
            raise IOError("Error simulado de almacenamiento")

    service = TachographDownloadService(
        tachograph,
        FailingStorage(),
    )

    operation = service.download()

    assert operation.status == OperationStatus.FAILED
    assert operation.file_id is None
    assert operation.tachograph_id == "TACHO-123"
    assert operation.vehicle_id == "VEHICLE-456"
    assert operation.vehicle_registration == "9999-XYZ"
    assert "Error simulado de almacenamiento" in operation.error_message


def test_tachograph_download_does_not_create_file_when_storage_fails(
    tmp_path,
):
    tachograph = SimulatedTachograph()

    tachograph.connect()
    tachograph.authenticate()

    class FailingStorage:
        def save(self, *args, **kwargs):
            raise IOError("Fallo de escritura")

    service = TachographDownloadService(
        tachograph,
        FailingStorage(),
    )

    operation = service.download()

    assert operation.status == OperationStatus.FAILED
    assert list(tmp_path.glob("*.DDD")) == []