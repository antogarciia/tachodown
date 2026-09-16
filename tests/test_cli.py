from datetime import date

from simulator.card.driver_card import DriverCard
from simulator.cli import TachographCLI
from simulator.metadata.models import OperationStatus


def create_card() -> DriverCard:
    return DriverCard(
        card_number="CARD-001",
        driver_id="DRIVER-001",
        issuing_country="ES",
        valid_from=date(2025, 1, 1),
        valid_until=date(2030, 12, 31),
    )


def test_cli_download_card_creates_file(tmp_path, monkeypatch):
    cli = TachographCLI(tmp_path)

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "CARD-001",
    )

    cli._download_card()

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 1


def test_cli_download_tachograph_creates_file(tmp_path, capsys):
    cli = TachographCLI(tmp_path)

    cli._download_tachograph()

    files = list(tmp_path.glob("*.DDD"))

    assert len(files) == 1

    output = capsys.readouterr().out

    assert "Estado:    COMPLETED" in output


def test_cli_verify_file_uses_file_service(tmp_path, monkeypatch, capsys):
    cli = TachographCLI(tmp_path)

    operation = cli.app.download_card(
        create_card()
    )

    assert operation.status == OperationStatus.COMPLETED
    assert operation.file_id is not None

    monkeypatch.setattr(
        "builtins.input",
        lambda _: operation.file_id,
    )

    cli._verify_file()

    output = capsys.readouterr().out

    assert "Archivo íntegro" in output


def test_cli_list_files_shows_registered_file(
    tmp_path,
    capsys,
):
    cli = TachographCLI(tmp_path)

    operation = cli.app.download_card(
        create_card()
    )

    assert operation.status == OperationStatus.COMPLETED

    cli._list_files()

    output = capsys.readouterr().out

    assert operation.file_id in output
    assert ".DDD" in output