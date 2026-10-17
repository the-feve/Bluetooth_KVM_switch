# Bluetooth_KVM_switch (bt-kvm) — working rules

- Read `HANDOFF.md` first, then `TODO.md`. Keep both up to date when something changes.
- **Document as we go, for a first-time Raspberry Pi user.** The owner is new to the Pi. Every step goes into the website build guide, https://fevergeon.com/cad-software/bluetooth-kvm/guide/ (source: `src/pages/cad-software/bluetooth-kvm/guide.astro` in the-feve/fevergeon-site; it goes live from `main`). Use interactive diagrams plus plain-language descriptions to explain steps, say what the user should see and what to do if they don't, and mark steps not yet confirmed on hardware. Keep its commands in step with README.md and install.sh.
- Hardware: Raspberry Pi 4 Model B + Keeb.io Sinc Rev. 4. Hosts are Windows PCs; the work PC allows Bluetooth but no software installs, so everything must work as a plain Bluetooth keyboard.
- Never log keystrokes (work passwords pass through this device).
- Keep `bt_kvm/hid.py` free of Bluetooth/D-Bus so it stays testable anywhere.
- Run `python -m pytest -q` before every push (needs `evdev`, `dbus-next`, `pytest`; a few seconds).
- Budget is tight: zero running cost, batch changes, develop on a branch, open a PR only when asked.
