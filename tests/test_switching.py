"""Host switching and control-channel handling, with socketpairs standing in for L2CAP."""
import asyncio
import socket

from evdev import ecodes as e

import bt_kvm.main as m


def pair():
    a, b = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    a.setblocking(False)
    b.settimeout(1)
    return a, b


def make_kvm(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "STATE_PATH", tmp_path / "state.json")
    kvm = m.Kvm(dict(m.DEFAULT_CONFIG), {"slots": ["AA:AA:AA:AA:AA:01", "AA:AA:AA:AA:AA:02"],
                                         "active": 0})

    async def no_trust(mac):
        pass
    kvm.trust = no_trust
    return kvm


def connect(kvm, mac):
    host = m.Host(mac)
    host.ctrl, ctrl_peer = pair()
    host.intr, intr_peer = pair()
    kvm.hosts[mac] = host
    return host, ctrl_peer, intr_peer


def test_reports_go_to_active_host_and_switch_releases_keys(tmp_path, monkeypatch):
    async def go():
        kvm = make_kvm(tmp_path, monkeypatch)
        _, _, intr1 = connect(kvm, "AA:AA:AA:AA:AA:01")
        _, _, intr2 = connect(kvm, "AA:AA:AA:AA:AA:02")
        await kvm.key(e.KEY_A, True)
        assert intr1.recv(64) == b"\xa1" + bytes([1, 0, 0, 4, 0, 0, 0, 0, 0])
        # chord: both Ctrl + 2 switches to host 2; '2' never reaches anyone
        await kvm.key(e.KEY_LEFTCTRL, True)
        await kvm.key(e.KEY_RIGHTCTRL, True)
        intr1.recv(64), intr1.recv(64)
        await kvm.key(e.KEY_2, True)
        assert kvm.active == 1
        assert intr1.recv(64) == b"\xa1" + m.EMPTY_KEYBOARD
        assert intr1.recv(64) == b"\xa1" + m.EMPTY_CONSUMER
        await kvm.key(e.KEY_2, False)
        await kvm.key(e.KEY_LEFTCTRL, False)
        await kvm.key(e.KEY_RIGHTCTRL, False)
        await kvm.key(e.KEY_A, False)
        # the new host starts from a clean "all keys up" report, never sees the chord
        assert intr2.recv(64) == b"\xa1" + m.EMPTY_KEYBOARD
        await kvm.key(e.KEY_B, True)
        assert intr2.recv(64) == b"\xa1" + bytes([1, 0, 0, 5, 0, 0, 0, 0, 0])
        assert (tmp_path / "state.json").exists()
    asyncio.run(go())


def test_control_channel_handshakes_and_leds(tmp_path, monkeypatch):
    async def go():
        kvm = make_kvm(tmp_path, monkeypatch)
        host, ctrl, intr = connect(kvm, "AA:AA:AA:AA:AA:01")
        await kvm.incoming(host, "ctrl", host.ctrl, bytes([0x70]))      # SET_PROTOCOL boot
        assert ctrl.recv(8) == b"\x00" and host.boot
        await kvm.incoming(host, "ctrl", host.ctrl, bytes([0x71]))      # SET_PROTOCOL report
        assert ctrl.recv(8) == b"\x00" and not host.boot
        await kvm.incoming(host, "ctrl", host.ctrl, bytes([0x41, 1]))   # GET_REPORT input 1
        assert ctrl.recv(16) == b"\xa1" + m.EMPTY_KEYBOARD
        await kvm.incoming(host, "ctrl", host.ctrl, bytes([0x52, 1, 2]))  # SET_REPORT LEDs
        assert ctrl.recv(8) == b"\x00" and host.leds == 2
        await kvm.incoming(host, "intr", host.intr, bytes([0xA2, 1, 1]))  # LED output report
        assert host.leds == 1
        await kvm.incoming(host, "ctrl", host.ctrl, bytes([0x15]))      # virtual cable unplug
        assert "AA:AA:AA:AA:AA:01" not in kvm.hosts
    asyncio.run(go())


def test_new_host_fills_pairing_slot(tmp_path, monkeypatch):
    async def go():
        kvm = make_kvm(tmp_path, monkeypatch)
        forgotten = []

        async def forget(mac):
            forgotten.append(mac)

        async def stop():
            kvm.pairing_slot = None
        kvm.forget, kvm.stop_pairing = forget, stop
        kvm.pairing_slot = 1
        host, _, _ = connect(kvm, "BB:BB:BB:BB:BB:BB")
        await kvm.host_ready(host)
        assert kvm.state["slots"] == ["AA:AA:AA:AA:AA:01", "BB:BB:BB:BB:BB:BB"]
        assert forgotten == ["AA:AA:AA:AA:AA:02"] and kvm.pairing_slot is None
    asyncio.run(go())
