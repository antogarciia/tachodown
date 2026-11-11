from abc import ABC, abstractmethod

from simulator.card.driver_card import DriverCard


class CardReaderInterface(ABC):
    """
    Interfaz para cualquier lector de tarjetas de conductor.

    La implementación puede ser simulada o corresponder
    a un lector de hardware real.
    """

    @abstractmethod
    def insert_card(self, card: DriverCard) -> None:
        """
        Inserta o detecta una tarjeta.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_card(self) -> None:
        """
        Retira la tarjeta del lector.
        """
        raise NotImplementedError

    @abstractmethod
    def is_card_inserted(self) -> bool:
        """
        Indica si hay una tarjeta insertada.
        """
        raise NotImplementedError

    @abstractmethod
    def read_card(self) -> DriverCard | None:
        """
        Devuelve la tarjeta insertada, si existe.
        """
        raise NotImplementedError