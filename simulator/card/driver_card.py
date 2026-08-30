from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DriverCard:
    """
    Modelo abstracto de una tarjeta de conductor para simulación.

    No contiene credenciales, claves privadas ni datos reales.
    """

    card_number: str
    driver_id: str
    issuing_country: str
    valid_from: date
    valid_until: date

    def is_valid_on(self, check_date: date) -> bool:
        """Comprueba si la tarjeta es válida en una fecha determinada."""
        return self.valid_from <= check_date <= self.valid_until