from dataclasses import dataclass


class ServerError(Exception):
    """Error relacionado con el servidor simulado."""


@dataclass(frozen=True)
class UploadedFile:
    file_id: str
    filename: str
    data: bytes
    sha256: str


class SimulatedServer:
    """Servidor simulado para almacenar archivos DDD."""

    def __init__(self):
        self.online = True
        self.files: dict[str, UploadedFile] = {}

    def upload(
        self,
        file_id: str,
        filename: str,
        data: bytes,
        sha256: str,
    ) -> UploadedFile:
        """Sube un archivo al servidor simulado."""

        if not self.online:
            raise ServerError(
                "Servidor no disponible"
            )

        if file_id in self.files:
            raise ServerError(
                f"El archivo ya existe en el servidor: {file_id}"
            )

        uploaded = UploadedFile(
            file_id=file_id,
            filename=filename,
            data=data,
            sha256=sha256,
        )

        self.files[file_id] = uploaded

        return uploaded

    def get_file(
        self,
        file_id: str,
    ) -> UploadedFile | None:
        """Obtiene un archivo previamente subido."""

        return self.files.get(file_id)