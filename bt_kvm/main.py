"""bt-kvm daemon: read a USB keyboard, send it to one of two Bluetooth hosts.

How it fits together (all in one asyncio loop, run as root by systemd):

  USB keyboard --evdev (grabbed)--> KeyState --HID reports--> L2CAP PSM 0x13 --> active host
                                     Hotkeys --switch/pair--> slot logic, GPIO LEDs
  GPIO button ----gpiozero thread--> same actions

Bluetooth Classic HID, device side:
- bluetoothd runs with its `input` plugin off (-P input), otherwise it holds PSMs 0x11/0x13.
- We register an SDP record (via ProfileManager1) so hosts see a keyboard, then listen on
  L2CAP 0x11 (control) and 0x13 (interrupt) ourselves.
- Hosts that are paired may connect to us at any time; we keep every such connection
  open, but only the active slot receives reports. Switching to a slot whose host isn't
  connected makes us dial it (HIDReconnectInitiate=true in the SDP record).
- A D-Bus agent with NoInputNoOutput accepts pairing, but only while pairing mode is on.
"""

import asyncio
import json
import logging
import os
import signal
import socket
import sys
from pathlib import Path

import evdev
from dbus_next import BusType, DBusError, Variant
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method
from evdev import ecodes as e

from .hid import EMPTY_CONSUMER, EMPTY_KEYBOARD, HID_UUID, Hotkeys, KeyState, key_code, sdp_record

log = logging.getLogger("bt-kvm")

CONFIG_PATH = Path(os.environ.get("BT_KVM_CONFIG", "/etc/bt-kvm/config.json"))
STATE_PATH = Path(os.environ.get("BT_KVM_STATE", "/var/lib/bt-kvm/state.json"))

DEFAULT_CONFIG = {
    "device_name": "BT-KVM Keyboard",
    "adapter": "hci0",
    # Grab every USB input device with keys whose name contains one of these
    # substrings. Empty list = any USB keyboard (fine on a headless Pi).
    "keyboard_names": [],
    # Single keys that fire an action. Map them on a QMK/VIA Fn layer.
    "hotkeys": {"KEY_F21": "host1", "KEY_F22": "host2", "KEY_F23": "pair"},
    # Fallback chord that works with any keyboard: hold all of these + press a key.
    "chord_modifiers": ["KEY_LEFTCTRL", "KEY_RIGHTCTRL"],
    "chord_keys": {"KEY_1": "host1", "KEY_2": "host2", "KEY_0": "pair"},
    # BCM GPIO numbers; set to null to disable. Button to GND, LEDs via 330 ohm to GND.
    "gpio_button": 17,
    "gpio_led_host1": 23,
    "gpio_led_host2": 24,
    "button_hold_seconds": 3,
    "pairing_seconds": 120,
}

PSM_CTRL = 0x11
PSM_INTR = 0x13
BLUEZ = "org.bluez"
AGENT_PATH = "/bt_kvm/agent"
PROFILE_PATH = "/bt_kvm/profile"

# HID transaction types (Bluetooth HID profile, first byte high nibble)
HANDSHAKE_OK = 0x00
HANDSHAKE_UNSUPPORTED = 0x03
HIDP_CONTROL, GET_REPORT, SET_REPORT, GET_PROTOCOL, SET_PROTOCOL = 0x1, 0x4, 0x5, 0x6, 0x7
GET_IDLE, SET_IDLE, DATA = 0x8, 0x9, 0xA
VIRTUAL_CABLE_UNPLUG = 0x5


def load_json(path, default):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default
    except (OSError, ValueError) as ex:
        log.warning("could not read %s (%s); using defaults", path, ex)
        return default


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    os.replace(tmp, STATE_PATH)


def l2cap_socket():
    return socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)


def l2cap_listen(psm):
    s = l2cap_socket()
    try:
        s.bind((socket.BDADDR_ANY, psm))
    except OSError as ex:
        s.close()
        raise SystemExit(
            f"cannot bind L2CAP PSM {psm:#x}: {ex}. Is bluetoothd still running its input "
            "plugin? See README step 4 (ExecStart ... -P input).") from ex
    s.listen(2)
    s.setblocking(False)
    return s


def l2cap_connect(mac, psm, timeout=8.0):
    """Blocking connect; run it in an executor."""
    s = l2cap_socket()
    s.settimeout(timeout)
    try:
        s.connect((mac, psm))
    except OSError:
        s.close()
        raise
    s.setblocking(False)
    return s


def device_path(adapter, mac):
    return f"/org/bluez/{adapter}/dev_{mac.upper().replace(':', '_')}"


class Host:
    """One connected host: its control and interrupt channels."""

    def __init__(self, mac):
        self.mac = mac
        self.ctrl = None
        self.intr = None
        self.boot = False       # host asked for boot protocol (no report IDs)
        self.leds = 0           # last LED byte the host sent (Num/Caps/Scroll)

    def close(self):
        for s in (self.ctrl, self.intr):
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass
        self.ctrl = self.intr = None


class Agent(ServiceInterface):
    """Pairing agent. Accepts 'just works' pairing only while pairing mode is on."""

    def __init__(self, kvm):
        super().__init__("org.bluez.Agent1")
        self.kvm = kvm

    def _allow(self, device):
        if self.kvm.pairing_slot is None:
            log.warning("rejected pairing from %s: not in pairing mode", device)
            raise DBusError("org.bluez.Error.Rejected", "not in pairing mode")
        log.info("accepting pairing from %s", device)

    @method()
    def Release(self):
        pass

    @method()
    def RequestPinCode(self, device: "o") -> "s":
        self._allow(device)
        return "0000"

    @method()
    def DisplayPinCode(self, device: "o", pincode: "s"):
        log.info("PIN for %s: %s", device, pincode)

    @method()
    def RequestPasskey(self, device: "o") -> "u":
        self._allow(device)
        return 0

    @method()
    def DisplayPasskey(self, device: "o", passkey: "u", entered: "q"):
        log.info("passkey for %s: %06d", device, passkey)

    @method()
    def RequestConfirmation(self, device: "o", passkey: "u"):
        self._allow(device)

    @method()
    def RequestAuthorization(self, device: "o"):
        self._allow(device)

    @method()
    def AuthorizeService(self, device: "o", uuid: "s"):
        pass  # only bonded devices get here

    @method()
    def Cancel(self):
        pass


class Profile(ServiceInterface):
    """Only here so BlueZ publishes our SDP record. We own the L2CAP sockets ourselves."""

    def __init__(self):
        super().__init__("org.bluez.Profile1")

    @method()
    def Release(self):
        pass

    @method()
    def NewConnection(self, device: "o", fd: "h", properties: "a{sv}"):
        os.close(fd)

    @method()
    def RequestDisconnection(self, device: "o"):
        pass


class Kvm:
    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state                    # {"slots": [mac|None, mac|None], "active": 0|1}
        self.loop = asyncio.get_running_loop()
        self.keys = KeyState()
        self.hotkeys = Hotkeys(
            {key_code(k): v for k, v in cfg["hotkeys"].items()},
            [key_code(k) for k in cfg["chord_modifiers"]],
            {key_code(k): v for k, v in cfg["chord_keys"].items()},
        )
        self.hosts = {}                       # mac -> Host (connected, or connecting)
        self.devices = {}                     # evdev path -> InputDevice
        self.ignored = set()                  # evdev paths we looked at and don't want
        self.pairing_slot = None
        self.pairing_task = None
        self.connect_task = None
        self.leds = []
        self.button = None
        self.bus = None
        self.adapter = None

    # ---------- state ----------
    @property
    def active(self):
        return self.state["active"]

    def slot_of(self, mac):
        try:
            return self.state["slots"].index(mac)
        except ValueError:
            return None

    def active_host(self):
        mac = self.state["slots"][self.active]
        host = self.hosts.get(mac) if mac else None
        return host if host and host.intr else None

    # ---------- Bluetooth: D-Bus setup ----------
    async def iface(self, path, name):
        intro = await self.bus.introspect(BLUEZ, path)
        return self.bus.get_proxy_object(BLUEZ, path, intro).get_interface(name)

    async def setup_bluez(self):
        self.bus = await MessageBus(bus_type=BusType.SYSTEM, negotiate_unix_fd=True).connect()
        self.bus.export(AGENT_PATH, Agent(self))
        self.bus.export(PROFILE_PATH, Profile())
        agents = await self.iface("/org/bluez", "org.bluez.AgentManager1")
        await agents.call_register_agent(AGENT_PATH, "NoInputNoOutput")
        await agents.call_request_default_agent(AGENT_PATH)
        profiles = await self.iface("/org/bluez", "org.bluez.ProfileManager1")
        await profiles.call_register_profile(PROFILE_PATH, HID_UUID, {
            "ServiceRecord": Variant("s", sdp_record(self.cfg["device_name"])),
            "Role": Variant("s", "server"),
            "RequireAuthentication": Variant("b", True),
            "RequireAuthorization": Variant("b", False),
        })
        self.adapter = await self.iface(f"/org/bluez/{self.cfg['adapter']}", "org.bluez.Adapter1")
        await self.adapter.set_powered(True)
        await self.adapter.set_alias(self.cfg["device_name"])
        await self.adapter.set_discoverable(False)
        await self.adapter.set_pairable(False)
        log.info("Bluetooth ready as %r", self.cfg["device_name"])

    async def trust(self, mac):
        try:
            dev = await self.iface(device_path(self.cfg["adapter"], mac), "org.bluez.Device1")
            await dev.set_trusted(True)
        except Exception as ex:  # noqa: BLE001 - best effort
            log.warning("could not mark %s trusted: %s", mac, ex)

    async def forget(self, mac):
        try:
            await self.adapter.call_remove_device(device_path(self.cfg["adapter"], mac))
            log.info("removed old pairing %s", mac)
        except Exception as ex:  # noqa: BLE001
            log.warning("could not remove %s: %s", mac, ex)

    # ---------- Bluetooth: pairing mode ----------
    async def start_pairing(self, slot):
        secs = int(self.cfg["pairing_seconds"])
        self.pairing_slot = slot
        await self.adapter.set_pairable(True)
        await self.adapter.set_discoverable_timeout(secs)
        await self.adapter.set_discoverable(True)
        log.info("pairing mode for host %d for %ds", slot + 1, secs)
        if self.pairing_task:
            self.pairing_task.cancel()
        self.pairing_task = self.loop.create_task(self._pairing_timeout(secs))
        self.update_leds()

    async def _pairing_timeout(self, secs):
        await asyncio.sleep(secs)
        self.pairing_task = None
        await self.stop_pairing()

    async def stop_pairing(self):
        if self.pairing_slot is None:
            return
        self.pairing_slot = None
        if self.pairing_task:
            self.pairing_task.cancel()
            self.pairing_task = None
        try:
            await self.adapter.set_discoverable(False)
            await self.adapter.set_pairable(False)
        except Exception as ex:  # noqa: BLE001
            log.warning("could not leave pairing mode cleanly: %s", ex)
        log.info("pairing mode off")
        self.update_leds()

    # ---------- Bluetooth: connections ----------
    async def accept_loop(self, server, kind):
        while True:
            conn, addr = await self.loop.sock_accept(server)
            conn.setblocking(False)
            log.info("%s channel from %s", kind, addr[0])
            await self.attach(addr[0], kind, conn)

    async def attach(self, mac, kind, sock):
        host = self.hosts.get(mac)
        if kind == "ctrl" and host and (host.ctrl or host.intr):
            self.drop(host, "reconnected")    # a new control channel starts a new session
            host = None
        if host is None:
            host = self.hosts[mac] = Host(mac)
        old = getattr(host, kind)
        if old is not None:
            old.close()
        setattr(host, kind, sock)
        self.loop.create_task(self.reader(host, kind, sock))
        if kind == "intr":
            await self.host_ready(host)

    async def host_ready(self, host):
        slots = self.state["slots"]
        if host.mac not in slots:
            target = self.pairing_slot
            if target is None and None in slots:
                target = slots.index(None)
            if target is not None:
                old = slots[target]
                slots[target] = host.mac
                save_state(self.state)
                log.info("host %d is now %s", target + 1, host.mac)
                if old and old not in slots:
                    await self.forget(old)
            else:
                log.warning("%s connected but both host slots are taken; ignoring it", host.mac)
        if self.pairing_slot is not None and host.mac in slots:
            await self.stop_pairing()
        await self.trust(host.mac)
        if self.slot_of(host.mac) == self.active:
            self.keys.switched_host()
            self.set_keyboard_leds(host.leds)
        self.update_leds()

    async def reader(self, host, kind, sock):
        try:
            while True:
                data = await self.loop.sock_recv(sock, 64)
                if not data:
                    break
                await self.incoming(host, kind, sock, data)
        except OSError as ex:
            log.info("%s %s channel closed: %s", host.mac, kind, ex)
        if getattr(host, kind) is sock and self.hosts.get(host.mac) is host:
            self.drop(host, "disconnected")

    def drop(self, host, why):
        host.close()
        if self.hosts.get(host.mac) is host:
            del self.hosts[host.mac]
        log.info("%s %s", host.mac, why)
        self.update_leds()

    async def incoming(self, host, kind, sock, data):
        hdr = data[0]
        if kind == "intr":
            # Output report from host: 0xA2, report id 1, LED bits
            if hdr == 0xA2 and len(data) >= 3 and data[1] == 1:
                self.host_leds(host, data[2])
            elif hdr == 0xA2 and len(data) >= 2 and host.boot:
                self.host_leds(host, data[1])
            return
        kind_, param = hdr >> 4, hdr & 0x0F
        reply = None
        if kind_ == HIDP_CONTROL:
            if param == VIRTUAL_CABLE_UNPLUG:
                self.drop(host, "unplugged by host")
            return
        if kind_ == GET_REPORT:
            rid = data[1] if len(data) > 1 else 1
            rep = self.keys.consumer_report() if rid == 2 else self.keys.keyboard_report()
            reply = bytes([(DATA << 4) | 0x1]) + (rep[1:] if host.boot else rep)
        elif kind_ == SET_REPORT:
            if param == 0x2 and len(data) >= 3 and data[1] == 1:
                self.host_leds(host, data[2])
            reply = bytes([HANDSHAKE_OK])
        elif kind_ == GET_PROTOCOL:
            reply = bytes([DATA << 4, 0 if host.boot else 1])
        elif kind_ == SET_PROTOCOL:
            host.boot = (param & 1) == 0
            log.info("%s set %s protocol", host.mac, "boot" if host.boot else "report")
            reply = bytes([HANDSHAKE_OK])
        elif kind_ == GET_IDLE:
            reply = bytes([DATA << 4, 0])
        elif kind_ == SET_IDLE:
            reply = bytes([HANDSHAKE_OK])
        else:
            reply = bytes([HANDSHAKE_UNSUPPORTED])
        try:
            await self.loop.sock_sendall(sock, reply)
        except OSError:
            pass

    async def send(self, report, host=None):
        host = host or self.active_host()
        if host is None or host.intr is None:
            return
        if host.boot:
            if report[0] != 1:
                return                         # boot keyboards have no media keys
            payload = b"\xa1" + report[1:]
        else:
            payload = b"\xa1" + report
        try:
            await self.loop.sock_sendall(host.intr, payload)
        except OSError as ex:
            self.drop(host, f"send failed ({ex})")

    def ensure_connected(self):
        if self.active_host() or self.state["slots"][self.active] is None:
            return
        if self.connect_task and not self.connect_task.done():
            return
        self.connect_task = self.loop.create_task(self.connect_slot(self.active))

    async def connect_slot(self, slot):
        mac = self.state["slots"][slot]
        for attempt in range(1, 4):
            if self.active != slot or (self.hosts.get(mac) and self.hosts[mac].intr):
                return
            log.info("connecting to host %d (%s), try %d", slot + 1, mac, attempt)
            ctrl = None
            try:
                ctrl = await self.loop.run_in_executor(None, l2cap_connect, mac, PSM_CTRL)
                intr = await self.loop.run_in_executor(None, l2cap_connect, mac, PSM_INTR)
            except OSError as ex:
                if ctrl:
                    ctrl.close()
                log.info("host %d not reachable: %s", slot + 1, ex)
                await asyncio.sleep(2)
                continue
            await self.attach(mac, "ctrl", ctrl)
            await self.attach(mac, "intr", intr)
            return
        log.warning("gave up on host %d; switch again or wake that computer", slot + 1)
        self.update_leds()

    # ---------- actions ----------
    def action(self, name):
        """Thread-safe entry point (the GPIO callbacks use it)."""
        self.loop.call_soon_threadsafe(lambda: self.loop.create_task(self.do_action(name)))

    async def do_action(self, name):
        if name == "host1":
            await self.switch(0)
        elif name == "host2":
            await self.switch(1)
        elif name == "toggle":
            await self.switch(1 - self.active)
        elif name == "pair":
            if self.pairing_slot is None:
                await self.start_pairing(self.active)
            else:
                await self.stop_pairing()
        else:
            log.warning("unknown action %r", name)

    async def switch(self, slot):
        if slot != self.active:
            old = self.active_host()
            if old:
                await self.send(EMPTY_KEYBOARD, old)   # no stuck keys on the old host
                await self.send(EMPTY_CONSUMER, old)
            self.state["active"] = slot
            save_state(self.state)
            log.info("active host is now %d", slot + 1)
        self.keys.switched_host()
        if self.pairing_slot is not None and self.pairing_slot != slot:
            await self.stop_pairing()
        host = self.active_host()
        if host:
            self.set_keyboard_leds(host.leds)
        elif self.state["slots"][slot] is None:
            log.info("host %d has no computer paired; press the pair shortcut", slot + 1)
        else:
            self.ensure_connected()
        self.update_leds()

    # ---------- keyboard ----------
    def wanted(self, dev):
        if e.EV_KEY not in dev.capabilities():
            return False
        if "usb" not in (dev.phys or ""):
            return False
        names = self.cfg["keyboard_names"]
        return not names or any(n.lower() in dev.name.lower() for n in names)

    async def watch_devices(self):
        while True:
            present = set(evdev.list_devices())
            self.ignored &= present
            for path in present - set(self.devices) - self.ignored:
                try:
                    dev = evdev.InputDevice(path)
                except OSError:
                    continue
                if not self.wanted(dev):
                    dev.close()
                    self.ignored.add(path)
                    continue
                try:
                    dev.grab()   # keep keystrokes away from the Pi's own console
                except OSError as ex:
                    log.warning("could not grab %s: %s", dev.name, ex)
                log.info("keyboard interface: %s (%s)", dev.name, path)
                self.devices[path] = dev
                self.loop.create_task(self.read_device(path, dev))
                host = self.active_host()
                if host:
                    self.set_keyboard_leds(host.leds)
            await asyncio.sleep(2)

    async def read_device(self, path, dev):
        try:
            async for ev in dev.async_read_loop():
                if ev.type == e.EV_KEY and ev.value in (0, 1):   # 2 = autorepeat: host repeats
                    await self.key(ev.code, ev.value == 1)
        except OSError:
            pass
        log.info("keyboard interface gone: %s", path)
        self.devices.pop(path, None)
        try:
            dev.close()
        except OSError:
            pass
        self.keys.clear()
        await self.send(EMPTY_KEYBOARD)
        await self.send(EMPTY_CONSUMER)

    async def key(self, code, down):
        swallow, action = self.hotkeys.check(code, down, self.keys.pressed)
        if action:
            await self.do_action(action)
        if swallow:
            return
        report = self.keys.event(code, down)
        if report is not None:
            await self.send(report)

    def host_leds(self, host, bits):
        host.leds = bits
        if self.slot_of(host.mac) == self.active:
            self.set_keyboard_leds(bits)

    def set_keyboard_leds(self, bits):
        for dev in list(self.devices.values()):
            if e.EV_LED not in dev.capabilities():
                continue
            try:
                dev.set_led(e.LED_NUML, bits & 1)
                dev.set_led(e.LED_CAPSL, (bits >> 1) & 1)
                dev.set_led(e.LED_SCROLLL, (bits >> 2) & 1)
            except OSError:
                pass

    # ---------- GPIO ----------
    def setup_gpio(self):
        pins = (self.cfg["gpio_led_host1"], self.cfg["gpio_led_host2"])
        try:
            from gpiozero import LED, Button
            if all(p is not None for p in pins):
                self.leds = [LED(p) for p in pins]
            if self.cfg["gpio_button"] is not None:
                self.button = Button(self.cfg["gpio_button"], pull_up=True, bounce_time=0.05,
                                     hold_time=float(self.cfg["button_hold_seconds"]))
        except Exception as ex:  # noqa: BLE001 - no GPIO is fine, hotkeys still work
            log.warning("GPIO disabled: %s", ex)
            return
        if self.button:
            held = {"yes": False}

            def on_held():
                held["yes"] = True
                self.action("pair")

            def on_released():
                if held["yes"]:
                    held["yes"] = False
                else:
                    self.action("toggle")

            self.button.when_held = on_held
            self.button.when_released = on_released

    def update_leds(self):
        """Solid = active and connected. Slow blink = active, not connected.
        Fast blink = pairing mode for that slot. Off = inactive."""
        for slot, led in enumerate(self.leds):
            try:
                if self.pairing_slot == slot:
                    led.blink(0.1, 0.1)
                elif slot == self.active:
                    if self.active_host():
                        led.on()
                    else:
                        led.blink(0.5, 0.5)
                else:
                    led.off()
            except Exception:  # noqa: BLE001
                pass

    # ---------- run ----------
    async def run(self):
        await self.setup_bluez()
        servers = [l2cap_listen(PSM_CTRL), l2cap_listen(PSM_INTR)]
        self.setup_gpio()
        tasks = [
            self.loop.create_task(self.accept_loop(servers[0], "ctrl")),
            self.loop.create_task(self.accept_loop(servers[1], "intr")),
            self.loop.create_task(self.watch_devices()),
        ]
        if self.state["slots"] == [None, None]:
            log.info("no computers paired yet: entering pairing mode for host 1")
            await self.start_pairing(0)
        else:
            self.ensure_connected()
        self.update_leds()

        stop = asyncio.Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            self.loop.add_signal_handler(sig, stop.set)
        await stop.wait()

        log.info("shutting down")
        await self.send(EMPTY_KEYBOARD)
        await self.send(EMPTY_CONSUMER)
        for t in tasks:
            t.cancel()
        for host in list(self.hosts.values()):
            host.close()
        for s in servers:
            s.close()
        for dev in self.devices.values():
            try:
                dev.ungrab()
            except OSError:
                pass
        for led in self.leds:
            led.off()


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(load_json(CONFIG_PATH, {}))
    return cfg


def load_state():
    state = load_json(STATE_PATH, {})
    slots = list(state.get("slots", [None, None]))[:2]
    slots += [None] * (2 - len(slots))
    active = state.get("active", 0)
    return {"slots": slots, "active": active if active in (0, 1) else 0}


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stdout)
    cfg = load_config()

    async def runner():
        await Kvm(cfg, load_state()).run()

    asyncio.run(runner())


if __name__ == "__main__":
    main()
