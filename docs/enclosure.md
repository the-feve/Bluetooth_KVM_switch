# Enclosure: Pi 4 dimensions and case rules

These figures come from the official Raspberry Pi 4 Model B mechanical drawing
(datasheets.raspberrypi.com). Check them with calipers on your own board before you
print the final case. Connector overhang in particular varies by a few tenths of a mm.

## Board

Coordinates use the bottom-left corner of the board as (0, 0). The "bottom" edge is
the long edge with USB-C and HDMI. The "left" edge has the microSD card.

| Item | Value |
|---|---|
| PCB outline | 85.0 × 56.0 mm, 3 mm corner radius, about 1.4 mm thick |
| Mounting holes | Ø 2.7 mm (M2.5), centres at (3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5); 58 × 49 mm spacing; 6 mm keep-out pad around each |
| Tallest parts | USB-A stack and Ethernet jack, about 16 mm above the top of the PCB |
| Underside | through-hole pins and the microSD socket, up to about 2.5 mm below the PCB |
| GPIO header | 2 × 20 along the top edge, row centre 3.5 mm from that edge, centred at x = 32.5; pins stand about 8.5 mm above the PCB |

### Connectors

| Edge | Connector | Centre position | Notes |
|---|---|---|---|
| Right (x = 85) | USB 3.0 pair (blue) | y = 9.0 | Housing sticks out about 2–3 mm past the PCB edge |
| Right | **USB 2.0 pair (black), use for the keyboard** | y = 27.0 | Option A: the USB-C→A adapter plugs in here and passes through the side wall |
| Right | Ethernet | y = 45.75 | Keep it reachable for wired SSH if you turn Wi-Fi off |
| Bottom (y = 0) | **USB-C power** | x = 11.2 | Option A: this *is* the box's power port; put the board's bottom edge about 1 mm from the front wall |
| Bottom | micro-HDMI 0 / 1 | x = 26.0 / 39.5 | Not needed after setup; a cover is fine |
| Bottom | 3.5 mm audio | x = 53.5 | not needed |
| Left (x = 0) | microSD (underside) | about y = 28 | Card sticks out about 2.5 mm. Leave a slot of at least 14 × 3 mm, or a removable panel |

## Clearance rules for the case (FDM)

1. **Standoffs:** 3 mm tall, Ø 6 mm, with M2.5 heat-set inserts. That clears the
   underside pins and the SD socket.
2. **Gaps:** about 1 mm between the PCB edge and the inner walls, except on the port
   sides. There the connector faces should sit about 0.5 mm inside the wall's inner
   face, so plugs seat fully.
3. **Port openings:** the connector body plus 0.5 mm per side, and room for the
   **plug's moulded housing**, not just the metal tip. A USB-A plug housing is about
   16 × 8 mm; a USB-C plug housing is about 12 × 6.5 mm. Thin the wall to 1.2–1.5 mm
   around the openings, or recess them from outside, so long housings don't bottom
   out.
4. **Fits:** start at 0.2 mm per side for slip fits and the lid lip. Print a fit-test
   coupon with your printer and filament before printing the full case.
5. **Bluetooth antenna:** the Pi 4's printed antenna sits next to the shielded
   wireless module at the pin-1 (SD card) end of the GPIO header. Keep **plastic only**
   within about 10 mm of it: no inserts, screws, magnets, wires, metal tape, or
   carbon-fibre/conductive filament. Don't run the keyboard's USB cable across that
   corner. Point that end of the box toward the computers if you can.
6. **Heat:** about 3 W in a closed box. Put vent slots over the SoC (the board
   centre) and along the bottom walls (about 30 mm² total each side is plenty), plus
   the stick-on heatsink. **PETG or ASA** is safer than PLA, which softens around
   55–60 °C.
7. **USB-C ports (see hardware.md, "USB-C on the box"):**
   - *Option A:* the Pi's USB-C power port and a USB-C→A adapter in a black USB 2.0
     port. The adapter's USB-C face sits flush with (or up to 0.5 mm inside) the
     outer wall. Around it, a printed **collar** 6–8 mm deep grips the adapter body
     (+0.15 mm per side; measure the adapter), tied into the wall and floor, so cable
     tugs load the case instead of the Pi. The power cutout is in the front wall,
     over the Pi's USB-C port.
   - *Option B:* panel-mount extensions screwed to the wall (measure the flange and
     screw spacing; they vary), plus room inside for the plugs: about 35 mm beyond a
     straight USB-A plug, 25 mm with right-angle plugs. Tie the cables down inside.
   - USB-C opening for the cable's plug: 12.5 × 7 mm minimum (the moulded housing),
     with the wall thinned to 1.2–1.5 mm around it so the plug seats fully.
   - Emboss **PWR ⚡** and **KB ⌨** next to the ports, ideally on different walls.
8. **Button and LEDs:** a 12 mm panel button needs a 12.2 mm hole and a wall of 2 mm or
   less. For a 6×6 tactile switch on perfboard, print a plunger with 0.3 mm clearance
   in its guide. 3 mm LEDs: a 3.0 mm hole for a press fit, or print light pipes in
   clear or natural PETG.
9. **Size:** Option A is about 100 × 66 mm inside (the Pi plus the adapter sticking
   out about 13 mm past the USB port) and 30 mm tall, so roughly 106 × 72 × 34 mm
   outside with 3 mm walls. Option B adds about 25–35 mm in one direction for the
   plugs.
10. **Feet:** rubber feet, or 1 mm recesses for them, so the box doesn't slide when you
    plug in a cable.

## One case with the keyboard, or a separate box?

**Use a separate box.** Reasons:

- The Sinc is a split board. You move and tent the halves, and the cable between them
  needs to stay free. A Pi 4 (85 × 56 × 16 mm, warm, with a power cable) bolted to one
  half makes that half heavy and fixes where it can go.
- Radio: the antenna works best away from hands, desk metal and the keyboard's own
  plate and wiring, ideally in view of both PCs. A box on the desk or on the monitor
  stand does that.
- The Sinc stays a normal wired keyboard. For BIOS, BitLocker or gaming you just move
  its USB cable to the PC.
- It's easy to service: SD card, Ethernet and HDMI stay reachable, and you can reprint
  the box without touching the keyboard.

A middle ground, if you want it to look like part of the keyboard: print the box in
the same colour and stick it under the desk or monitor stand with Velcro, with a
0.5–1 m cable to the keyboard.
