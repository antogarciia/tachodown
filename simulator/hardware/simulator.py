from .interface import TachographHardwareInterface
import os

class SimulatedTachographReader(TachographHardwareInterface):
    def __init__(self, dummy_file_path: str = "dummy.ddd"):
        self.dummy_file_path = dummy_file_path
        self.is_connected = False

    def connect(self) -> bool:
        print("[SIM] Conectando al hardware simulado...")
        self.is_connected = True
        return True

    def read_driver_card(self) -> bytes:
        if not self.is_connected:
            raise ConnectionError("Dispositivo no conectado.")
        
        print("[SIM] Leyendo tarjeta de conducción...")
        if os.path.exists(self.dummy_file_path):
            print(f"[SIM] Archivo {self.dummy_file_path} encontrado. Leyendo...")
            with open(self.dummy_file_path, "rb") as f:
                return f.read()
        else:
            print("[SIM] Archivo no encontrado. Generando bytes de prueba...")
            # Bloque de bytes falso simulando un archivo .ddd
            return b"\x00\x01\x02_DUMMY_CARD_DATA_\x03\x04"

    def read_vehicle_unit(self) -> bytes:
        if not self.is_connected:
            raise ConnectionError("Dispositivo no conectado.")
        print("[SIM] Descargando datos del tacógrafo...")
        return b"\x00_DUMMY_VU_DATA_\x00"

    def disconnect(self) -> None:
        print("[SIM] Desconectando hardware simulado...")
        self.is_connected = False