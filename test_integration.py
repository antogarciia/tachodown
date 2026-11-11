from simulator.hardware.simulator import SimulatedTachographReader
from simulator.hardware.manager import DownloadManager

def run_integration():
    print("--- INICIANDO INTEGRACIÓN CON SIMULADOR ---")
    
    # 1. Instanciamos el lector falso
    simulated_reader = SimulatedTachographReader()
    
    # 2. Se lo pasamos al manager (Inyección de dependencias)
    manager = DownloadManager(hardware=simulated_reader)
    
    # 3. Ejecutamos el flujo de descarga
    downloaded_bytes = manager.run_driver_card_download()
    
    if downloaded_bytes:
        print("--- INTEGRACIÓN EXITOSA ---")
        print("Los datos están listos para ser parseados por tu código actual.")
    else:
        print("--- FALLO EN LA INTEGRACIÓN ---")

if __name__ == "__main__":
    run_integration()