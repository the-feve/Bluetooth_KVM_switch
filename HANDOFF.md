# Handoff

## Current state (2026-10-17)

- First version written in a cloud session: daemon, installer, systemd unit, docs, tests.
- **Not yet run on hardware.** 12 unit tests pass (key tables, reports, hotkeys,
  switching, control channel). The Bluetooth/D-Bus parts are untested.
- Target: Raspberry Pi 4 Model B (the owner's unit), Raspberry Pi OS Lite 64-bit,
  Keeb.io Sinc Rev. 4 (QMK/VIA).

- Website: project page https://fevergeon.com/cad-software/bluetooth-kvm/ and the
  first-time build guide …/guide/ (interactive diagrams), both in the-feve/fevergeon-site.
  The owner is new to Raspberry Pi; update the guide as each step is done on hardware.
- The repo's default branch is `claude/festive-hopper-swypfc` (it was the first push to an
  empty repo), so a plain `git clone` gets the code. Renaming it to `main` later is fine;
  the guide links use `HEAD`.

## Code map

- `bt_kvm/hid.py`: report descriptor, SDP record, evdev→HID tables, `KeyState`,
  `Hotkeys`. No Bluetooth, so it can be tested anywhere.
- `bt_kvm/main.py`: the `Kvm` daemon (asyncio). It handles the BlueZ agent and profile
  over D-Bus (dbus-next), the L2CAP 0x11/0x13 sockets, slots and switching, the evdev
  grab with hotplug polling, and the gpiozero button and LEDs.
- `install.sh`, `systemd/bt-kvm.service`, `config.example.json`.
- Runtime files: `/etc/bt-kvm/config.json`, `/var/lib/bt-kvm/state.json` (slots plus
  the active slot).

## Decisions

- **Bluetooth Classic HID, not BLE (HOGP).** Classic is simpler in BlueZ, works on
  Windows 10/11, and reconnects can be started from the Pi. `ControllerMode = bredr`.
- **Rebuild reports from evdev** instead of forwarding USB reports: QMK exposes
  several interfaces and NKRO, and hosts only understand our SDP descriptor.
  Reports are 6-key with ErrorRollOver.
- **Both hosts stay connected; only the active one gets reports.** Switching is
  instant when both are connected. Otherwise the Pi dials the host
  (HIDReconnectInitiate=true).
- **Pairing only in pairing mode** (agent rejects otherwise; Pairable/Discoverable off).
  A new host fills the active slot and removes that slot's old pairing.
- On switch: send "all up" to the old host, and hide keys still held from the new
  host (`KeyState.switched_host`).
- Keyboard-page Power (0x66) is never forwarded; QMK system and mouse keys are dropped.
- Pi 4 over Zero 2 W: the owner has one, it has USB-A host ports (no OTG adapter or
  splitter), and it's desk-powered anyway.
- Separate box, not built into the split keyboard (see docs/enclosure.md).
- **Both box ports are USB-C** (owner, 2026-10-17). Option A (recommended): the Pi's own
  USB-C power port in the front wall, plus a USB-C(f)→USB-A(m) adapter in a black USB 2.0
  port, flush with the side wall and held by a printed collar. Option B: panel-mount
  extensions. Ports labelled and on different walls, because the keyboard port isn't a
  power input. The Sinc uses a C-to-C cable.
- Owner's hardware: a Vilros Pi 4 kit (4 GB Pi, 5.1 V 3 A switched supply, Vilros case
  with fan, SD card). The Vilros case is the stand-in until a custom case exists.

## Next steps

See TODO.md. The first job is hardware bring-up on the Pi 4, pairing with a Windows PC.
