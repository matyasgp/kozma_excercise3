"""Required detection range per direction (Exercise 4, step 1).

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
"""
from math import atan, degrees, sqrt

KMH = 1 / 3.6
T_R = 1.0            # s, detection to action
A_COMFORT = 3.0      # m/s^2, comfortable braking
S_CROSS = 15.0       # m, distance to clear a two-lane road from a stop line (2 lanes + car length)
A_GO = 2.0           # m/s^2, moderate acceleration from standstill
T_LC = 3.0           # s, lane change duration
JOGGER = 3.0         # m/s, a running pedestrian
R_CURVE = {"car": 720.0, "pedestrian": 120.0}   # m, tightest curve at highway / urban arterial speed
OFFSET = {"car": 3.5, "pedestrian": 5.0}        # m, lateral offset: next lane / pedestrian at the kerb
NEAR = (0.1, 5.0)    # m, near field around the body
NEAR_H = 0.5         # m, smallest object the near field must see (kerb, bollard, crouching child)


def stop_distance(v_kmh, t_r=T_R, a=A_COMFORT):
    v = v_kmh * KMH
    return v * t_r + v * v / (2 * a)


def safe_speed(d, t_r=T_R, a=A_COMFORT):
    """Highest speed [km/h] whose stopping distance fits in d metres (inverse of stop_distance)."""
    return a * (-t_r + sqrt(t_r**2 + 2 * d / a)) / KMH


T_PULLOUT = T_R + sqrt(2 * S_CROSS / A_GO)           # 4.9 s to clear the crossing road
SCENARIOS = {
    # (direction, target): (scenario, required range m)
    ("front", "car"): ("stop for a car from 130 km/h (highway)", stop_distance(130)),
    ("front", "pedestrian"): ("stop for a pedestrian from 70 km/h (urban arterial)", stop_distance(70)),
    ("side", "car"): ("pull out (4.9 s) before cross traffic at 60 km/h arrives", 60 * KMH * T_PULLOUT),
    ("side", "pedestrian"): ("a jogger (3 m/s) reaches our path during the 4.9 s", JOGGER * T_PULLOUT),
    ("rear", "car"): ("lane change (3 s) with a car closing at 60 km/h, which then brakes at 3 m/s^2",
                      60 * KMH * T_LC + (60 * KMH) ** 2 / (2 * A_COMFORT)),
    ("rear", "pedestrian"): ("a jogger reaches us while we turn or reverse (4.9 s)", JOGGER * T_PULLOUT),
}
REQ = {k: v[1] for k, v in SCENARIOS.items()}


def cone(direction, target):
    """Half-angle [deg] of the sector where the front or rear requirement holds."""
    d = REQ[(direction, target)]
    return degrees(d / (2 * R_CURVE[target]) + atan(OFFSET[target] / d))


FRONT_CONE = {t: cone("front", t) for t in ("car", "pedestrian")}
REAR_CONE = {t: cone("rear", t) for t in ("car", "pedestrian")}


def required_range(bearing_deg, target):
    """Required detection range [m] at a bearing (0 = ahead, +-180 = behind; symmetric left/right)."""
    b = abs((bearing_deg + 180) % 360 - 180)
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
