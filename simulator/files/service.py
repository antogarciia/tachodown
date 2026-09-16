from hashlib import sha256
from pathlib import Path

from simulator.metadata.models import FileMetadata
from simulator.operations.log import OperationLog
from simulator.storage.local_storage import LocalStorage


class FileService:
    """
    Servicio de consulta y verificación de archivos DDD.

    El servicio no modifica nunca los archivos originales.
    """

    def __init__(
        self,
        storage_path: Path,
        operation_log: OperationLog,
    ):
        self.storage_path = Path(storage_path).resolve()
        self.operation_log = operation_log
        self.storage = LocalStorage(self.storage_path)

    def list_files(self) -> list[FileMetadata]:
        """
        Devuelve los archivos DDD registrados en el almacenamiento.
        """
        results = []

        for metadata in self.storage.list_metadata():
            if not self._is_inside_storage(
                Path(metadata.storage_path)
            ):
                continue

            if not Path(metadata.storage_path).exists():
                continue

            results.append(metadata)

        return results

    def get_file(
        self,
        file_id: str,
    ) -> FileMetadata | None:
        """
        Obtiene los metadatos originales de un archivo DDD.

        Devuelve None si el archivo no está registrado
        o si el archivo físico ya no existe.
        """
        if not file_id:
            return None

        metadata = self.storage.get_metadata(file_id)

        if metadata is None:
            return None

        path = Path(metadata.storage_path)

        if not self._is_inside_storage(path):
            return None

        if not path.exists():
            return None

        if not path.is_file():
            return None

        return metadata

    def verify_file(
        self,
        file_id: str,
    ) -> bool:
        """
        Verifica que el archivo físico coincide con sus
        metadatos originales.

        Comprueba:
        - existencia;
        - tamaño;
        - SHA-256.
        """
        metadata = self.storage.get_metadata(file_id)

        if metadata is None:
            return False

        path = Path(metadata.storage_path)

        if not self._is_inside_storage(path):
            return False

        if not path.exists():
            return False

        if not path.is_file():
            return False

        data = path.read_bytes()

        current_size = len(data)
        current_hash = sha256(data).hexdigest()

        return (
            current_size == metadata.size_bytes
            and current_hash == metadata.sha256
        )

    def _is_inside_storage(
        self,
        path: Path,
    ) -> bool:
        """
        Comprueba que una ruta permanece dentro del almacenamiento.
        """
        try:
            path.resolve().relative_to(
                self.storage_path
            )
            return True
        except ValueError:
            return False