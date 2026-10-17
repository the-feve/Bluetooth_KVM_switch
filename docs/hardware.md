# Hardware: which Pi, what to buy, wiring

## Which Pi?

Two features matter here. The Pi has to be a **USB host**, to read the keyboard, and it
has to be a **Bluetooth Classic device**, to type into the PCs. *USB gadget mode* is
the opposite role (the Pi pretending to be a USB keyboard on a cable), so this project
doesn't need it.

| | Pi 4 Model B (what we use) | Pi Zero 2 W | Pi 5 |
|---|---|---|---|
| Bluetooth | 5.0, Classic + LE | 4.2, Classic + LE | 5.0 |
| USB host ports | 2× USB 2.0 + 2× USB 3.0, full size | 1 micro-USB OTG (adapter needed) | 2+2 |
| Power while idle | about 2.7–3.5 W | about 0.6–0.8 W | about 3–4 W |
| Board size | 85 × 56 mm | 65 × 30 mm | 85 × 56 mm |
| Latency | Bluetooth link dominates (5–20 ms); CPU irrelevant | same | same |
| Gadget mode | USB-C only, which is also the power input | the OTG port (needed for the keyboard here) | USB-C |

**Use the Pi 4 you have.** The keyboard plugs straight into a full-size USB-A port and
the Pi powers it, so you need **no power splitter and no OTG adapter**. The extra
power draw doesn't matter for a box that sits on a desk on mains power. The Zero 2 W
only wins if you want a tiny or battery-powered dongle. The code is the same on any
Pi with built-in Bluetooth; only the case changes.

(If your "2nd edition, updated for Pi 4" unit turns out to be a Pi 400, which has a
built-in keyboard, or a Pi 3, it will still work, but the case notes in
[enclosure.md](enclosure.md) assume a Pi 4 Model B.)

## Shopping list

**What the owner has (2026-10-17): a Vilros Raspberry Pi 4 kit.** It includes a Pi 4 Model B
(4 GB), a Vilros USB-C 5.1 V 3 A supply with an on/off switch (fine in place of the
official one; switch off only after `sudo poweroff`), a Vilros black case with fan (a
stand-in until the custom box exists; fan on GPIO pins 4 and 6, no clash with ours), a
microSD card (gets reflashed) and a micro-HDMI adapter (not needed). Still to buy: the
USB-C→A adapter, a C-to-C cable, and the button/LED parts.


| Qty | Part | Notes |
|---|---|---|
| 1 | Raspberry Pi 4 Model B | you have it (Vilros kit, 4 GB) |
| 1 | **Official Raspberry Pi 15 W USB-C power supply** (5.1 V 3 A) | Phone chargers sag in voltage, and Bluetooth gets flaky when the Pi runs low. The Pi 4's USB ports share a 1.2 A budget, plenty for the Sinc. |
| 1 | microSD, 16–32 GB, A1, "High Endurance" type | e.g. SanDisk High Endurance |
| 1 | **USB-C to USB-C cable**, 0.5–1 m | Sinc to the box's USB-C keyboard port. Any C-to-C cable carries keyboard data. |
| 1 | **USB-C (female) to USB-A (male) adapter**, short, data-capable | Makes the box's keyboard port USB-C (Option A below). Get a *data* one, not "charge only"; ones with a 56 kΩ resistor are the in-spec kind. Measure it before the case CAD is finalised. |
| 1 | Pi 4 heatsink set (stick-on) | optional; the load is light but the case is closed |
| 1 | Mini momentary panel push button, 7 mm thread (e.g. PBS-110 style) | profile toggle / pairing; fits the desk-organizer box |
| 2 | 3 mm LEDs, two colours (say green = host 1, blue = host 2) | or one common-cathode bicolour LED |
| 2 | 330 Ω resistors, ¼ W | one per LED |
| 1 | Female Dupont jumpers or a 2×20 female header, heat-shrink | so the Pi stays removable |
| 4 + 4 | M2.5 × 6 mm screws, M2.5 heat-set inserts | Pi mounting |
| 4 | M3 × 8 countersunk screws + M3 heat-set inserts | tray to lid |
| 4 | Rubber feet | |
| *opt. B* | Panel-mount **USB-C (female) to USB-A (male)** extension, 20–30 cm, right-angle A plug if you can | keyboard port anywhere on the case (Option B) |
| *opt. B* | Panel-mount **USB-C (female) to USB-C (male)** extension, 20–30 cm, rated 3 A, right-angle plug if you can | power port anywhere on the case (Option B) |
| *opt.* | Small perfboard (about 30 × 20 mm) | carries the button, LEDs and resistors |

**Batteries:** not recommended. A Pi 4 draws about 3 W, so a 10,000 mAh power bank
lasts only about 10–12 hours. A battery build would need a different board, such as a
Zero 2 W with a PiSugar, plus a power-off routine.

## USB-C on the box: power in and keyboard in

Both ports on the box are USB-C. Power is easy, since the Pi 4's power input is already
USB-C. The keyboard needs one adapter, because the Pi 4's host ports are all USB-A.

**Option A, compact (recommended):**

- **Power:** the Pi's own USB-C power port sits behind an opening in the right side
  of the box. No extra parts.
- **Keyboard:** a short USB-C (female) to USB-A (male) adapter plugs into a **black
  USB 2.0 port**, and its USB-C face sits flush with the front face. A printed collar
  in the case grips the adapter body, so pulling the keyboard cable loads the case,
  not the Pi's USB port.
- The two ports are on **different faces** (KB in front, PWR on the right), so they're
  hard to mix up. See enclosure.md, "Desk organizer mount".

**Option B, panel-mount cables:** two short panel-mount extensions (C→A for the
keyboard, C→C for power) let you put both sockets wherever you like, for example side
by side on the back wall. It's tidier on the desk, but the box gets bigger (room
for the plugs and cable bends; right-angle plugs help) and there are two more
connections that can work loose.

**Rules for both options:**

- **Label the ports on the case** (emboss "PWR" with a ⚡ and "KB" with a keyboard
  icon). The keyboard port is *not* a power input. Some USB-C power supplies put
  out 5 V as soon as they're plugged in, and that would push power backwards into
  the Pi's USB port.
- Power with the **official supply**. Early Pi 4 boards (rev 1.1) don't power up from
  some USB-C laptop chargers with "smart" (e-marked) C-to-C cables.
- Wiring 5 V straight to GPIO pins 2/4 + 6 also powers the Pi, but it bypasses the
  Pi's input protection. Not needed here.

## Wiring (BCM numbering, 40-pin header)

```
 Button:  GPIO17 (pin 11) ──[button]── GND (pin 9)        internal pull-up, no resistor
 LED 1:   GPIO23 (pin 16) ──[330 Ω]──►|── GND (pin 14)     host 1
 LED 2:   GPIO24 (pin 18) ──[330 Ω]──►|── GND (pin 20)     host 2
                                    (long leg = anode, toward the resistor/GPIO)
```

You can change the pins in `/etc/bt-kvm/config.json` (`gpio_button`,
`gpio_led_host1`, `gpio_led_host2`). Set any of them to `null` to leave it out.
