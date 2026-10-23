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
                                         "active": {"kb": 0, "mouse": 0}})

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
        assert kvm.active("kb") == 1
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


def test_keyboard_and_mouse_switch_independently(tmp_path, monkeypatch):
    async def go():
        from evdev import InputEvent
        kvm = make_kvm(tmp_path, monkeypatch)
        _, _, intr1 = connect(kvm, "AA:AA:AA:AA:AA:01")
        _, _, intr2 = connect(kvm, "AA:AA:AA:AA:AA:02")
        kvm.cfg["mouse_report_ms"] = 1
        # Front "keyboard" button: keyboard moves to host 2, mouse stays on host 1.
        await kvm.do_action("kb_toggle")
        assert kvm.active("kb") == 1 and kvm.active("mouse") == 0
        intr1.recv(64), intr1.recv(64)   # all-up keyboard + consumer to the old host
        await kvm.key(e.KEY_A, True)
        assert intr2.recv(64)[:2] == b"\xa1\x01"
        # Mouse movement goes to host 1; a click is sent at once.
        await kvm.pointer(InputEvent(0, 0, e.EV_REL, e.REL_X, 5))
        await kvm.pointer(InputEvent(0, 0, e.EV_SYN, e.SYN_REPORT, 0))
        await asyncio.sleep(0.05)
        rep = intr1.recv(64)
        assert rep[:2] == b"\xa1\x03" and int.from_bytes(rep[3:5], "little", signed=True) == 5
        await kvm.pointer(InputEvent(0, 0, e.EV_KEY, e.BTN_LEFT, 1))
        assert intr1.recv(64)[2] == 1
        # Mouse button: mouse moves to host 2; host 1 gets "buttons up" first.
        await kvm.do_action("mouse_toggle")
        assert intr1.recv(64) == b"\xa1" + m.EMPTY_MOUSE
        assert kvm.state["active"] == {"kb": 1, "mouse": 1}
    asyncio.run(go())


def test_pedal_moves_keyboard_and_mouse_together(tmp_path, monkeypatch):
    async def go():
        kvm = make_kvm(tmp_path, monkeypatch)
        _, _, intr1 = connect(kvm, "AA:AA:AA:AA:AA:01")
        connect(kvm, "AA:AA:AA:AA:AA:02")
        await kvm.do_action("both_toggle")
        assert kvm.state["active"] == {"kb": 1, "mouse": 1}
        # the old host is left with nothing held: keyboard, media keys and mouse all up
        assert [intr1.recv(64) for _ in range(3)] == [
            b"\xa1" + m.EMPTY_KEYBOARD, b"\xa1" + m.EMPTY_CONSUMER, b"\xa1" + m.EMPTY_MOUSE]
        await kvm.do_action("both_toggle")
        assert kvm.state["active"] == {"kb": 0, "mouse": 0}
        # split (keyboard on 1, mouse on 2): both join the computer the keyboard isn't on
        await kvm.do_action("mouse_toggle")
        await kvm.do_action("both_toggle")
        assert kvm.state["active"] == {"kb": 1, "mouse": 1}
    asyncio.run(go())


def test_old_state_and_config_files_still_load(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(m, "STATE_PATH", tmp_path / "state.json")
    (tmp_path / "state.json").write_text(json.dumps({"slots": ["AA:AA:AA:AA:AA:01"], "active": 1}))
    assert m.load_state() == {"slots": ["AA:AA:AA:AA:AA:01", None], "active": {"kb": 1, "mouse": 1}}
    monkeypatch.setattr(m, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text(json.dumps({"gpio_button": 5, "gpio_led_host1": 6, "gpio_led_host2": 7}))
    cfg = m.load_config()
    assert cfg["buttons"]["kb"] == 5 and cfg["leds"]["kb"] == [6, 7] and cfg["buttons"]["mouse"] == 27
    # a config written before the foot pedal existed still gets its pin
    (tmp_path / "config.json").write_text(json.dumps({"buttons": {"kb": 5, "mouse": 6}}))
    assert m.load_config()["buttons"] == {"kb": 5, "mouse": 6, "both": 22}


def test_device_kinds():
    assert m.device_kind({e.EV_KEY: [e.KEY_A], e.EV_LED: [0]}) == "kb"
    assert m.device_kind({e.EV_KEY: [e.BTN_LEFT], e.EV_REL: [e.REL_X, e.REL_Y]}) == "mouse"
    assert m.device_kind({e.EV_ABS: [0]}) is None
