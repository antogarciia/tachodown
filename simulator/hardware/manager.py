from .interface import TachographHardwareInterface

class DownloadManager:
    def __init__(self, hardware: TachographHardwareInterface):
        # Inyectamos la dependencia: el manager no sabe si es real o simulado
        self.hardware = hardware

    def run_driver_card_download(self):
        print("\n[MANAGER] Iniciando flujo de descarga de tarjeta...")
        if not self.hardware.connect():
            print("[MANAGER] Error: No se pudo conectar al lector.")
            return None

        try:
            data = self.hardware.read_driver_card()
            print(f"[MANAGER] Descarga completada. Bytes recuperados: {len(data)}")
            # Aquí es donde inyectaremos tu lógica de parseo actual
            return data
        except Exception as e:
            print(f"[MANAGER] Error durante la lectura: {e}")
        finally:
            self.hardware.disconnect()