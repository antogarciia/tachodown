from simulator.card.driver_card import DriverCard


class CardReader:
    """Lector de tarjetas simulado."""

    def __init__(self):
        self._card = None

    def insert_card(self, card: DriverCard) -> None:
        """Simula la inserción de una tarjeta."""

        if self._card is not None:
            raise ValueError(
                "Ya hay una tarjeta insertada"
            )

        if card is None:
            raise ValueError(
                "La tarjeta no puede ser None"
            )

        self._card = card

    def remove_card(self) -> None:
        """Simula la retirada de la tarjeta."""

        self._card = None

    def is_card_inserted(self) -> bool:
        """Indica si hay una tarjeta insertada."""

        return self._card is not None

    def read_card(self) -> DriverCard | None:
        """Devuelve la tarjeta insertada, si existe."""

        return self._card