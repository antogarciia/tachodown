from datetime import date
from pathlib import Path

from simulator.application import TachographApplication
from simulator.card.driver_card import DriverCard
from simulator.files.service import FileService
from simulator.metadata.models import OperationStatus


class TachographCLI:
    def __init__(self, storage_path: Path):
        self.app = TachographApplication(
            storage_path=storage_path,
        )

        self.file_service = FileService(
            storage_path=storage_path,
            operation_log=self.app.operation_log,
        )

    def run(self) -> None:
        while True:
            self._print_menu()

            option = input("Selecciona una opción: ").strip()

            if option == "1":
                self._download_card()
            elif option == "2":
                self._download_tachograph()
            elif option == "3":
                self._list_files()
            elif option == "4":
                self._verify_file()
            elif option == "5":
                self._show_operations()
            elif option == "6":
                self._sync_pending()
            elif option == "7":
                print("\nSaliendo de TACHO-DOWN...")
                break
            else:
                print("\nOpción no válida.")

            input("\nPulsa ENTER para continuar...")

    @staticmethod
    def _print_menu() -> None:
        print()
        print("=" * 50)
        print("              TACHO-DOWN BETA")
        print("=" * 50)
        print("1. Descargar tarjeta")
        print("2. Descargar tacógrafo")
        print("3. Ver archivos")
        print("4. Verificar archivo")
        print("5. Ver operaciones")
        print("6. Sincronizar pendientes")
        print("7. Salir")
        print("=" * 50)

    def _download_card(self) -> None:
        print("\n--- DESCARGA DE TARJETA ---")

        card_number = input(
            "Número de tarjeta [CARD-001]: "
        ).strip()

        if not card_number:
            card_number = "CARD-001"

        card = DriverCard(
            card_number=card_number,
            driver_id="DRIVER-001",
            issuing_country="ES",
            valid_from=date(2025, 1, 1),
            valid_until=date(2030, 12, 31),
        )

        try:
            operation = self.app.download_card(card)
        except Exception as exc:
            print(f"\nError: {exc}")
            return

        self._print_operation_result(operation)

    def _download_tachograph(self) -> None:
        print("\n--- DESCARGA DE TACÓGRAFO ---")

        try:
            self.app.tachograph.connect()
            self.app.tachograph.authenticate()

            operation = self.app.download_tachograph()

        except Exception as exc:
            print(f"\nError: {exc}")
            return

        finally:
            if self.app.tachograph.connected:
                self.app.tachograph.disconnect()

        self._print_operation_result(operation)

    def _list_files(self) -> None:
        print("\n--- ARCHIVOS DDD ---")

        files = self.file_service.list_files()

        if not files:
            print("No hay archivos registrados.")
            return

        for metadata in files:
            print()
            print(f"ID:       {metadata.file_id}")
            print(f"Nombre:   {metadata.filename}")
            print(f"Origen:   {metadata.source_type.value}")
            print(f"Tamaño:   {metadata.size_bytes} bytes")
            print(f"SHA-256:  {metadata.sha256}")
            print(f"Creado:   {metadata.created_at}")

    def _verify_file(self) -> None:
        print("\n--- VERIFICAR ARCHIVO ---")

        file_id = input(
            "File ID: "
        ).strip()

        if not file_id:
            print("Debes indicar un File ID.")
            return

        valid = self.file_service.verify_file(
            file_id
        )

        if valid:
            print("\n✓ Archivo íntegro.")
        else:
            print(
                "\n✗ El archivo no existe, no está registrado "
                "o ha sido modificado."
            )

    def _show_operations(self) -> None:
        print("\n--- HISTORIAL DE OPERACIONES ---")

        operations = self.app.operation_log.all()

        if not operations:
            print("No hay operaciones registradas.")
            return

        for operation in operations:
            print()
            print(
                f"[{operation.get('timestamp')}] "
                f"{operation.get('operation_type')}"
            )
            print(
                f"  ID:       {operation.get('operation_id')}"
            )
            print(
                f"  Estado:   {operation.get('status')}"
            )

            if operation.get("file_id"):
                print(
                    f"  Archivo:  {operation.get('file_id')}"
                )

            if operation.get("card_number"):
                print(
                    f"  Tarjeta:  {operation.get('card_number')}"
                )

            if operation.get("vehicle_registration"):
                print(
                    f"  Vehículo: "
                    f"{operation.get('vehicle_registration')}"
                )

            if operation.get("sync_status"):
                print(
                    f"  Sync:     "
                    f"{operation.get('sync_status')}"
                )

            if operation.get("error_message"):
                print(
                    f"  Error:    "
                    f"{operation.get('error_message')}"
                )

    def _sync_pending(self) -> None:
        print("\n--- SINCRONIZACIÓN ---")

        try:
            results = self.app.sync_pending()
        except Exception as exc:
            print(f"\nError durante la sincronización: {exc}")
            return

        if not results:
            print("No hay operaciones pendientes.")
            return

        completed = 0
        failed = 0

        for operation in results:
            if operation.status == OperationStatus.COMPLETED:
                completed += 1
            else:
                failed += 1

        print()
        print(f"Operaciones sincronizadas: {completed}")

        if failed:
            print(f"Operaciones con error:     {failed}")

    @staticmethod
    def _print_operation_result(operation) -> None:
        print()

        print(
            f"Operación: {operation.operation_id}"
        )

        print(
            f"Tipo:      {operation.operation_type.value}"
        )

        print(
            f"Estado:    {operation.status.value}"
        )

        if operation.file_id:
            print(
                f"Archivo:   {operation.file_id}"
            )

        if operation.sync_status:
            print(
                f"Sync:      {operation.sync_status.value}"
            )

        if operation.error_message:
            print(
                f"Error:     {operation.error_message}"
            )


def main() -> None:
    storage_path = Path("data")

    cli = TachographCLI(
        storage_path=storage_path,
    )

    cli.run()


if __name__ == "__main__":
    main()