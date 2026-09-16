"""from datetime import datetime, timezone
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
        )   """
        
        
import json
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from simulator.metadata.models import FileMetadata, SourceType


class LocalStorage:
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.metadata_path = self.base_path / "file_metadata.json"

        if not self.metadata_path.exists():
            self.metadata_path.write_text(
                "[]",
                encoding="utf-8",
            )

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

        metadata = FileMetadata(
            file_id=file_id,
            filename=candidate.name,
            source_type=source_type,
            created_at=datetime.now(timezone.utc),
            size_bytes=size_bytes,
            sha256=file_hash,
            storage_path=str(candidate),
        )

        self._save_metadata(metadata)

        return metadata

    def get_metadata(
        self,
        file_id: str,
    ) -> FileMetadata | None:
        for item in self._read_metadata():
            if item.get("file_id") != file_id:
                continue

            return FileMetadata(
                file_id=item["file_id"],
                filename=item["filename"],
                source_type=SourceType(item["source_type"]),
                created_at=datetime.fromisoformat(
                    item["created_at"]
                ),
                size_bytes=item["size_bytes"],
                sha256=item["sha256"],
                storage_path=item["storage_path"],
            )

        return None

    def list_metadata(self) -> list[FileMetadata]:
        return [
            metadata
            for metadata in (
                self.get_metadata(item["file_id"])
                for item in self._read_metadata()
            )
            if metadata is not None
        ]

    def _save_metadata(
        self,
        metadata: FileMetadata,
    ) -> None:
        records = self._read_metadata()

        records.append(
            self._serialize_metadata(metadata)
        )

        self.metadata_path.write_text(
            json.dumps(
                records,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _read_metadata(self) -> list[dict]:
        content = self.metadata_path.read_text(
            encoding="utf-8"
        )

        if not content.strip():
            return []

        return json.loads(content)

    @staticmethod
    def _serialize_metadata(
        metadata: FileMetadata,
    ) -> dict:
        data = asdict(metadata)

        data["source_type"] = metadata.source_type.value
        data["created_at"] = metadata.created_at.isoformat()

        return data