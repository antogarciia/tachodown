from datetime import datetime, timezone
from uuid import uuid4

from simulator.metadata.models import (
    Operation,
    OperationStatus,
    OperationType,
    SourceType,
    SyncStatus,
)
from simulator.operations.log import OperationLog
from simulator.storage.local_storage import LocalStorage
from simulator.sync.service import SyncService


class CardDownloadService:
    def __init__(
        self,
        reader,
        storage: LocalStorage,
        sync_service: SyncService | None = None,
        operation_log: OperationLog | None = None,
    ):
        self.reader = reader
        self.storage = storage
        self.sync_service = sync_service
        self.operation_log = operation_log

    def download(self) -> Operation:
        operation_id = f"OP-{uuid4().hex}"
        timestamp = datetime.now(timezone.utc)

        card = self.reader.read_card()

        if card is None:
            operation = Operation(
                operation_id=operation_id,
                operation_type=OperationType.CARD_DOWNLOAD,
                timestamp=timestamp,
                source_type=SourceType.DRIVER_CARD,
                status=OperationStatus.FAILED,
                error_message="No hay ninguna tarjeta insertada",
            )

            self._record(operation)

            return operation

        data = b"SIMULATED_DRIVER_CARD_DATA"

        filename = (
            f"{card.card_number}_"
            f"{timestamp:%Y%m%d%H%M%S}_"
            f"{operation_id[-6:]}.DDD"
        )

        try:
            metadata = self.storage.save(
                data=data,
                filename=filename,
                source_type=SourceType.DRIVER_CARD,
            )
        except Exception as exc:
            operation = Operation(
                operation_id=operation_id,
                operation_type=OperationType.CARD_DOWNLOAD,
                timestamp=timestamp,
                source_type=SourceType.DRIVER_CARD,
                status=OperationStatus.FAILED,
                card_number=card.card_number,
                driver_id=card.driver_id,
                error_message=str(exc),
            )

            self._record(operation)

            return operation

        sync_status = SyncStatus.LOCAL_ONLY

        if self.sync_service is not None:
            sync_status = self.sync_service.sync_file(metadata)

        operation = Operation(
            operation_id=operation_id,
            operation_type=OperationType.CARD_DOWNLOAD,
            timestamp=timestamp,
            source_type=SourceType.DRIVER_CARD,
            status=OperationStatus.COMPLETED,
            card_number=card.card_number,
            driver_id=card.driver_id,
            file_id=metadata.file_id,
            sync_status=sync_status,
        )

        self._record(operation)

        return operation

    def _record(self, operation: Operation) -> None:
        if self.operation_log is not None:
            self.operation_log.append(operation)