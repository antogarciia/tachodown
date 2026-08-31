from simulator.tachograph.interface import TachographInterface


class TachographError(Exception):
    """Error relacionado con el tacógrafo simulado."""


class SimulatedTachograph(TachographInterface):
    """Tacógrafo simulado para pruebas de laboratorio."""

    def __init__(
        self,
        data: bytes = b"SIMULATED_TACHOGRAPH_DATA",
        tachograph_id: str = "TACHO-001",
        vehicle_id: str = "VEHICLE-001",
        vehicle_registration: str = "1234-ABC",
    ):
        self.tachograph_id = tachograph_id
        self.vehicle_id = vehicle_id
        self.vehicle_registration = vehicle_registration

        self.connected = False
        self.authenticated = False
        self._data = data

    def connect(self) -> None:
        if self.connected:
            raise TachographError(
                "El tacógrafo ya está conectado"
            )

        self.connected = True

    def authenticate(self) -> None:
        if not self.connected:
            raise TachographError(
                "No se puede autenticar sin conexión"
            )

        self.authenticated = True

    def download(self) -> bytes:
        if not self.connected:
            raise TachographError(
                "No se puede descargar sin conexión"
            )

        if not self.authenticated:
            raise TachographError(
                "No se puede descargar sin autenticación"
            )

        return bytes(self._data)

    def disconnect(self) -> None:
        self.connected = False
        self.authenticated = False

