from simulator.metadata.models import SourceType
from simulator.storage.local_storage import LocalStorage


def test_storage_saves_file_and_generates_metadata(tmp_path):
    storage = LocalStorage(tmp_path)

    data = b"SIMULATED_DDD_DATA"

    metadata = storage.save(
        data=data,
        filename="CARD_001_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    assert metadata.file_id
    assert metadata.filename == "CARD_001_20260830.DDD"
    assert metadata.source_type == SourceType.DRIVER_CARD
    assert metadata.size_bytes == len(data)
    assert len(metadata.sha256) == 64


def test_storage_preserves_original_bytes(tmp_path):
    storage = LocalStorage(tmp_path)

    data = b"ORIGINAL_DDD_CONTENT"

    metadata = storage.save(
        data=data,
        filename="CARD_002_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    saved_path = tmp_path / metadata.filename

    assert saved_path.exists()
    assert saved_path.read_bytes() == data


def test_storage_generates_different_file_ids(tmp_path):
    storage = LocalStorage(tmp_path)

    data = b"SIMULATED_DDD_DATA"

    first = storage.save(
        data=data,
        filename="FIRST.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    second = storage.save(
        data=data,
        filename="SECOND.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    assert first.file_id != second.file_id

def test_storage_rejects_path_traversal(tmp_path):
    storage = LocalStorage(tmp_path)

    try:
        storage.save(
            data=b"ATTACK_DATA",
            filename="..\\outside.DDD",
            source_type=SourceType.DRIVER_CARD,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Se ha permitido una ruta fuera del almacenamiento"
        )


def test_storage_rejects_absolute_path(tmp_path):
    storage = LocalStorage(tmp_path)

    try:
        storage.save(
            data=b"ATTACK_DATA",
            filename="C:\\outside.DDD",
            source_type=SourceType.DRIVER_CARD,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Se ha permitido una ruta absoluta"
        )


def test_storage_persists_file_metadata(tmp_path):
    storage = LocalStorage(tmp_path)

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="CARD_001_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    second_storage = LocalStorage(tmp_path)

    restored = second_storage.get_metadata(
        metadata.file_id
    )

    assert restored is not None
    assert restored.file_id == metadata.file_id
    assert restored.filename == metadata.filename
    assert restored.size_bytes == metadata.size_bytes
    assert restored.sha256 == metadata.sha256


def test_storage_persists_original_hash_after_file_is_modified(tmp_path):
    storage = LocalStorage(tmp_path)

    metadata = storage.save(
        data=b"ORIGINAL_DDD_DATA",
        filename="CARD_001_20260830.DDD",
        source_type=SourceType.DRIVER_CARD,
    )

    path = tmp_path / metadata.filename
    path.write_bytes(b"MODIFIED_DDD_DATA")

    restored = storage.get_metadata(
        metadata.file_id
    )

    assert restored is not None
    assert restored.sha256 == metadata.sha256
    assert restored.sha256 != "MODIFIED_DDD_DATA"