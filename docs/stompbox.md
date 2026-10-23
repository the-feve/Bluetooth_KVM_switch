# Add-on (planned): foot-pedal "stomp box"

> **Status: idea only. Nothing here has been built or tested.** Do the main build
> first. This add-on doesn't change the software, so you can add it at any time.

A second set of switches in a 3D-printed foot pedal, like a guitar effects pedal, joined
to the main box by a cable. The pedals do exactly what the front buttons do:

| Pedal | Tap | Hold 3 s |
|---|---|---|
| **Keyboard** (left) | keyboard to the other computer | pair the computer the keyboard is on |
| **Mouse** (right) | mouse to the other computer | pair the computer the mouse is on |

The front buttons keep working as before. Use whichever is closer to hand (or foot).

## How it works: wired in parallel, so no software changes

Each pedal is wired **in parallel with its front button**: both connect the same Pi pin
to ground. The Pi can't tell which one you pressed, so the software, the config file
and the 3 s hold all work unchanged.

```
                        main box                          |  cable  |   stomp box
 Pi pin 11 (GPIO17) ──┬──[front Keyboard button]── GND    |         |
                      └──[1 kΩ]── socket D+ ──────────────┼─────────┼── [Keyboard pedal] ──┐
 Pi pin 13 (GPIO27) ──┬──[front Mouse button]──── GND     |         |                      │
                      └──[1 kΩ]── socket D− ──────────────┼─────────┼── [Mouse pedal] ─────┤
 Pi pin 9  (GND) ──────────────── socket GND ─────────────┼─────────┼──────────────────────┘
                                  socket VBUS: not connected (either end)
```

The pedal has no LEDs; the LEDs on the main box still show where each device is.

## The cable: a USB cable used as plain wire

The link uses an ordinary USB cable and USB sockets, but **it isn't USB**: the cable
just carries three wires (two switches and a ground). That gives you a cheap, tough,
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
- **VBUS (the 5 V wire) stays unconnected at both ends.** That's what makes this safe if
  someone plugs the wrong thing in. A PC plugged into either socket can't push 5 V into
  the Pi's pins, and a USB gadget plugged into the main box's socket just gets no power.
  The 1 kΩ resistors protect the Pi's pins from anything else odd on the wire.
- **Label the socket** on the main box ("PEDAL, not USB") so nobody plugs a keyboard
  into it. It wouldn't do any harm, but it wouldn't work either.

**Simpler alternative (if USB-C breakouts are fiddly):** a 1/4" (6.35 mm) **stereo
(TRS)** guitar jack at each end, with a stereo jack cable. This is how real dual
footswitches connect: tip = Keyboard, ring = Mouse, sleeve = GND. Use the same 1 kΩ
resistors. Be sure it's a stereo cable (three bands on the plug), not a mono
instrument cable.

### Long cables

Switching is slow, so cable length doesn't matter much. The Pi's built-in pull-up is
weak (about 50 kΩ), though, and a long cable near mains wiring can pick up noise and
cause a stray "press". If that happens, add a **10 kΩ resistor from each pin (11 and
13) to 3.3 V (pin 1 or 17)** on the main box's perfboard. With that, a 3 m cable
should be fine.

## The pedal: hard stops so your foot can't break the switch

The pedals use the **same small panel push buttons as the front panel** (the 7 mm
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
   through the back of the base. Each pedal has its own treadle.
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

**Rough sizes, to be checked in CAD:** base about 160 × 120 mm, front edge about 30 mm
tall, rising toward the back; two treadles about 70 mm wide each with a small gap
between them; treadle travel 4–6 mm, of which the button needs only the last 1–2 mm.

**Printing:** PETG (tougher than PLA, and it doesn't creep under load). Treadles with
4–5 walls and about 40% infill. Print the treadle flat, top face down. Put the USB-C
socket on the back of the base, held by screws, and add a cable clamp inside so a
tug on the cable doesn't pull on the solder joints.

**Single-pedal version:** one treadle wired to the Keyboard line works the same way.
A pedal that moves **both** devices at once would need a small software change (its
own pin and a "swap both" action); note that if you want it.

## Extra parts

You already have the push buttons. Use two from the pack, or buy two more of the same.

| Qty | Part | Notes |
|---|---|---|
| 2 | Push buttons, same as the front panel | the pedal switches |
| 2 | USB-C female breakout with D+/D− (or panel-mount USB-C socket) | one in each box |
| 1 | USB-C to USB-C **data** cable, 1–3 m | not a charge-only cable |
| 2 | 1 kΩ resistors | in the main box, one per line |
| 2 | 10 kΩ resistors | optional, only if you get stray presses |
| 2 | M4 × 50 mm bolt + nyloc nut (or 4 mm rod) | treadle hinges (length to suit the CAD) |
| 2 | M3 × 10 mm set screws + M3 nuts + M3 heat-set inserts | adjustable actuators |
| 2 | Light compression springs, about 5–8 mm diameter | treadle return (pen springs) |
| 2–4 | Stick-on rubber bumpers | hard stops (or print them) |
| 4 | Rubber feet | |
| — | Hook-up wire, heat-shrink, M3 screws + inserts for the lid | |

## When you build it

- [ ] Check the breakout boards bring out D+/D− and join A6/B6 and A7/B7 (meter it).
- [ ] Wire the main box side first and test with a bare wire: touching D+ to GND on the
      socket should act like a Keyboard button press.
- [ ] Print a test treadle and base corner, then set the actuator and hard stop.
- [ ] Add it to the website build guide as an optional step.
