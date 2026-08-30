from abc import ABC, abstractmethod


class TachographInterface(ABC):
    """Interfaz abstracta para comunicación con un tacógrafo."""

    @abstractmethod
    def connect(self) -> None:
        """Establece la conexión con el tacógrafo."""
        raise NotImplementedError

    @abstractmethod
    def authenticate(self) -> None:
        """Realiza el proceso de autenticación."""
        raise NotImplementedError

    @abstractmethod
    def download(self) -> bytes:
        """Descarga los datos del tacógrafo."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """Cierra la conexión con el tacógrafo."""
        raise NotImplementedError