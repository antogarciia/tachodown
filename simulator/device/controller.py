from enum import Enum

from simulator.metadata.models import (
    OperationStatus,
    SyncStatus,
)


class DeviceState(Enum):
    IDLE = "IDLE"
    CARD_DETECTED = "CARD_DETECTED"
    AUTHENTICATING = "AUTHENTICATING"
    DOWNLOADING = "DOWNLOADING"
    VERIFYING = "VERIFYING"
    STORED_LOCAL = "STORED_LOCAL"
    SYNC_PENDING = "SYNC_PENDING"
    SYNCED = "SYNCED"
    ERROR = "ERROR"


ALLOWED_TRANSITIONS = {
    DeviceState.IDLE: {
        DeviceState.CARD_DETECTED,
    },
    DeviceState.CARD_DETECTED: {
        DeviceState.AUTHENTICATING,
        DeviceState.ERROR,
    },
    DeviceState.AUTHENTICATING: {
        DeviceState.DOWNLOADING,
        DeviceState.ERROR,
    },
    DeviceState.DOWNLOADING: {
        DeviceState.VERIFYING,
        DeviceState.ERROR,
    },
    DeviceState.VERIFYING: {
        DeviceState.STORED_LOCAL,
        DeviceState.ERROR,
    },
    DeviceState.STORED_LOCAL: {
        DeviceState.SYNC_PENDING,
    },
    DeviceState.SYNC_PENDING: {
        DeviceState.SYNCED,
        DeviceState.ERROR,
    },
    DeviceState.SYNCED: {
        DeviceState.IDLE,
    },
    DeviceState.ERROR: {
        DeviceState.IDLE,
    },
}


class InvalidTransition(Exception):
    """Error producido por una transición de estado no permitida."""


class DeviceController:

    def __init__(
        self,
        reader=None,
        download_service=None,
    ):
        self.state = DeviceState.IDLE
        self.card = None

        self.reader = reader
        self.download_service = download_service

        self.last_operation = None

    def detect_card(self, card=None):
        """Registra una tarjeta detectada por el lector."""

        if self.state != DeviceState.IDLE:
            raise InvalidTransition(
                f"No se puede detectar una tarjeta desde "
                f"{self.state.value}"
            )

        if card is None and self.reader is not None:
            card = self.reader.read_card()

        if card is None:
            raise ValueError(
                "No hay ninguna tarjeta disponible"
            )

        self.card = card
        self.transition_to(DeviceState.CARD_DETECTED)

    def download_card(self):
        """
        Ejecuta el flujo de descarga de una tarjeta.

        El servicio de descarga se encarga del almacenamiento y
        sincronización. El controlador gobierna los estados.
        """

        if self.download_service is None:
            raise RuntimeError(
                "No hay servicio de descarga configurado"
            )

        if self.state != DeviceState.CARD_DETECTED:
            raise InvalidTransition(
                f"No se puede iniciar una descarga desde "
                f"{self.state.value}"
            )

        try:
            self.transition_to(DeviceState.AUTHENTICATING)
            self.transition_to(DeviceState.DOWNLOADING)

            operation = self.download_service.download()
            self.last_operation = operation

            if operation.status == OperationStatus.FAILED:
                self.transition_to(DeviceState.ERROR)
                return operation

            self.transition_to(DeviceState.VERIFYING)
            self.transition_to(DeviceState.STORED_LOCAL)

            if operation.sync_status == SyncStatus.SYNCED:
                self.transition_to(DeviceState.SYNC_PENDING)
                self.transition_to(DeviceState.SYNCED)
                self.transition_to(DeviceState.IDLE)
            else:
                self.transition_to(DeviceState.SYNC_PENDING)

            return operation

        except Exception:
            if self.state != DeviceState.ERROR:
                allowed_states = ALLOWED_TRANSITIONS.get(
                    self.state,
                    set(),
                )

                if DeviceState.ERROR in allowed_states:
                    self.transition_to(DeviceState.ERROR)

            raise

    def reset(self) -> None:
        """Devuelve el dispositivo al estado IDLE."""

        if self.state not in {
            DeviceState.ERROR,
            DeviceState.SYNCED,
            DeviceState.IDLE,
        }:
            raise InvalidTransition(
                f"No se puede reiniciar desde "
                f"{self.state.value}"
            )

        if self.reader is not None:
            self.reader.remove_card()

        self.state = DeviceState.IDLE

        self.card = None
        self.last_operation = None

    def transition_to(self, new_state):
        """Realiza una transición validada de estado."""

        allowed_states = ALLOWED_TRANSITIONS.get(
            self.state,
            set(),
        )

        if new_state not in allowed_states:
            raise InvalidTransition(
                f"Transición no permitida: "
                f"{self.state.value} -> {new_state.value}"
            )

        print(
            f"[STATE] "
            f"{self.state.value} -> {new_state.value}"
        )

        self.state = new_state