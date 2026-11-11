from datetime import datetime
from pathlib import Path

from simulator.card.reader import CardReader
from simulator.device.controller import DeviceController
from simulator.download.card_download import CardDownloadService
from simulator.download.tachograph_download import (
    TachographDownloadService,
)
from simulator.files.service import FileService
from simulator.metadata.models import (
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
    - gestión de archivos y metadatos
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

        self.file_service = FileService(
            storage_path=self.storage_path,
            operation_log=self.operation_log,
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

        return self.tachograph_download_service.download()

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

            metadata = self.file_service.get_file(
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

    @staticmethod
    def _operation_from_dict(
        data,
    ):
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