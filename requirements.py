"""Required detection range per direction (Exercise 4, step 1).

Question this file answers: how far must the car see, in each direction, to drive safely?
Each number comes from one driving scenario and one formula (v in m/s):
  front  stop for an object in the lane:            d = v t_r + v^2 / (2 a)
  side   pull out across a two-lane road:           d = v_cross (t_r + sqrt(2 s / a_go))
  rear   change lanes with a faster car behind:     d = dv t_lc + dv^2 / (2 a)
  near   parking, kerbs, a child beside the car:    0.1 .. 5 m around the body

t_r = 1 s (perception + planning + actuation) and a = 3 m/s^2 (comfortable braking): an automated car
should plan to stop without emergency braking. With the Exercise 3 emergency values (0.5 s, 6 m/s^2) the
130 km/h stopping distance would be only 127 m.

Where each requirement holds follows from road geometry. A lane that curves with radius Rc is d / (2 Rc) rad
off-axis at distance d, and a lane offset o adds atan(o / d). So the front requirement holds in a cone of
d / (2 Rc) + atan(o / d) around ahead, the rear one in the same kind of cone around behind, and the side
requirement everywhere else (cross traffic can come from any other bearing).
Run `python requirements.py` to print the table.

Results (rounded): front car 253 m (+-11 deg), front pedestrian 82 m (+-23 deg), side car 81 m,
rear car 96 m (+-6 deg), pedestrian at the sides and behind 15 m, near field 0.1-5 m.
"""
from math import atan, degrees, sqrt

# ---------------- scenario parameters (our choices, listed in the README) ----------------
KMH = 1 / 3.6        # multiply km/h by this to get m/s
T_R = 1.0            # s, detection to action: the car keeps driving at full speed for this long
A_COMFORT = 3.0      # m/s^2, comfortable braking (an emergency stop would be ~6 m/s^2)
S_CROSS = 15.0       # m, distance to clear a two-lane road from a stop line (2 lanes + car length)
A_GO = 2.0           # m/s^2, moderate acceleration from standstill
T_LC = 3.0           # s, lane change duration
JOGGER = 3.0         # m/s, a running pedestrian
R_CURVE = {"car": 720.0, "pedestrian": 120.0}   # m, tightest curve at highway / urban arterial speed
OFFSET = {"car": 3.5, "pedestrian": 5.0}        # m, lateral offset: next lane / pedestrian at the kerb
NEAR = (0.1, 5.0)    # m, near field around the body
NEAR_H = 0.5         # m, smallest object the near field must see (kerb, bollard, crouching child)


def stop_distance(v_kmh, t_r=T_R, a=A_COMFORT):
    """Stopping distance [m] from v_kmh: distance driven during the reaction time + braking distance."""
    v = v_kmh * KMH
    return v * t_r + v * v / (2 * a)            # 130 km/h: 36 m + 217 m = 253 m


def safe_speed(d, t_r=T_R, a=A_COMFORT):
    """Highest speed [km/h] whose stopping distance fits in d metres (inverse of stop_distance).
    Solves v t_r + v^2/(2a) = d for v: the positive root of the quadratic."""
    return a * (-t_r + sqrt(t_r**2 + 2 * d / a)) / KMH


# Pulling out from a stop line: 1 s to react, then accelerate over 15 m (s = a t^2 / 2  ->  t = sqrt(2 s / a)).
T_PULLOUT = T_R + sqrt(2 * S_CROSS / A_GO)           # 1 s + 3.9 s = 4.9 s to clear the crossing road
SCENARIOS = {
    # (direction, target): (scenario, required range m)
    # front: stopping distance from the highest speed where such an object can be in our lane
    ("front", "car"): ("stop for a car from 130 km/h (highway)", stop_distance(130)),                 # 253 m
    ("front", "pedestrian"): ("stop for a pedestrian from 70 km/h (urban arterial)", stop_distance(70)),  # 82 m
    # side: cross traffic must not reach us while we cross its road (it drives 60 km/h for 4.9 s)
    ("side", "car"): ("pull out (4.9 s) before cross traffic at 60 km/h arrives", 60 * KMH * T_PULLOUT),  # 81 m
    ("side", "pedestrian"): ("a jogger (3 m/s) reaches our path during the 4.9 s", JOGGER * T_PULLOUT),  # 15 m
    # rear: during a 3 s lane change a car 60 km/h faster closes in (50 m), then it must brake down to
    # our speed at 3 m/s^2 (46 m): we must see it 96 m back before we start the lane change
    ("rear", "car"): ("lane change (3 s) with a car closing at 60 km/h, which then brakes at 3 m/s^2",
                      60 * KMH * T_LC + (60 * KMH) ** 2 / (2 * A_COMFORT)),                            # 96 m
    ("rear", "pedestrian"): ("a jogger reaches us while we turn or reverse (4.9 s)", JOGGER * T_PULLOUT),  # 15 m
}
REQ = {k: v[1] for k, v in SCENARIOS.items()}       # {(direction, target): required range m}


def cone(direction, target):
    """Half-angle [deg] of the sector where the front or rear requirement holds.
    An object d metres down a lane that curves with radius Rc appears d/(2 Rc) rad off our axis (small-angle
    circle geometry); being in the next lane (offset o) adds atan(o/d). Outside this cone an object at that
    distance cannot be in a lane we drive into, so the (shorter) side requirement applies there."""
    d = REQ[(direction, target)]
    return degrees(d / (2 * R_CURVE[target]) + atan(OFFSET[target] / d))


FRONT_CONE = {t: cone("front", t) for t in ("car", "pedestrian")}   # car +-11 deg, pedestrian +-23 deg
REAR_CONE = {t: cone("rear", t) for t in ("car", "pedestrian")}     # car +-6 deg, pedestrian +-22 deg


def required_range(bearing_deg, target):
    """Required detection range [m] at a bearing (0 = ahead, +-180 = behind; symmetric left/right).
    This is the function the coverage map evaluates on every 1 deg bearing."""
    b = abs((bearing_deg + 180) % 360 - 180)        # fold any angle into 0..180 deg off ahead
    if b <= FRONT_CONE[target]:
        return REQ[("front", target)]
    if b >= 180 - REAR_CONE[target]:
        return REQ[("rear", target)]
    return REQ[("side", target)]


if __name__ == "__main__":
    print(f"{'direction':10s}{'target':12s}{'required':>10s}   scenario")
    for (d, t), (s, r) in SCENARIOS.items():
        print(f"{d:10s}{t:12s}{r:8.0f} m   {s}")
    for t in ("car", "pedestrian"):
        print(f"{t}: front cone +-{FRONT_CONE[t]:.1f} deg, rear cone +-{REAR_CONE[t]:.1f} deg "
              f"(curve radius {R_CURVE[t]:.0f} m, lateral offset {OFFSET[t]} m)")
    print(f"near field: {NEAR[0]}-{NEAR[1]} m around the body, objects >= {NEAR_H} m tall")
    print(f"emergency stop from 130 km/h (0.5 s, 6 m/s^2, Exercise 3): {stop_distance(130, 0.5, 6):.0f} m")
