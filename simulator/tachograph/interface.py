from abc import ABC, abstractmethod


class TachographInterface(ABC):
    """
    Interfaz común para tacógrafos simulados o físicos.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Establece la conexión con el tacógrafo.
        """
        raise NotImplementedError

    @abstractmethod
    def authenticate(self) -> None:
        """
        Autentica el dispositivo o la sesión de acceso.
        """
        raise NotImplementedError

    @abstractmethod
    def download(self) -> bytes:
        """
        Descarga los datos del tacógrafo.
        """
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """
        Cierra la conexión con el tacógrafo.
        """
        raise NotImplementedError