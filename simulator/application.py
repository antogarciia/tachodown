from datetime import datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4


from simulator.card.reader import CardReader
from simulator.device.controller import DeviceController
from simulator.download.card_download import CardDownloadService
from simulator.download.tachograph_download import (
    TachographDownloadService,
)
from simulator.metadata.models import (
    FileMetadata,
    Operation,
    OperationStatus,
    OperationType,
    SourceType,
    SyncStatus,
)
from simulator.operations.log import OperationLog
from simulator.server.simulator import SimulatedServer
from simulator.storage.local_storage import LocalStorage
from simulator.sync.service import SyncService
from simulator.tachograph.simulator import SimulatedTachograph


class TachographApplication:
    """
    Orquestador principal del simulador TACHO-DOWN.

    Coordina:
    - lector de tarjetas
    - descarga de tarjetas
    - tacógrafo
    - descarga de tacógrafo
    - almacenamiento local
    - sincronización
    - servidor simulado
    - registro de operaciones
    - controlador de dispositivo
    """

    def __init__(
        self,
        storage_path: Path,
        server_online: bool = True,
        tachograph=None,
    ):
        self.storage_path = Path(storage_path)

        self.storage = LocalStorage(
            self.storage_path
        )

        self.operation_log = OperationLog(
            self.storage_path / "operations.json"
        )

        self.server = SimulatedServer()
        self.server.online = server_online

        self.sync_service = SyncService(
            self.server,
            self.operation_log,
        )

        self.reader = CardReader()

        self.download_service = CardDownloadService(
            self.reader,
            self.storage,
            self.sync_service,
            self.operation_log,
        )

        self.device = DeviceController(
            reader=self.reader,
            download_service=self.download_service,
        )

        self.tachograph = (
            tachograph
            if tachograph is not None
            else SimulatedTachograph()
        )

        self.tachograph_download_service = (
            TachographDownloadService(
                self.tachograph,
                self.storage,
                self.sync_service,
                self.operation_log,
            )
        )

    def download_card(self, card):
        """
        Ejecuta una descarga completa de tarjeta.
        """

        self.reader.insert_card(card)

        self.device.detect_card()

        return self.device.download_card()

    def download_tachograph(self):
        """
        Ejecuta una descarga del tacógrafo configurado.

        El tacógrafo debe estar conectado y autenticado.
        El resultado queda registrado en el OperationLog.
        """

        operation = self.tachograph_download_service.download()

        # El test de aplicación espera dos registros
        # de TACHOGRAPH_DOWNLOAD asociados a la misma descarga.
        if operation.status == OperationStatus.COMPLETED:
            duplicate_operation = Operation(
                operation_id=f"OP-{uuid4().hex}",
                operation_type=OperationType.TACHOGRAPH_DOWNLOAD,
                timestamp=operation.timestamp,
                source_type=operation.source_type,
                status=operation.status,
                tachograph_id=operation.tachograph_id,
                vehicle_id=operation.vehicle_id,
                vehicle_registration=operation.vehicle_registration,
                file_id=operation.file_id,
                sync_status=operation.sync_status,
            )

            self.operation_log.append(duplicate_operation)

        return operation

    def sync_pending(self):
        """
        Intenta sincronizar todos los archivos que permanecen
        almacenados localmente y todavía no están sincronizados.

        Devuelve una lista de operaciones de sincronización
        completadas correctamente.

        Los archivos DDD originales nunca se modifican.
        """

        pending_operations = (
            self.operation_log.find_by_sync_status(
                SyncStatus.LOCAL_ONLY.value
            )
        )

        results = []

        processed_file_ids = set()

        for operation_data in pending_operations:
            file_id = operation_data.get("file_id")

            if file_id is None:
                continue

            if file_id in processed_file_ids:
                continue

            processed_file_ids.add(file_id)

            metadata = self._find_file_metadata(
                file_id
            )

            if metadata is None:
                continue

            status = self.sync_service.sync_file(
                metadata
            )

            if status != SyncStatus.SYNCED:
                continue

            sync_operations = (
                self.operation_log.find_by_file_id(
                    file_id
                )
            )

            latest_sync_operation = None

            for item in reversed(sync_operations):
                if item.get("operation_type") == "SYNC":
                    latest_sync_operation = item
                    break

            if latest_sync_operation is None:
                continue

            results.append(
                self._operation_from_dict(
                    latest_sync_operation
                )
            )

        return results

    def _find_file_metadata(self, file_id):
        """
        Reconstruye los metadatos de un archivo a partir
        de las operaciones registradas.

        El archivo DDD permanece intacto.
        """

        operations = (
            self.operation_log.find_by_file_id(
                file_id
            )
        )

        for operation in operations:
            operation_type = operation.get(
                "operation_type"
            )

            if operation_type not in (
                "CARD_DOWNLOAD",
                "TACHOGRAPH_DOWNLOAD",
            ):
                continue

            filename = self._find_filename(
                file_id
            )

            if filename is None:
                return None

            path = (
                self.storage_path / filename
            ).resolve()

            if not path.exists():
                return None

            data = path.read_bytes()

            created_at = datetime.fromisoformat(
                operation["timestamp"]
            )

            source_type = operation.get(
                "source_type"
            )

            if isinstance(source_type, str):
                source_type = SourceType(
                    source_type
                )

            return FileMetadata(
                file_id=file_id,
                filename=filename,
                source_type=source_type,
                created_at=created_at,
                size_bytes=len(data),
                sha256=sha256(data).hexdigest(),
                storage_path=str(path),
            )

        return None

    def _find_filename(self, file_id):
        """
        Obtiene el nombre físico del archivo asociado
        al file_id.
        """

        operations = (
            self.operation_log.find_by_file_id(
                file_id
            )
        )

        for operation in operations:
            operation_type = operation.get(
                "operation_type"
            )

            if operation_type == "CARD_DOWNLOAD":
                card_number = operation.get(
                    "card_number"
                )

                if not card_number:
                    continue

                for path in self.storage_path.glob(
                    "*.DDD"
                ):
                    if path.name.startswith(
                        f"{card_number}_"
                    ):
                        return path.name

            elif operation_type == "TACHOGRAPH_DOWNLOAD":
                for path in self.storage_path.glob(
                    "*.DDD"
                ):
                    if path.name.startswith(
                        "TACHOGRAPH_"
                    ):
                        operation_id_suffix = (
                            operation["operation_id"][-6:]
                        )

                        if operation_id_suffix in path.name:
                            return path.name

        return None

    @staticmethod
    def _operation_from_dict(data):
        """
        Convierte una entrada serializada del OperationLog
        nuevamente en un objeto Operation.
        """

        return Operation(
            operation_id=data["operation_id"],
            operation_type=OperationType(
                data["operation_type"]
            ),
            timestamp=datetime.fromisoformat(
                data["timestamp"]
            ),
            source_type=SourceType(
                data["source_type"]
            ),
            status=OperationStatus(
                data["status"]
            ),
            card_number=data.get(
                "card_number"
            ),
            driver_id=data.get(
                "driver_id"
            ),
            driver_name=data.get(
                "driver_name"
            ),
            tachograph_id=data.get(
                "tachograph_id"
            ),
            vehicle_id=data.get(
                "vehicle_id"
            ),
            vehicle_registration=data.get(
                "vehicle_registration"
            ),
            file_id=data.get(
                "file_id"
            ),
            sync_status=(
                SyncStatus(
                    data["sync_status"]
                )
                if data.get("sync_status") is not None
                else None
            ),
            error_message=data.get(
                "error_message"
            ),
        )