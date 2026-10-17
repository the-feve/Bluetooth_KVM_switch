"""The HID side of the proxy, with no Bluetooth or D-Bus in it so it can be unit-tested.

- the HID report descriptor and the SDP record the hosts read when they pair
- tables from Linux evdev key codes to USB HID usages
- KeyState: which keys are down, and the HID reports that describe that
- MouseState: buttons held and movement since the last report
- Hotkeys: the profile-switch shortcuts, which are kept away from the hosts

We re-build standard reports from evdev events instead of forwarding the keyboard's
raw USB reports. QMK boards (the Sinc included) expose several interfaces (6KRO boot,
NKRO, consumer, system, mouse, VIA raw HID) with their own descriptors, and a host
only understands the descriptor we advertised over Bluetooth.
"""

from evdev import ecodes as e

HID_UUID = "00001124-0000-1000-8000-00805f9b34fb"
KEYBOARD_ID = 1
CONSUMER_ID = 2
MOUSE_ID = 3

# Report 1: boot-style keyboard (modifier byte, reserved byte, 6 key slots) plus the
# 5 LED output bits. Report 2: one 16-bit consumer-control usage (media keys).
# Report 3: a mouse (5 buttons, 16-bit X/Y, wheel, horizontal wheel). One device
# with all three means each computer pairs once and gets both keyboard and mouse.
REPORT_DESCRIPTOR = bytes([
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x06,        # Usage (Keyboard)
    0xA1, 0x01,        # Collection (Application)
    0x85, KEYBOARD_ID, #   Report ID 1
    0x05, 0x07,        #   Usage Page (Keyboard/Keypad)
    0x19, 0xE0,        #   Usage Minimum (Left Control)
    0x29, 0xE7,        #   Usage Maximum (Right GUI)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1)
    0x75, 0x01,        #   Report Size (1)
    0x95, 0x08,        #   Report Count (8)
    0x81, 0x02,        #   Input (Data, Variable, Absolute)   modifiers
    0x95, 0x01,        #   Report Count (1)
    0x75, 0x08,        #   Report Size (8)
    0x81, 0x01,        #   Input (Constant)                   reserved
    0x95, 0x05,        #   Report Count (5)
    0x75, 0x01,        #   Report Size (1)
    0x05, 0x08,        #   Usage Page (LEDs)
    0x19, 0x01,        #   Usage Minimum (Num Lock)
    0x29, 0x05,        #   Usage Maximum (Kana)
    0x91, 0x02,        #   Output (Data, Variable, Absolute)  LEDs
    0x95, 0x01,        #   Report Count (1)
    0x75, 0x03,        #   Report Size (3)
    0x91, 0x01,        #   Output (Constant)                  padding
    0x95, 0x06,        #   Report Count (6)
    0x75, 0x08,        #   Report Size (8)
    0x15, 0x00,        #   Logical Minimum (0)
    0x26, 0xFF, 0x00,  #   Logical Maximum (255)  (2 bytes: 0x25 0xFF would mean -1)
    0x05, 0x07,        #   Usage Page (Keyboard/Keypad)
    0x19, 0x00,        #   Usage Minimum (0)
    0x29, 0xFF,        #   Usage Maximum (255)
    0x81, 0x00,        #   Input (Data, Array)                6 key slots
    0xC0,              # End Collection
    0x05, 0x0C,        # Usage Page (Consumer)
    0x09, 0x01,        # Usage (Consumer Control)
    0xA1, 0x01,        # Collection (Application)
    0x85, CONSUMER_ID, #   Report ID 2
    0x15, 0x00,        #   Logical Minimum (0)
    0x26, 0xFF, 0x03,  #   Logical Maximum (0x3FF)
    0x19, 0x00,        #   Usage Minimum (0)
    0x2A, 0xFF, 0x03,  #   Usage Maximum (0x3FF)
    0x75, 0x10,        #   Report Size (16)
    0x95, 0x01,        #   Report Count (1)
    0x81, 0x00,        #   Input (Data, Array)
    0xC0,              # End Collection
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x02,        # Usage (Mouse)
    0xA1, 0x01,        # Collection (Application)
    0x85, MOUSE_ID,    #   Report ID 3
    0x09, 0x01,        #   Usage (Pointer)
    0xA1, 0x00,        #   Collection (Physical)
    0x05, 0x09,        #     Usage Page (Buttons)
    0x19, 0x01,        #     Usage Minimum (1)
    0x29, 0x05,        #     Usage Maximum (5)
    0x15, 0x00,        #     Logical Minimum (0)
    0x25, 0x01,        #     Logical Maximum (1)
    0x95, 0x05,        #     Report Count (5)
    0x75, 0x01,        #     Report Size (1)
    0x81, 0x02,        #     Input (Data, Variable, Absolute)   buttons
    0x95, 0x01,        #     Report Count (1)
    0x75, 0x03,        #     Report Size (3)
    0x81, 0x01,        #     Input (Constant)                   padding
    0x05, 0x01,        #     Usage Page (Generic Desktop)
    0x09, 0x30,        #     Usage (X)
    0x09, 0x31,        #     Usage (Y)
    0x16, 0x01, 0x80,  #     Logical Minimum (-32767)
    0x26, 0xFF, 0x7F,  #     Logical Maximum (32767)
    0x75, 0x10,        #     Report Size (16)
    0x95, 0x02,        #     Report Count (2)
    0x81, 0x06,        #     Input (Data, Variable, Relative)   X, Y
    0x09, 0x38,        #     Usage (Wheel)
    0x15, 0x81,        #     Logical Minimum (-127)
    0x25, 0x7F,        #     Logical Maximum (127)
    0x75, 0x08,        #     Report Size (8)
    0x95, 0x01,        #     Report Count (1)
    0x81, 0x06,        #     Input (Data, Variable, Relative)   wheel
    0x05, 0x0C,        #     Usage Page (Consumer)
    0x0A, 0x38, 0x02,  #     Usage (AC Pan)
    0x95, 0x01,        #     Report Count (1)
    0x81, 0x06,        #     Input (Data, Variable, Relative)   horizontal wheel
    0xC0,              #   End Collection
    0xC0,              # End Collection
])

EMPTY_KEYBOARD = bytes([KEYBOARD_ID, 0, 0, 0, 0, 0, 0, 0, 0])
EMPTY_CONSUMER = bytes([CONSUMER_ID, 0, 0])
EMPTY_MOUSE = bytes([MOUSE_ID, 0, 0, 0, 0, 0, 0, 0])

MOUSE_BUTTONS = {e.BTN_LEFT: 0x01, e.BTN_RIGHT: 0x02, e.BTN_MIDDLE: 0x04, e.BTN_SIDE: 0x08, e.BTN_EXTRA: 0x10}

MODIFIER_BITS = {
    e.KEY_LEFTCTRL: 0x01, e.KEY_LEFTSHIFT: 0x02, e.KEY_LEFTALT: 0x04, e.KEY_LEFTMETA: 0x08,
    e.KEY_RIGHTCTRL: 0x10, e.KEY_RIGHTSHIFT: 0x20, e.KEY_RIGHTALT: 0x40, e.KEY_RIGHTMETA: 0x80,
}

# evdev key code -> HID Keyboard page usage. Inverse of hid_keyboard[] in the
# kernel's drivers/hid/hid-input.c, for the keys a normal keyboard sends.
KEY_USAGES = {}


def _run(start, names):
    for i, name in enumerate(names.split()):
        KEY_USAGES[getattr(e, "KEY_" + name)] = start + i


_run(0x04, "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z")
_run(0x1E, "1 2 3 4 5 6 7 8 9 0 ENTER ESC BACKSPACE TAB SPACE MINUS EQUAL "
           "LEFTBRACE RIGHTBRACE BACKSLASH")
_run(0x33, "SEMICOLON APOSTROPHE GRAVE COMMA DOT SLASH CAPSLOCK "
           "F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 F11 F12 SYSRQ SCROLLLOCK PAUSE "
           "INSERT HOME PAGEUP DELETE END PAGEDOWN RIGHT LEFT DOWN UP "
           "NUMLOCK KPSLASH KPASTERISK KPMINUS KPPLUS KPENTER "
           "KP1 KP2 KP3 KP4 KP5 KP6 KP7 KP8 KP9 KP0 KPDOT 102ND COMPOSE POWER KPEQUAL "
           "F13 F14 F15 F16 F17 F18 F19 F20 F21 F22 F23 F24")
# Keyboard-page Power (0x66) can shut a Windows PC down; don't pass it on.
del KEY_USAGES[e.KEY_POWER]
KEY_USAGES.update({
    e.KEY_KPCOMMA: 0x85, e.KEY_RO: 0x87, e.KEY_KATAKANAHIRAGANA: 0x88, e.KEY_YEN: 0x89,
    e.KEY_HENKAN: 0x8A, e.KEY_MUHENKAN: 0x8B, e.KEY_HANGEUL: 0x90, e.KEY_HANJA: 0x91,
})

# evdev key code -> HID Consumer page usage (what QMK's media keys send).
CONSUMER_USAGES = {
    e.KEY_MUTE: 0xE2, e.KEY_VOLUMEUP: 0xE9, e.KEY_VOLUMEDOWN: 0xEA,
    e.KEY_PLAYPAUSE: 0xCD, e.KEY_NEXTSONG: 0xB5, e.KEY_PREVIOUSSONG: 0xB6,
    e.KEY_STOPCD: 0xB7, e.KEY_FASTFORWARD: 0xB3, e.KEY_REWIND: 0xB4, e.KEY_EJECTCD: 0xB8,
    e.KEY_BRIGHTNESSUP: 0x6F, e.KEY_BRIGHTNESSDOWN: 0x70,
    e.KEY_MAIL: 0x18A, e.KEY_CALC: 0x192, e.KEY_FILE: 0x194, e.KEY_COMPUTER: 0x194,
    e.KEY_SEARCH: 0x221, e.KEY_HOMEPAGE: 0x223, e.KEY_BACK: 0x224, e.KEY_FORWARD: 0x225,
    e.KEY_REFRESH: 0x227, e.KEY_BOOKMARKS: 0x22A,
}


def key_code(name):
    """'KEY_F21' or 'F21' -> evdev code. Raises ValueError for a typo in the config."""
    name = name.upper()
    if not name.startswith("KEY_"):
        name = "KEY_" + name
    code = getattr(e, name, None)
    if not isinstance(code, int):
        raise ValueError(f"unknown key name {name!r}")
    return code


class KeyState:
    """Keys held on the physical keyboard, and the reports that describe them.

    `suppressed` holds keys that were down when we switched host: the new host must not
    see them (it would get a stray Ctrl from the switch chord), so they stay hidden
    until they are released.
    """

    def __init__(self):
        self.pressed = []          # press order, so the 6 slots fill like a real keyboard
        self.suppressed = set()
        self.consumer = []         # consumer usages held, newest last
        self._last = {}            # report id -> last report produced

    def event(self, code, down):
        """Apply one key event. Returns the changed report (bytes), or None."""
        if code in CONSUMER_USAGES:
            usage = CONSUMER_USAGES[code]
            if down:
                self.consumer.append(usage)
            elif usage in self.consumer:
                self.consumer.remove(usage)
            return self._changed(self.consumer_report())
        if code in KEY_USAGES or code in MODIFIER_BITS:
            if down:
                if code not in self.pressed:
                    self.pressed.append(code)
            else:
                if code in self.pressed:
                    self.pressed.remove(code)
                self.suppressed.discard(code)
            return self._changed(self.keyboard_report())
        return None  # system-control, mouse buttons, etc.: not forwarded

    def keyboard_report(self):
        mods = 0
        keys = []
        for code in self.pressed:
            if code in self.suppressed:
                continue
            if code in MODIFIER_BITS:
                mods |= MODIFIER_BITS[code]
            else:
                keys.append(KEY_USAGES[code])
        if len(keys) > 6:
            keys = [0x01] * 6      # ErrorRollOver: "too many keys", as real 6KRO boards do
        keys += [0] * (6 - len(keys))
        return bytes([KEYBOARD_ID, mods, 0] + keys)

    def consumer_report(self):
        usage = self.consumer[-1] if self.consumer else 0
        return bytes([CONSUMER_ID, usage & 0xFF, usage >> 8])

    def _changed(self, report):
        if self._last.get(report[0]) == report:
            return None
        self._last[report[0]] = report
        return report

    def switched_host(self):
        """Call after changing host: hide held keys and resend from a clean slate."""
        self.suppressed = set(self.pressed)
        self.consumer.clear()
        self._last.clear()

    def clear(self):
        """Keyboard unplugged: everything is up."""
        self.pressed.clear()
        self.suppressed.clear()
        self.consumer.clear()
        self._last.clear()


def _clamp(v, lim):
    return max(-lim, min(lim, v))


class MouseState:
    """A mouse's buttons, and the movement added up since the last report.

    USB mice report up to 1000 times a second; Bluetooth carries far fewer, so
    movement is summed between reports (nothing is lost, it just arrives in
    bigger steps). What doesn't fit one report's range is kept for the next."""

    def __init__(self):
        self.buttons = 0
        self.dx = self.dy = self.wheel = self.pan = 0

    def event(self, etype, code, value):
        """Apply one evdev event. Returns True if a button changed (send now)."""
        if etype == e.EV_KEY and code in MOUSE_BUTTONS:
            bit = MOUSE_BUTTONS[code]
            before = self.buttons
            self.buttons = (self.buttons | bit) if value else (self.buttons & ~bit)
            return self.buttons != before
        if etype == e.EV_REL:
            if code == e.REL_X:
                self.dx += value
            elif code == e.REL_Y:
                self.dy += value
            elif code == e.REL_WHEEL:
                self.wheel += value
            elif code == e.REL_HWHEEL:
                self.pan += value
        return False

    @property
    def moved(self):
        return bool(self.dx or self.dy or self.wheel or self.pan)

    def report(self):
        """The next report; takes the movement it carries out of the totals."""
        x, y = _clamp(self.dx, 32767), _clamp(self.dy, 32767)
        w, h = _clamp(self.wheel, 127), _clamp(self.pan, 127)
        self.dx, self.dy, self.wheel, self.pan = self.dx - x, self.dy - y, self.wheel - w, self.pan - h
        return bytes([MOUSE_ID, self.buttons]) + x.to_bytes(2, "little", signed=True) + \
            y.to_bytes(2, "little", signed=True) + w.to_bytes(1, "little", signed=True) + h.to_bytes(1, "little", signed=True)

    def clear(self):
        self.buttons = 0
        self.dx = self.dy = self.wheel = self.pan = 0


class Hotkeys:
    """Profile-switch shortcuts. Their key presses are swallowed (never sent to a host).

    direct: {code: action}, e.g. F21 -> "host1", fired on press.
    chord_mods + chord_keys: holding every key in chord_mods and pressing a chord key
    fires its action. The modifiers themselves still reach the host; KeyState hides them
    from the new host after a switch.
    """

    def __init__(self, direct, chord_mods, chord_keys):
        self.direct = dict(direct)
        self.chord_mods = set(chord_mods)
        self.chord_keys = dict(chord_keys)
        self._swallowed = set()

    def check(self, code, down, held):
        """Returns (swallow, action). `held` = keys currently down, before this event."""
        if not down:
            if code in self._swallowed:
                self._swallowed.discard(code)
                return True, None
            return False, None
        if code in self.direct:
            self._swallowed.add(code)
            return True, self.direct[code]
        if code in self.chord_keys and self.chord_mods and self.chord_mods <= set(held):
            self._swallowed.add(code)
            return True, self.chord_keys[code]
        return False, None


def sdp_record(name):
    """The SDP service record (BlueZ XML) that tells hosts we are a HID keyboard."""
    desc = REPORT_DESCRIPTOR.hex()
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<record>
  <attribute id="0x0001"><sequence><uuid value="0x1124" /></sequence></attribute>
  <attribute id="0x0004">
    <sequence>
      <sequence><uuid value="0x0100" /><uint16 value="0x0011" /></sequence>
      <sequence><uuid value="0x0011" /></sequence>
    </sequence>
  </attribute>
  <attribute id="0x0005"><sequence><uuid value="0x1002" /></sequence></attribute>
  <attribute id="0x0006">
    <sequence><uint16 value="0x656e" /><uint16 value="0x006a" /><uint16 value="0x0100" /></sequence>
  </attribute>
  <attribute id="0x0009">
    <sequence><sequence><uuid value="0x1124" /><uint16 value="0x0101" /></sequence></sequence>
  </attribute>
  <attribute id="0x000d">
    <sequence><sequence>
      <sequence><uuid value="0x0100" /><uint16 value="0x0013" /></sequence>
      <sequence><uuid value="0x0011" /></sequence>
    </sequence></sequence>
  </attribute>
  <attribute id="0x0100"><text value="{name}" /></attribute>
  <attribute id="0x0101"><text value="USB to Bluetooth keyboard" /></attribute>
  <attribute id="0x0102"><text value="bt-kvm" /></attribute>
  <attribute id="0x0200"><uint16 value="0x0100" /></attribute>
  <attribute id="0x0201"><uint16 value="0x0111" /></attribute>
  <attribute id="0x0202"><uint8 value="0x40" /></attribute>
  <attribute id="0x0203"><uint8 value="0x00" /></attribute>
  <attribute id="0x0204"><boolean value="true" /></attribute>
  <attribute id="0x0205"><boolean value="true" /></attribute>
  <attribute id="0x0206">
    <sequence><sequence>
      <uint8 value="0x22" />
      <text encoding="hex" value="{desc}" />
    </sequence></sequence>
  </attribute>
  <attribute id="0x0207">
    <sequence><sequence><uint16 value="0x0409" /><uint16 value="0x0100" /></sequence></sequence>
  </attribute>
  <attribute id="0x020b"><uint16 value="0x0100" /></attribute>
  <attribute id="0x020c"><uint16 value="0x0c80" /></attribute>
  <attribute id="0x020d"><boolean value="true" /></attribute>
  <attribute id="0x020e"><boolean value="false" /></attribute>
</record>
"""
