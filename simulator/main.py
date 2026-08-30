from enum import Enum


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
    pass


class DeviceController:

    def __init__(self):
        self.state = DeviceState.IDLE

    def transition_to(self, new_state):

        allowed_states = ALLOWED_TRANSITIONS.get(
            self.state,
            set()
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


def main():

    print("=" * 50)
    print("       TACHO-DOWN SIMULATOR V1")
    print("=" * 50)
    print()

    device = DeviceController()

    print(
        f"Estado inicial: "
        f"{device.state.value}"
    )

    print()

    device.transition_to(DeviceState.CARD_DETECTED)
    device.transition_to(DeviceState.AUTHENTICATING)
    device.transition_to(DeviceState.DOWNLOADING)
    device.transition_to(DeviceState.VERIFYING)
    device.transition_to(DeviceState.STORED_LOCAL)
    device.transition_to(DeviceState.SYNC_PENDING)
    device.transition_to(DeviceState.SYNCED)

    print()

    print(
        f"Estado final: "
        f"{device.state.value}"
    )

    print()
    print("SIMULADOR: OK")


if __name__ == "__main__":
    main()