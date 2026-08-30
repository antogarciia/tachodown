from simulator.device.controller import DeviceController, DeviceState


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