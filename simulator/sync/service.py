import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from simulator.metadata.models import (
    Operation,
    OperationStatus,
    OperationType,
    SyncStatus,
)
from simulator.server.simulator import (
    ServerError,
    SimulatedServer,
)


class SyncService:
    def __init__(
        self,
        server: SimulatedServer,
        operation_log=None,
    ):
        self.server = server
        self.operation_log = operation_log

    def sync_file(self, metadata) -> SyncStatus:
        operation_id = f"OP-{uuid4().hex}"
        timestamp = datetime.now(timezone.utc)

        path = Path(metadata.storage_path)

        if not path.exists():
            status = SyncStatus.LOCAL_ONLY

            self._record(
                operation_id=operation_id,
                timestamp=timestamp,
                metadata=metadata,
                status=OperationStatus.FAILED,
                sync_status=status,
                error_message="El archivo local no existe",
            )

            return status

        data = path.read_bytes()

        local_sha256 = hashlib.sha256(data).hexdigest()

        if local_sha256 != metadata.sha256:
            status = SyncStatus.LOCAL_ONLY

            self._record(
                operation_id=operation_id,
                timestamp=timestamp,
                metadata=metadata,
                status=OperationStatus.FAILED,
                sync_status=status,
                error_message="El archivo local ha sido modificado",
            )

            return status

        try:
            uploaded = self.server.upload(
                file_id=metadata.file_id,
                filename=metadata.filename,
                data=data,
                sha256=metadata.sha256,
            )
        except ServerError as exc:
            status = SyncStatus.LOCAL_ONLY

            self._record(
                operation_id=operation_id,
                timestamp=timestamp,
                metadata=metadata,
                status=OperationStatus.FAILED,
                sync_status=status,
                error_message=str(exc),
            )

            return status

        uploaded_sha256 = hashlib.sha256(
            uploaded.data
        ).hexdigest()

        if uploaded_sha256 != metadata.sha256:
            status = SyncStatus.LOCAL_ONLY

            self._record(
                operation_id=operation_id,
                timestamp=timestamp,
                metadata=metadata,
                status=OperationStatus.FAILED,
                sync_status=status,
                error_message="La integridad del archivo remoto no coincide",
            )

            return status

        status = SyncStatus.SYNCED

        self._record(
            operation_id=operation_id,
            timestamp=timestamp,
            metadata=metadata,
            status=OperationStatus.COMPLETED,
            sync_status=status,
        )

        return status

    def _record(
        self,
        operation_id,
        timestamp,
        metadata,
        status,
        sync_status,
        error_message=None,
    ) -> None:
        if self.operation_log is None:
            return

        operation = Operation(
            operation_id=operation_id,
            operation_type=OperationType.SYNC,
            timestamp=timestamp,
            source_type=metadata.source_type,
            status=status,
            file_id=metadata.file_id,
            sync_status=sync_status,
            error_message=error_message,
        )

        self.operation_log.append(operation)
