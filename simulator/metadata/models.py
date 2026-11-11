from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OperationType(str, Enum):
    CARD_INSERTED = "CARD_INSERTED"
    CARD_DOWNLOAD = "CARD_DOWNLOAD"
    CARD_DELETE = "CARD_DELETE"
    TACHOGRAPH_CONNECT = "TACHOGRAPH_CONNECT"
    TACHOGRAPH_DOWNLOAD = "TACHOGRAPH_DOWNLOAD"
    SYNC = "SYNC"


class OperationStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SourceType(str, Enum):
    DRIVER_CARD = "DRIVER_CARD"
    TACHOGRAPH = "TACHOGRAPH"


class SyncStatus(str, Enum):
    LOCAL_ONLY = "LOCAL_ONLY"
    SYNC_PENDING = "SYNC_PENDING"
    SYNCED = "SYNCED"
    SYNC_FAILED = "SYNC_FAILED"


@dataclass(frozen=True)
class FileMetadata:
    file_id: str
    filename: str
    source_type: SourceType
    created_at: datetime
    size_bytes: int
    sha256: str
    storage_path: str


@dataclass(frozen=True)
class Operation:
    operation_id: str
    operation_type: OperationType
    timestamp: datetime
    source_type: SourceType
    status: OperationStatus

    card_number: str | None = None
    driver_id: str | None = None
    driver_name: str | None = None

    tachograph_id: str | None = None
    vehicle_id: str | None = None
    vehicle_registration: str | None = None

    file_id: str | None = None
    sync_status: SyncStatus | None = None
    error_message: str | None = None