from abc import ABC, abstractmethod

class TachographHardwareInterface(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Establece conexión con el lector."""
        pass

    @abstractmethod
    def read_driver_card(self) -> bytes:
        """Lee los datos de la tarjeta de conducción."""
        pass

    @abstractmethod
    def read_vehicle_unit(self) -> bytes:
        """Lee los datos del tacógrafo."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Cierra la conexión."""
        pass