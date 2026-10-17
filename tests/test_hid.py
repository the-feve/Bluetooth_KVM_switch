"""Unit tests for the parts that don't need Bluetooth: tables, reports, hotkeys."""
import xml.etree.ElementTree as ET

from evdev import ecodes as e

from bt_kvm.hid import (CONSUMER_USAGES, EMPTY_KEYBOARD, KEY_USAGES, REPORT_DESCRIPTOR,
                        Hotkeys, KeyState, key_code, sdp_record)
from bt_kvm.main import DEFAULT_CONFIG


def test_usage_table_matches_hid_spec():
    assert KEY_USAGES[e.KEY_A] == 0x04
    assert KEY_USAGES[e.KEY_Z] == 0x1D
    assert KEY_USAGES[e.KEY_1] == 0x1E
    assert KEY_USAGES[e.KEY_0] == 0x27
    assert KEY_USAGES[e.KEY_BACKSLASH] == 0x31
    assert KEY_USAGES[e.KEY_SEMICOLON] == 0x33
    assert KEY_USAGES[e.KEY_F12] == 0x45
    assert KEY_USAGES[e.KEY_UP] == 0x52
    assert KEY_USAGES[e.KEY_KPDOT] == 0x63
    assert KEY_USAGES[e.KEY_COMPOSE] == 0x65
    assert KEY_USAGES[e.KEY_KPEQUAL] == 0x67
    assert KEY_USAGES[e.KEY_F13] == 0x68
    assert KEY_USAGES[e.KEY_F24] == 0x73
    assert e.KEY_POWER not in KEY_USAGES
    assert len(set(KEY_USAGES.values())) == len(KEY_USAGES)  # no two keys share a usage


def test_media_keys_are_consumer_usages():
    assert CONSUMER_USAGES[e.KEY_VOLUMEUP] == 0xE9
    assert CONSUMER_USAGES[e.KEY_PLAYPAUSE] == 0xCD
    assert not set(CONSUMER_USAGES) & set(KEY_USAGES)


def test_typing_and_modifiers():
    k = KeyState()
    assert k.event(e.KEY_LEFTSHIFT, True) == bytes([1, 0x02, 0, 0, 0, 0, 0, 0, 0])
    assert k.event(e.KEY_A, True) == bytes([1, 0x02, 0, 0x04, 0, 0, 0, 0, 0])
    assert k.event(e.KEY_A, False) == bytes([1, 0x02, 0, 0, 0, 0, 0, 0, 0])
    assert k.event(e.KEY_LEFTSHIFT, False) == EMPTY_KEYBOARD


def test_rollover_and_dedupe():
    k = KeyState()
    for code in (e.KEY_A, e.KEY_S, e.KEY_D, e.KEY_F, e.KEY_G, e.KEY_H):
        k.event(code, True)
    assert k.event(e.KEY_J, True)[3:] == bytes([1] * 6)
    assert k.event(e.BTN_LEFT, True) is None  # mouse buttons are not forwarded
    assert k.event(e.KEY_J, True) is None  # same state again: nothing to send


def test_consumer_report():
    k = KeyState()
    assert k.event(e.KEY_VOLUMEUP, True) == bytes([2, 0xE9, 0x00])
    assert k.event(e.KEY_CALC, True) == bytes([2, 0x92, 0x01])
    assert k.event(e.KEY_CALC, False) == bytes([2, 0xE9, 0x00])
    assert k.event(e.KEY_VOLUMEUP, False) == bytes([2, 0, 0])


def test_switch_hides_held_keys_until_released():
    k = KeyState()
    k.event(e.KEY_LEFTCTRL, True)
    k.switched_host()
    assert k.keyboard_report() == EMPTY_KEYBOARD
    assert k.event(e.KEY_C, True) == bytes([1, 0, 0, 0x06, 0, 0, 0, 0, 0])
    k.event(e.KEY_LEFTCTRL, False)
    assert k.event(e.KEY_LEFTCTRL, True) == bytes([1, 0x01, 0, 0x06, 0, 0, 0, 0, 0])


def test_hotkeys_direct_and_chord():
    h = Hotkeys({e.KEY_F21: "host1"}, [e.KEY_LEFTCTRL, e.KEY_RIGHTCTRL], {e.KEY_2: "host2"})
    assert h.check(e.KEY_F21, True, []) == (True, "host1")
    assert h.check(e.KEY_F21, False, []) == (True, None)
    assert h.check(e.KEY_2, True, [e.KEY_LEFTCTRL]) == (False, None)
    assert h.check(e.KEY_2, False, [e.KEY_LEFTCTRL]) == (False, None)
    assert h.check(e.KEY_2, True, [e.KEY_LEFTCTRL, e.KEY_RIGHTCTRL]) == (True, "host2")
    assert h.check(e.KEY_2, False, []) == (True, None)


def test_default_config_key_names_resolve():
    for name in list(DEFAULT_CONFIG["hotkeys"]) + DEFAULT_CONFIG["chord_modifiers"] + \
            list(DEFAULT_CONFIG["chord_keys"]):
        key_code(name)
    assert key_code("f21") == e.KEY_F21


def test_descriptor_and_sdp_record():
    assert REPORT_DESCRIPTOR.count(0xA1) >= 2 and REPORT_DESCRIPTOR[-1] == 0xC0
    root = ET.fromstring(sdp_record("Test").encode())
    ids = {a.get("id") for a in root.findall("attribute")}
    assert {"0x0001", "0x0004", "0x000d", "0x0206"} <= ids
    hexdesc = root.find(".//attribute[@id='0x0206']//text").get("value")
    assert bytes.fromhex(hexdesc) == REPORT_DESCRIPTOR
