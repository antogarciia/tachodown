import json
from dataclasses import asdict
from pathlib import Path

from simulator.metadata.models import Operation


class OperationLog:
    """Registro local de operaciones.

    Las operaciones se almacenan como entradas independientes en JSON
    y no modifican nunca los archivos DDD originales.
    """

    def __init__(self, path: Path):
        self.path = Path(path)

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.path.exists():
            self.path.write_text(
                "[]",
                encoding="utf-8",
            )

    def append(self, operation: Operation) -> None:
        operations = self._read()

        operations.append(
            self._serialize(operation)
        )

        self.path.write_text(
            json.dumps(
                operations,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def all(self) -> list[dict]:
        return self._read()
    
    def find_by_operation_id(
        self,
        operation_id: str,
    ) -> list[dict]:
        return [
            operation
            for operation in self._read()
            if operation.get("operation_id") == operation_id
        ]

    def find_by_file_id(self, file_id: str) -> list[dict]:
        return [
            operation
            for operation in self._read()
            if operation.get("file_id") == file_id
        ]

    def find_by_card_number(self, card_number: str) -> list[dict]:
        return [
            operation
            for operation in self._read()
            if operation.get("card_number") == card_number
        ]

    def find_by_driver_id(self, driver_id: str) -> list[dict]:
        return [
            operation
            for operation in self._read()
            if operation.get("driver_id") == driver_id
        ]

    def find_by_status(self, status: str) -> list[dict]:
        return [
            operation
            for operation in self._read()
            if operation.get("status") == status
        ]

    def find_by_sync_status(self, sync_status: str) -> list[dict]:
        return [
            operation
            for operation in self._read()
            if operation.get("sync_status") == sync_status
        ]

    def find_by_operation_type(
        self,
        operation_type: str,
    ) -> list[dict]:
        return [
            operation
            for operation in self._read()
            if operation.get("operation_type") == operation_type
        ]

    def find_by_source_type(
        self,
        source_type: str,
    ) -> list[dict]:
        return [
            operation
            for operation in self._read()
            if operation.get("source_type") == source_type
        ]

    def _read(self) -> list[dict]:
        content = self.path.read_text(
            encoding="utf-8"
        )

        if not content.strip():
            return []

        return json.loads(content)

    @staticmethod
    def _serialize(operation: Operation) -> dict:
        data = asdict(operation)

        for key, value in data.items():
            if hasattr(value, "value"):
                data[key] = value.value

        if hasattr(data.get("timestamp"), "isoformat"):
            data["timestamp"] = data["timestamp"].isoformat()

        return data

