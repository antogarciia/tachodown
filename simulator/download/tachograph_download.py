"""from datetime import datetime, timezone
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


class TachographDownloadService:
    def __init__(
        self,
        tachograph,
        storage: LocalStorage,
        sync_service: SyncService | OperationLog | None = None,
        operation_log: OperationLog | None = None,
    ):
        self.tachograph = tachograph
        self.storage = storage

        # Compatibilidad con las dos formas de construcción:
        #
        # Nueva:
        # TachographDownloadService(
        #     tachograph,
        #     storage,
        #     sync_service,
        #     operation_log,
        # )
        #
        # Antigua:
        # TachographDownloadService(
        #     tachograph,
        #     storage,
        #     operation_log,
        # )
        if isinstance(sync_service, OperationLog):
            self.sync_service = None
            self.operation_log = sync_service
        else:
            self.sync_service = sync_service
            self.operation_log = operation_log

    def download(self) -> Operation:
        operation_id = f"OP-{uuid4().hex}"
        timestamp = datetime.now(timezone.utc)

        tachograph_id = getattr(
            self.tachograph,
            "tachograph_id",
            None,
        )

        vehicle_id = getattr(
            self.tachograph,
            "vehicle_id",
            None,
        )

        vehicle_registration = getattr(
            self.tachograph,
            "vehicle_registration",
            None,
        )

        # ---------------------------------------------------------
        # 1. Descargar datos del tacógrafo
        # ---------------------------------------------------------
        try:
            data = self.tachograph.download()

        except Exception as exc:
            operation = Operation(
                operation_id=operation_id,
                operation_type=OperationType.TACHOGRAPH_DOWNLOAD,
                timestamp=timestamp,
                source_type=SourceType.TACHOGRAPH,
                status=OperationStatus.FAILED,
                tachograph_id=tachograph_id,
                vehicle_id=vehicle_id,
                vehicle_registration=vehicle_registration,
                file_id=None,
                sync_status=None,
                error_message=str(exc),
            )

            self._record(operation)

            return operation

        # ---------------------------------------------------------
        # 2. Crear nombre del archivo DDD
        # ---------------------------------------------------------
        filename = (
            f"TACHOGRAPH_"
            f"{timestamp:%Y%m%d%H%M%S}_"
            f"{operation_id[-6:]}.DDD"
        )

        # ---------------------------------------------------------
        # 3. Guardar archivo localmente
        # ---------------------------------------------------------
        try:
            metadata = self.storage.save(
                data=data,
                filename=filename,
                source_type=SourceType.TACHOGRAPH,
            )

        except Exception as exc:
            operation = Operation(
                operation_id=operation_id,
                operation_type=OperationType.TACHOGRAPH_DOWNLOAD,
                timestamp=timestamp,
                source_type=SourceType.TACHOGRAPH,
                status=OperationStatus.FAILED,
                tachograph_id=tachograph_id,
                vehicle_id=vehicle_id,
                vehicle_registration=vehicle_registration,
                file_id=None,
                sync_status=None,
                error_message=str(exc),
            )

            self._record(operation)

            return operation

        # ---------------------------------------------------------
        # 4. Sincronizar si existe SyncService
        # ---------------------------------------------------------
        sync_status = SyncStatus.LOCAL_ONLY

        if self.sync_service is not None:
            try:
                sync_status = self.sync_service.sync_file(
                    metadata
                )

            except Exception:
                # El archivo ya está guardado localmente.
                # Si falla la sincronización, permanece pendiente.
                sync_status = SyncStatus.LOCAL_ONLY

        # ---------------------------------------------------------
        # 5. Crear operación final
        # ---------------------------------------------------------
        operation = Operation(
            operation_id=operation_id,
            operation_type=OperationType.TACHOGRAPH_DOWNLOAD,
            timestamp=timestamp,
            source_type=SourceType.TACHOGRAPH,
            status=OperationStatus.COMPLETED,
            tachograph_id=tachograph_id,
            vehicle_id=vehicle_id,
            vehicle_registration=vehicle_registration,
            file_id=metadata.file_id,
            sync_status=sync_status,
        )

        # ---------------------------------------------------------
        # 6. Registrar UNA sola operación de descarga
        # ---------------------------------------------------------
        self._record(operation)

        return operation

    def _record(
        self,
        operation: Operation,
    ) -> None:
        if self.operation_log is not None:
            self.operation_log.append(operation) """
            
            
            
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

# Importamos nuestra nueva interfaz abstracta
from simulator.hardware.interface import TachographHardwareInterface


class TachographDownloadService:
    def __init__(
        self,
        tachograph,
        storage: LocalStorage,
        sync_service: SyncService | OperationLog | None = None,
        operation_log: OperationLog | None = None,
        hardware: TachographHardwareInterface | None = None,  # INYECCIÓN DEL HARDWARE
    ):
        self.tachograph = tachograph
        self.storage = storage
        self.hardware = hardware

        if isinstance(sync_service, OperationLog):
            self.sync_service = None
            self.operation_log = sync_service
        else:
            self.sync_service = sync_service
            self.operation_log = operation_log

    def download(self) -> Operation:
        operation_id = f"OP-{uuid4().hex}"
        timestamp = datetime.now(timezone.utc)

        tachograph_id = getattr(self.tachograph, "tachograph_id", None)
        vehicle_id = getattr(self.tachograph, "vehicle_id", None)
        vehicle_registration = getattr(self.tachograph, "vehicle_registration", None)

        # ---------------------------------------------------------
        # 1. Descargar datos del tacógrafo (HARDWARE REAL/SIMULADOR)
        # ---------------------------------------------------------
        try:
            if self.hardware is not None:
                if self.hardware.connect():
                    try:
                        data = self.hardware.read_vehicle_unit()
                    finally:
                        self.hardware.disconnect()
                else:
                    raise ConnectionError("No se pudo conectar al tacógrafo físico.")
            else:
                # Fallback para tests antiguos
                data = self.tachograph.download()

        except Exception as exc:
            operation = Operation(
                operation_id=operation_id,
                operation_type=OperationType.TACHOGRAPH_DOWNLOAD,
                timestamp=timestamp,
                source_type=SourceType.TACHOGRAPH,
                status=OperationStatus.FAILED,
                tachograph_id=tachograph_id,
                vehicle_id=vehicle_id,
                vehicle_registration=vehicle_registration,
                file_id=None,
                sync_status=None,
                error_message=str(exc),
            )
            self._record(operation)
            return operation

        # ---------------------------------------------------------
        # 2. Crear nombre del archivo DDD
        # ---------------------------------------------------------
        filename = (
            f"TACHOGRAPH_"
            f"{timestamp:%Y%m%d%H%M%S}_"
            f"{operation_id[-6:]}.DDD"
        )

        # ---------------------------------------------------------
        # 3. Guardar archivo localmente
        # ---------------------------------------------------------
        try:
            metadata = self.storage.save(
                data=data,
                filename=filename,
                source_type=SourceType.TACHOGRAPH,
            )

        except Exception as exc:
            operation = Operation(
                operation_id=operation_id,
                operation_type=OperationType.TACHOGRAPH_DOWNLOAD,
                timestamp=timestamp,
                source_type=SourceType.TACHOGRAPH,
                status=OperationStatus.FAILED,
                tachograph_id=tachograph_id,
                vehicle_id=vehicle_id,
                vehicle_registration=vehicle_registration,
                file_id=None,
                sync_status=None,
                error_message=str(exc),
            )
            self._record(operation)
            return operation

        # ---------------------------------------------------------
        # 4. Sincronizar si existe SyncService
        # ---------------------------------------------------------
        sync_status = SyncStatus.LOCAL_ONLY

        if self.sync_service is not None:
            try:
                sync_status = self.sync_service.sync_file(metadata)
            except Exception:
                sync_status = SyncStatus.LOCAL_ONLY

        # ---------------------------------------------------------
        # 5. Crear operación final
        # ---------------------------------------------------------
        operation = Operation(
            operation_id=operation_id,
            operation_type=OperationType.TACHOGRAPH_DOWNLOAD,
            timestamp=timestamp,
            source_type=SourceType.TACHOGRAPH,
            status=OperationStatus.COMPLETED,
            tachograph_id=tachograph_id,
            vehicle_id=vehicle_id,
            vehicle_registration=vehicle_registration,
            file_id=metadata.file_id,
            sync_status=sync_status,
        )

        self._record(operation)
        return operation

    def _record(self, operation: Operation) -> None:
        if self.operation_log is not None:
            self.operation_log.append(operation)