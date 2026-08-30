from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from simulator.metadata.models import FileMetadata, SourceType


class LocalStorage:
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        data: bytes,
        filename: str,
        source_type: SourceType,
    ) -> FileMetadata:
        if not data:
            raise ValueError("No se pueden guardar datos vacíos")

        if not filename:
            raise ValueError("El nombre del archivo es obligatorio")

        candidate = (self.base_path / filename).resolve()

        try:
            candidate.relative_to(self.base_path)
        except ValueError:
            raise ValueError(
                "El archivo debe permanecer dentro del almacenamiento local"
            )

        file_id = f"FILE-{uuid4().hex}"

        file_hash = sha256(data).hexdigest()
        size_bytes = len(data)

        if candidate.exists():
            raise FileExistsError(
                f"El archivo ya existe: {filename}"
            )

        candidate.write_bytes(data)

        return FileMetadata(
            file_id=file_id,
            filename=candidate.name,
            source_type=source_type,
            created_at=datetime.now(timezone.utc),
            size_bytes=size_bytes,
            sha256=file_hash,
            storage_path=str(candidate),
        )