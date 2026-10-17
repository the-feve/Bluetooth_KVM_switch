#!/usr/bin/env bash
# Install bt-kvm on Raspberry Pi OS (Bookworm or Trixie). Run from the repo: sudo ./install.sh
# Safe to re-run after a `git pull`.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Run with sudo: sudo ./install.sh"; exit 1; }
cd "$(dirname "$0")"

echo "== packages"
apt-get update
apt-get install -y bluez python3-evdev python3-gpiozero python3-lgpio
apt-get install -y python3-dbus-next || true
if ! python3 -c 'import dbus_next' 2>/dev/null; then
    apt-get install -y python3-pip
    pip3 install --break-system-packages dbus-next
fi

echo "== program files"
install -d /opt/bt-kvm/bt_kvm /etc/bt-kvm /var/lib/bt-kvm
install -m 644 bt_kvm/*.py /opt/bt-kvm/bt_kvm/
[ -f /etc/bt-kvm/config.json ] || install -m 644 config.example.json /etc/bt-kvm/config.json

echo "== bluetoothd: turn off the input plugin (it would hold L2CAP PSMs 0x11/0x13)"
BTD=""
for p in /usr/libexec/bluetooth/bluetoothd /usr/lib/bluetooth/bluetoothd; do
    if [ -x "$p" ]; then BTD="$p"; break; fi
done
[ -n "$BTD" ] || { echo "bluetoothd not found"; exit 1; }
install -d /etc/systemd/system/bluetooth.service.d
cat > /etc/systemd/system/bluetooth.service.d/bt-kvm.conf <<CONF
[Service]
ExecStart=
ExecStart=$BTD -P input
CONF

echo "== /etc/bluetooth/main.conf: keyboard class, Classic (BR/EDR) only"
MAIN=/etc/bluetooth/main.conf
[ -f "$MAIN.bt-kvm.bak" ] || cp "$MAIN" "$MAIN.bt-kvm.bak"
set_general() {   # set_general Key Value: replace the first (maybe commented) line, or add it
    if grep -qE "^[#[:space:]]*$1[[:space:]]*=" "$MAIN"; then
        sed -i -E "0,/^[#[:space:]]*$1[[:space:]]*=.*/s||$1 = $2|" "$MAIN"
    else
        sed -i "/^\[General\]/a $1 = $2" "$MAIN"
    fi
}
set_general Class 0x000540          # Peripheral / Keyboard; BlueZ adds the service bits
set_general ControllerMode bredr    # we are a Classic HID device; hide the LE side
set_general Name "BT-KVM Keyboard"

echo "== service"
install -m 644 systemd/bt-kvm.service /etc/systemd/system/bt-kvm.service
rfkill unblock bluetooth || true
systemctl daemon-reload
systemctl restart bluetooth
systemctl enable bt-kvm
systemctl restart bt-kvm

echo
echo "Done. Watch it with:  journalctl -u bt-kvm -f"
echo "Check the class with: bluetoothctl show | grep Class   (should end in 540)"
