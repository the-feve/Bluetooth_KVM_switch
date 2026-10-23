# Add-on (planned): foot-pedal "stomp box"

> **Status: hardware not built or tested.** The software side is done and unit-tested.
> Do the main build first; you can add the pedal at any time after, with no setup.

A single foot switch in a 3D-printed pedal, like a guitar effects pedal, joined to the
main box by a cable. One stomp moves **the keyboard and the mouse together**:

| Pedal | Tap | Hold 3 s |
|---|---|---|
| **Swap both** | keyboard **and** mouse to the other computer | pair the computer the keyboard is on |

If the two are split (keyboard on one computer, mouse on the other), a tap brings both
to the computer the keyboard *isn't* on. So "tap = everything to the other PC" always
holds when they're together, and a split is undone in one stomp.

The two front buttons keep working as before, for moving just one of them.

## How it works: its own pin, already in the software

The pedal has its own Pi pin, **GPIO22 (pin 15)**, next to the two front-button pins.
The software already watches that pin (`"both": 22` under `buttons` in
`/etc/bt-kvm/config.json`). With no pedal plugged in, the pin just reads "not pressed",
so there's nothing to turn on: plug the pedal in and it works.

```
                        main box                         |  cable  |   stomp box
 Pi pin 15 (GPIO22) ──[1 kΩ]── socket D+ ────────────────┼─────────┼──[pedal switch]──┐
 Pi pin 14 (GND) ──────────── socket GND ────────────────┼─────────┼──────────────────┘
                              socket D− and VBUS: not connected (either end)
```

The pedal has no LEDs; the LEDs on the main box show where each device is.

## The cable: a USB cable used as plain wire

The link uses an ordinary USB cable and USB sockets, but **it isn't USB**: the cable
just carries two wires (the switch and a ground). That gives you a cheap, tough,
easy-to-replace cable that unplugs at both ends.

Use **USB-C**. It plugs in either way round, and USB-C cables are easy to find.

- **Sockets:** two USB-C female breakout boards that bring out **D+ and D−** (often sold
  as "USB-C 2.0 female breakout" or "24-pin breakout"). The common 6-pin "power only"
  boards bring out only VBUS, GND and CC, so they **won't work**. Check that the board
  joins A6 to B6 and A7 to B7 (nearly all do); then it doesn't matter which way up the
  plug goes in. Panel-mount USB-C sockets with screw holes are sturdier still.
- **Cable:** a USB-C to USB-C **data** cable (USB 2.0 is plenty), 1–3 m. **Charge-only
  cables have no D+/D− wires and won't work.** If your pedal does nothing, try another
  cable first.
- **VBUS (the 5 V wire) and D− stay unconnected at both ends.** That's what makes this safe if
  someone plugs the wrong thing in. A PC plugged into either socket can't push 5 V into
  the Pi's pins, and a USB gadget plugged into the main box's socket just gets no power.
  The 1 kΩ resistor protects the Pi's pins from anything else odd on the wire.
- **Label the socket** on the main box ("PEDAL, not USB") so nobody plugs a keyboard
  into it. It wouldn't do any harm, but it wouldn't work either.

**Simpler alternative (if USB-C breakouts are fiddly):** a 1/4" (6.35 mm) guitar jack
at each end with an ordinary instrument cable. This is how real footswitches connect:
tip = pedal (to the 1 kΩ and pin 15), sleeve = GND. Fit stereo (TRS) jacks if you'd
like room for a second pedal later; a mono cable still works in them.

### Long cables

Switching is slow, so cable length doesn't matter much. The Pi's built-in pull-up is
weak (about 50 kΩ), though, and a long cable near mains wiring can pick up noise and
cause a stray "press". If that happens, add a **10 kΩ resistor from pin 15 to 3.3 V
(pin 17)** on the main box's perfboard. With that, a 3 m cable
should be fine.

## The pedal: hard stops so your foot can't break the switch

The pedal uses the **same small panel push button as the front panel** (the 7 mm
PBS-110 style ones). They're made for a fingertip, not a foot, so the button must only
**signal** the press. The printed case takes the force.

```
  side view, one pedal (not to scale)

          hinge pin (M4 bolt)            treadle (your foot goes here)
             ◯═══════════════════════════════════════════════╗
             ║                    ▲ adjustable actuator       ║
             ║    return spring   ┃ (M3 set screw + nut)      ║   ▼ hard stop:
             ║      ≋≋≋           ┃                           ║   treadle lands on
             ║                  ┌─┴─┐ push button             ║   this rib/bumper
  ═══════════╩══════════════════╧═══╧═══════════════════════════╧═══ base
        heavy base, rubber feet        button mounted in base
```

1. **Treadle on a hinge.** A printed treadle pivots on an M4 bolt (or a 4 mm steel rod)
   through the back of the base.
2. **Hard stop.** Under the front of the treadle there's a printed rib or a stick-on
   rubber bumper that lands on the base. The treadle **stops there**, so stomping
   pushes the plastic into the base, not into the button.
3. **Adjustable actuator.** An M3 set screw in a heat-set insert on the treadle's
   underside presses the button. Turn it until the button clicks just before the
   treadle reaches the hard stop (about 0.3–0.5 mm before), then lock it with a nut.
   That way print tolerances don't matter, and the button is never pushed past its
   own travel. Measure your button's travel with calipers before setting the stop.
4. **Return spring.** The button's own spring is too weak to lift a treadle. Add a
   light compression spring (a pen spring works) between the base and treadle, or a
   printed flexure. A printed lip on the base keeps the treadle from lifting too far.
5. **Heavy, grippy base.** Rubber feet, and a pocket for some weight (steel washers or
   a bag of sand) so the box doesn't slide when you tap it.

**Rough sizes, to be checked in CAD:** base about 100 × 130 mm, front edge about 30 mm
tall, rising toward the back; one treadle about 80 mm wide; treadle travel 4–6 mm, of
which the button needs only the last 1–2 mm.

**Printing:** PETG (tougher than PLA, and it doesn't creep under load). Treadles with
4–5 walls and about 40% infill. Print the treadle flat, top face down. Put the USB-C
socket on the back of the base, held by screws, and add a cable clamp inside so a
tug on the cable doesn't pull on the solder joints.

## Extra parts

You already have the push buttons. Use a spare from the pack, or buy one more of the same.

| Qty | Part | Notes |
|---|---|---|
| 1 | Push button, same as the front panel | the pedal switch |
| 2 | USB-C female breakout with D+/D− (or panel-mount USB-C socket) | one in each box |
| 1 | USB-C to USB-C **data** cable, 1–3 m | not a charge-only cable |
| 1 | 1 kΩ resistor | in the main box |
| 1 | 10 kΩ resistor | optional, only if you get stray presses |
| 1 | M4 × 100 mm bolt + nyloc nut (or 4 mm rod) | treadle hinge (length to suit the CAD) |
| 1 | M3 × 10 mm set screw + M3 nut + M3 heat-set insert | adjustable actuator |
| 1–2 | Light compression springs, about 5–8 mm diameter | treadle return (pen springs) |
| 2–4 | Stick-on rubber bumpers | hard stops (or print them) |
| 4 | Rubber feet | |
| — | Hook-up wire, heat-shrink, M3 screws + inserts for the lid | |

## When you build it

- [ ] Check the breakout boards bring out D+/D− and join A6/B6 and A7/B7 (meter it).
- [ ] Wire the main box side first and test with a bare wire: touching D+ to GND on the
      socket should move both the keyboard and the mouse (all four LEDs swap), and
      `journalctl -u bt-kvm -f` should log both moves.
- [ ] Print a test treadle and base corner, then set the actuator and hard stop.
- [ ] Add it to the website build guide as an optional step.
