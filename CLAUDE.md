# Bluetooth_KVM_switch (bt-kvm) — working rules

- Read `HANDOFF.md` first, then `TODO.md`. Keep both up to date when something changes.
- Hardware: Raspberry Pi 4 Model B + Keeb.io Sinc Rev. 4. Hosts are Windows PCs; the work PC allows Bluetooth but no software installs, so everything must work as a plain Bluetooth keyboard.
- Never log keystrokes (work passwords pass through this device).
- Keep `bt_kvm/hid.py` free of Bluetooth/D-Bus so it stays testable anywhere.
- Run `python -m pytest -q` before every push (needs `evdev`, `dbus-next`, `pytest`; a few seconds).
- Budget is tight: zero running cost, batch changes, develop on a branch, open a PR only when asked.
