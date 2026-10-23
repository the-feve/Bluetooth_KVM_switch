# Bluetooth KVM switch (bt-kvm)

A Raspberry Pi 4 that takes a wired USB keyboard (a Keeb.io Sinc Rev. 4) and a USB
mouse, and passes them on over Bluetooth to two computers. Each has its own button on
the front: a press moves that device to the other computer, the way a multi-device
NuPhy keyboard swaps, and a long hold pairs. So the keyboard can be on the work PC
while the mouse stays on the personal one, or both can move together. The computers
just see an ordinary Bluetooth keyboard and mouse, so nothing has to be installed on
them. That matters for a locked-down work PC.

```
 Sinc (USB) ──┐                                  ┌► Host 1 (personal PC)
              ├► Pi 4 ──► bt-kvm ──► Bluetooth ──┤
 Mouse (USB) ─┘     ▲                            └► Host 2 (work PC)
        front buttons: [Keyboard 1|2]  [Mouse 1|2]   (also Fn keys / a Ctrl chord)
```

**Status:** the code passes its unit tests but has not been run on real hardware yet.
See [TODO.md](TODO.md) for what still needs checking.

**New to Raspberry Pi? Start with the illustrated, step-by-step build guide:
https://fevergeon.com/cad-software/bluetooth-kvm/guide/** It covers flashing the SD
card, connecting over SSH, pairing both PCs and wiring the button, with interactive
diagrams. This README is the shorter technical version.

- [docs/hardware.md](docs/hardware.md): which Pi to use, what to buy, wiring
- [docs/enclosure.md](docs/enclosure.md): Pi 4 dimensions, port layout, case rules
- [docs/stompbox.md](docs/stompbox.md): planned add-on, a foot pedal that mirrors the two front buttons
- [HANDOFF.md](HANDOFF.md): how the code works, and the decisions behind it

## How it works

- **Input:** the Pi reads the keyboard and mouse through Linux `evdev` and *grabs*
  them, so the Pi's own console never sees your input. Anything that moves a pointer
  counts as the mouse; anything with keys counts as the keyboard. (QMK keyboards show
  up as several devices, and a QMK mouse-keys interface follows the mouse button.)
  Wired mice and wireless ones with a USB dongle both work.
- **Output:** the Pi registers with BlueZ as one **Bluetooth Classic HID device**
  with a keyboard, media keys and a mouse (5 buttons, 16-bit movement, wheel and
  horizontal wheel), so each computer pairs once. It handles the two HID L2CAP
  channels itself: control on PSM 0x11 and interrupt on 0x13. Reports are rebuilt
  from the input events rather than copied from USB, because the host only
  understands the descriptor we advertised. Mouse movement is batched to one report
  every 8 ms (about what a Bluetooth link carries) and clicks go out at once.
- **Two hosts, two channels:** each computer is stored in a *slot*, 1 or 2, and both
  can stay connected. The keyboard and the mouse each point at a slot on their own.
  Switching to a connected computer is instant; otherwise the Pi connects to it,
  which takes about 1–3 s. Before switching, the old computer gets "all keys up" or
  "buttons up", so nothing gets stuck, and the keys you held to switch are hidden
  from the new one until you let go of them.
- **Caps/Num Lock LEDs** follow the computer the keyboard is on.
- **Pairing** is allowed only in pairing mode (2 minutes, or until a host pairs). The
  new computer goes into the active slot and replaces whatever was in it.

## Controls

| Action | Front button | Fn-layer key (set in VIA) | Chord, works with any keyboard |
|---|---|---|---|
| Keyboard to the other computer | **Keyboard** button, short press | `F21` (host 1) / `F22` (host 2) | hold **both Ctrls** + `1` / `2` |
| Mouse to the other computer | **Mouse** button, short press | `F19` (host 1) / `F20` (host 2) | hold **both Ctrls** + `3` / `4` |
| Pair a new computer (again to cancel) | either button, **hold 3 s** | `F23` | hold **both Ctrls** + `0` |

A long hold pairs the computer slot that button's device is on, so to pair host 2,
first switch to it with a short press. The computers never see F19–F23 or the chord
keys. You can change any of these in `/etc/bt-kvm/config.json` (actions: `host1`,
`host2`, `mouse1`, `mouse2`, `both1`, `both2`, `kb_toggle`, `mouse_toggle`, `pair`).

Each button has two LEDs beside it, one per computer: **solid** = the device is on
that computer and connected · **slow blink** = on that computer, not connected ·
**fast blink** = pairing that slot · **off** = on the other computer.

## Setup, step by step

### 1. Flash the SD card

Use Raspberry Pi Imager and pick **Raspberry Pi OS Lite (64-bit)**. Then click the
gear icon (OS customisation) and set:
hostname `bt-kvm`, enable SSH, your username and password, and your Wi-Fi (or use
Ethernet).

### 2. First boot and updates

```bash
ssh <you>@bt-kvm.local
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git
sudo reboot
```

### 3. Install bt-kvm

```bash
git clone https://github.com/the-feve/Bluetooth_KVM_switch.git
cd Bluetooth_KVM_switch
sudo ./install.sh
```

`install.sh` does the following. Each step can also be done by hand:

1. Installs `bluez python3-evdev python3-dbus-next python3-gpiozero python3-lgpio`.
2. Copies `bt_kvm/` to `/opt/bt-kvm/`, and `config.example.json` to
   `/etc/bt-kvm/config.json` if that file doesn't exist yet.
3. **Turns off BlueZ's `input` plugin** with a systemd override, so the Pi can own the
   HID channels:
   ```ini
   # /etc/systemd/system/bluetooth.service.d/bt-kvm.conf
   [Service]
   ExecStart=
   ExecStart=/usr/libexec/bluetooth/bluetoothd -P input
   ```
4. Sets the following in `/etc/bluetooth/main.conf` under `[General]`, after backing it
   up to `main.conf.bt-kvm.bak`:
   ```ini
   Class = 0x000540          # Peripheral / Keyboard, so hosts show a keyboard icon
   ControllerMode = bredr    # Classic only; we don't use Bluetooth LE
   Name = BT-KVM Keyboard
   ```
5. Installs and starts `bt-kvm.service`, which restarts itself if it crashes.

Check that it worked:

```bash
journalctl -u bt-kvm -f                # live log
bluetoothctl show | grep -i class      # should end in ...540
```

### 4. Plug in the keyboard and mouse

Plug the Sinc (USB-C to USB-A cable) and the mouse into the two **black USB 2.0
ports**. The blue USB 3.0 ports give off 2.4 GHz noise that can hurt Bluetooth, so
keep them for anything else. The log should show `keyboard interface: Keebio Sinc ...`
a few times (once per USB interface) and `mouse interface: ...` for the mouse.

### 5. Add the switch keys to the Sinc (VIA)

Open [usevia.app](https://usevia.app) in Chrome or Edge with the Sinc plugged into a
computer. On your Fn layer, set keys to `F21`/`F22` (keyboard to host 1/2), `F19`/`F20`
(mouse to host 1/2) and `F23` (pair). If they aren't in the picker, use **Any** and
type `KC_F21` etc. The front buttons do the same, so this is optional.
The keymap is stored on the keyboard itself. If you'd rather skip this step, the
both-Ctrls chord works without it.

### 6. Pair the two computers

1. On first start, with nothing paired, the Pi goes straight into pairing mode for
   **host 1** (both "1" LEDs blink fast).
2. On the **personal PC**: Settings → Bluetooth & devices → Add device → Bluetooth →
   **BT-KVM Keyboard**. It should pair without a PIN, as a keyboard and mouse. The
   "1" LEDs turn solid. Type and move the mouse to check.
3. Short-press the **Keyboard** button. Its "2" LED slow-blinks because slot 2 is
   empty. Hold the same button for 3 s: the "2" LEDs blink fast.
4. On the **work PC**: Add device → **BT-KVM Keyboard**. The keyboard's "2" LED turns
   solid.
5. Now each button swaps its own device: press **Keyboard** or **Mouse** whenever you
   like.

Pairing keys are stored in `/var/lib/bluetooth` (by BlueZ) and the slots in
`/var/lib/bt-kvm/state.json`. To pair a slot again, make it active, press pair, and
pair the new computer. The old pairing in that slot is removed.

### 7. Harden it (recommended once both computers are paired)

- **Read-only SD card.** Run `sudo raspi-config` → Performance → Overlay File System →
  enable. After that, pulling the power can't corrupt the SD card. However, **new
  pairings and the last-used slot won't survive a reboot** while it's on. To pair
  something new, turn the overlay off, reboot, pair, then turn it back on.
- **Everything you type, work passwords included, passes through this Pi.** bt-kvm
  never logs keystrokes. Use SSH keys (`PasswordAuthentication no`), and think about
  turning Wi-Fi off once it works: add `dtoverlay=disable-wifi` to
  `/boot/firmware/config.txt`, and use Ethernet when you need to log in. Also check
  your employer's policy on Bluetooth keyboards.

## Things it can't do

- **No Bluetooth keyboard works before the OS loads**: BIOS/UEFI, the boot menu, a
  BitLocker pre-boot PIN. Plug the Sinc straight into the PC for those. The Windows
  login screen does work once the keyboard is paired.
- Typing latency is roughly 5–20 ms, set by the Bluetooth link. That's fine for
  typing and office work. For competitive gaming, plug the keyboard in.
- The Pi takes about 20 s to boot after power-on before it can type.
- Only keyboard and media keys are passed through. QMK mouse keys and system
  power/sleep keys are dropped.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Log says `cannot bind L2CAP PSM 0x11` | The input plugin is still on. Check `systemctl cat bluetooth` shows `-P input`, then `sudo systemctl restart bluetooth`. |
| PC can't find "BT-KVM Keyboard" | Not in pairing mode (press F23 / hold the button). Check `bluetoothctl show` says `Discoverable: yes`. |
| Pairs, then won't type, or drops at once | Remove it on both sides: in Windows, *Remove device*; on the Pi, `bluetoothctl remove <MAC>`. Then pair again. Windows caches the HID descriptor, so after any descriptor change you must pair again. |
| Switching to a host does nothing | That PC is asleep or out of range. Wake it and switch again; the Pi tries 3 times. |
| Laggy or dropped keys | Use a black USB 2.0 port, keep USB 3 drives away, and use the official 3 A power supply (low voltage makes Bluetooth unreliable). |
| Keys go to the Pi's screen | The grab failed, usually because another program has the keyboard open. Check the log. |

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install evdev dbus-next pytest
.venv/bin/python -m pytest -q
```

The tests cover the key tables, report building, hotkeys, host switching and the HID
control channel. Local sockets stand in for Bluetooth, so the tests run on any Linux
machine.
