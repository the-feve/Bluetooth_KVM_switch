# TODO

## Hardware bring-up (first)
- [ ] Install on the Pi 4, then check `bluetoothctl show` reports class ...540 and the log shows the Sinc interfaces.
- [ ] Pair the personal PC (Windows): confirm Just Works pairing (no PIN prompt) and that typing works.
- [ ] Pair the work PC; confirm switching both ways, with both connected and with one asleep (Pi-initiated reconnect).
- [ ] Caps Lock LED follows the active host.
- [ ] Media keys (volume, play/pause) work on both.
- [ ] Measure the time from switching until the first keystroke lands, for both the connected and reconnect cases.
- [ ] Reboot test: hosts reconnect by themselves after the Pi reboots.

## Website guide (fevergeon.com/cad-software/bluetooth-kvm/guide/)
- [ ] As each step works on the Pi, remove its "not yet tested" badge and add photos or screenshots (Imager screens, first SSH login, Windows pairing, the wiring).
- [ ] Add the enclosure as a guide step once the CAD exists (interactive exploded view or annotated renders).

- [ ] Buy the USB-C→A adapter (data-capable) and a C-to-C cable for the Sinc; measure the adapter for the collar.

## Later
- [ ] Enclosure CAD (Pi 4 box, panel USB-A and USB-C, button, two LEDs); dimensions are in docs/enclosure.md. Print fit coupons first.
- [ ] Keep pairings when the read-only overlay is on (bind-mount /var/lib/bluetooth and /var/lib/bt-kvm onto a small writable partition).
- [ ] Optional: forward QMK mouse keys (add a mouse report to the descriptor).
- [ ] Optional: a third "wired" target via USB gadget mode on the Pi 4's USB-C (would need power through GPIO).
- [ ] dbus-next uses `typing.no_type_check_decorator`, which goes away in Python 3.15; watch for that when Pi OS moves past 3.13.
