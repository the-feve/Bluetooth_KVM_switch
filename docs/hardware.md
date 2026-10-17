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
button/LED parts, and a USB mouse if you don't have a spare.


| Qty | Part | Notes |
|---|---|---|
| 1 | Raspberry Pi 4 Model B | you have it (Vilros kit, 4 GB) |
| 1 | **Official Raspberry Pi 15 W USB-C power supply** (5.1 V 3 A) | Phone chargers sag in voltage, and Bluetooth gets flaky when the Pi runs low. The Pi 4's USB ports share a 1.2 A budget, plenty for the Sinc. |
| 1 | microSD, 16–32 GB, A1, "High Endurance" type | e.g. SanDisk High Endurance |
| 1 | **USB-C (keyboard) to USB-A (Pi) cable**, 0.5–1 m | the Sinc's own cable, if it's C-to-A |
| 1 | **USB mouse** | wired, or wireless with a USB dongle; both work |
| 1 | Pi 4 heatsink set (stick-on) | optional; the load is light but the case is closed |
| 2 | Mini momentary panel push buttons, 7 mm thread (e.g. PBS-110 style) | front: Keyboard and Mouse |
| 4 | 3 mm LEDs, two colours (say 2 green = host 1, 2 blue = host 2) | one pair beside each button |
| 4 | 330 Ω resistors, ¼ W | one per LED |
| 1 | Female Dupont jumpers or a 2×20 female header, heat-shrink | so the Pi stays removable |
| 4 + 4 | M2.5 × 6 mm screws, M2.5 heat-set inserts | Pi mounting |
| 4 | M3 × 8 countersunk screws + M3 heat-set inserts | tray to lid |
| 4 | Rubber feet | |
| 1 | Small perfboard (about 70 × 20 mm) | carries the buttons, LEDs and resistors behind the front panel |

**Batteries:** not recommended. A Pi 4 draws about 3 W, so a 10,000 mAh power bank
lasts only about 10–12 hours. A battery build would need a different board, such as a
Zero 2 W with a PiSugar, plus a power-off routine.

## Ports on the box

The case keeps the Pi's own layout, which also keeps it small:

- **Back:** the four USB ports, all left open. The keyboard and mouse go in the two
  **black USB 2.0** ports; the blue USB 3.0 ports stay free for later. Ethernet is
  covered (not used).
- **Side:** the Pi's own **USB-C power** port, on its long edge.
- **Front:** the two buttons, **Keyboard** and **Mouse**, each with its pair of LEDs.

No adapters or extension cables are needed: everything plugs straight into the Pi.
Power with the official supply or a kit supply rated 5.1 V 3 A. Early Pi 4 boards
(rev 1.1) don't power up from some USB-C laptop chargers with "smart" (e-marked) C-to-C
cables.

## Wiring (BCM numbering, 40-pin header)

All of the buttons and LEDs share one ground wire, so the front-panel perfboard needs
seven wires to the Pi. The buttons and ground are on the header's inner row, the four
LEDs on the outer row:

```
 GND ............ pin 9   (shared by both buttons and all four LED short legs)
 Keyboard button  GPIO17  pin 11 ──[button]── GND     internal pull-up, no resistor
 Mouse button     GPIO27  pin 13 ──[button]── GND
 Keyboard LED 1   GPIO18  pin 12 ──[330 Ω]──►|── GND  keyboard on host 1
 Keyboard LED 2   GPIO23  pin 16 ──[330 Ω]──►|── GND  keyboard on host 2
 Mouse LED 1      GPIO24  pin 18 ──[330 Ω]──►|── GND  mouse on host 1
 Mouse LED 2      GPIO25  pin 22 ──[330 Ω]──►|── GND  mouse on host 2
                                  (long leg = anode, toward the resistor/GPIO)
```

They're all within pins 9–22, so a single 2 × 7 female header (pins 9–22) can carry
them. (GPIO18 is also the PCM audio pin; that's off by default, so it's free.) The Vilros case fan, if fitted, stays on pins 4 and 6.

You can change the pins in `/etc/bt-kvm/config.json` (`buttons` and `leds`, each with
`kb` and `mouse`). Set any of them to `null` to leave it out.
