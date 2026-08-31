from datetime import date
from pathlib import Path

from simulator.application import TachographApplication
from simulator.card.driver_card import DriverCard


def main():
    print("=" * 50)
    print("       TACHO-DOWN SIMULATOR V1")
    print("=" * 50)
    print()

    storage_path = Path("data")

    app = TachographApplication(
        storage_path=storage_path,
        server_online=True,
    )

    card = DriverCard(
        card_number="DEMO-CARD-001",
        driver_id="DEMO-DRIVER-001",
        issuing_country="ES",
        valid_from=date(2026, 1, 1),
        valid_until=date(2030, 12, 31),
    )

    print(f"Estado inicial: {app.device.state.value}")
    print()

    print("Insertando tarjeta...")
    app.reader.insert_card(card)

    print("Detectando tarjeta...")
    app.device.detect_card()

    print("Ejecutando descarga...")
    operation = app.device.download_card()

    print()
    print(f"Operación: {operation.operation_id}")
    print(f"Estado: {operation.status.value}")
    print(f"Archivo: {operation.file_id}")
    print(f"Sincronización: {operation.sync_status}")

    print()
    print(f"Estado final: {app.device.state.value}")

    print()
    print("Archivos locales:")

    for path in storage_path.glob("*.DDD"):
        print(f"  - {path}")

    print()
    print("Operaciones registradas:")

    for operation in app.operation_log.all():
        print(
            f"  - {operation['operation_type']}: "
            f"{operation['status']}"
        )

    print()
    print("SIMULADOR: OK")


if __name__ == "__main__":
    main()