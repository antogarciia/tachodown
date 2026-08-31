import hashlib

import pytest

from simulator.server.simulator import ServerError, SimulatedServer


def test_server_starts_online():
    server = SimulatedServer()

    assert server.online is True


def test_server_can_upload_file():
    server = SimulatedServer()

    data = b"ORIGINAL_DDD_DATA"
    sha256 = hashlib.sha256(data).hexdigest()

    uploaded = server.upload(
        file_id="FILE-000001",
        filename="TEST.DDD",
        data=data,
        sha256=sha256,
    )

    assert uploaded.file_id == "FILE-000001"
    assert uploaded.filename == "TEST.DDD"
    assert uploaded.data == data
    assert uploaded.sha256 == sha256


def test_server_preserves_original_bytes():
    server = SimulatedServer()

    data = b"ORIGINAL_DDD_DATA"
    sha256 = hashlib.sha256(data).hexdigest()

    server.upload(
        file_id="FILE-000001",
        filename="TEST.DDD",
        data=data,
        sha256=sha256,
    )

    stored = server.get_file("FILE-000001")

    assert stored is not None
    assert stored.data == data
    assert hashlib.sha256(stored.data).hexdigest() == sha256


def test_server_rejects_duplicate_file():
    server = SimulatedServer()

    data = b"ORIGINAL_DDD_DATA"
    sha256 = hashlib.sha256(data).hexdigest()

    server.upload(
        file_id="FILE-000001",
        filename="TEST.DDD",
        data=data,
        sha256=sha256,
    )

    with pytest.raises(ServerError):
        server.upload(
            file_id="FILE-000001",
            filename="TEST2.DDD",
            data=b"OTHER_DATA",
            sha256=hashlib.sha256(b"OTHER_DATA").hexdigest(),
        )


def test_server_rejects_upload_when_offline():
    server = SimulatedServer()
    server.online = False

    with pytest.raises(ServerError):
        server.upload(
            file_id="FILE-000001",
            filename="TEST.DDD",
            data=b"DATA",
            sha256=hashlib.sha256(b"DATA").hexdigest(),
        )