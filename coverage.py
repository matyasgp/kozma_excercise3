"""Coverage map per condition (Exercise 4, step 4): in every direction, how many independent modalities
(camera, lidar, radar, thermal) still reach the required range.

For each bearing (1 deg steps, 0 = ahead, +90 = left) and three rings:
  car         a car at the required car range (requirements.py), measured from the body edge
  pedestrian  a pedestrian at the required pedestrian range
  near field  an object 0.5 m tall anywhere from 0.1 to 5 m from the body (geometry only: FOV, mount
              height, pitch, minimum range, the roof lidar's view blocked by the car body; at night the
              car's own lamps are assumed to light the first metres for the cameras)
a sensor counts when the target lies in its horizontal FOV and within its effective range from model.py
(at the target's angle off boresight; at night a camera sees a pedestrian only inside the low beam,
+-30 deg ahead). A modality counts when at least one of its sensors does. A
condition group takes the worst of its sub-cases bearing by bearing.
Status: >= 2 modalities = redundant, 1 = single point of failure, 0 = gap.

Run `python coverage.py`: prints the summary, writes coverage.csv and figures/coverage_conditions.{png,pdf}
and figures/coverage_detail_1.png and _2.png.
"""
import logging
import os

import matplotlib
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from model import FORWARD_YAW, GROUPS, LOW_BEAM_HALF, SUBCASES, effective_range, load_suite
from requirements import NEAR, NEAR_H, required_range

MODS = ("camera", "lidar", "radar", "thermal")
RINGS = ("car", "pedestrian", "near")
RING_NAME = {"car": "Car", "pedestrian": "Pedestrian", "near": "Near field"}
BEARINGS = np.arange(-180, 180)                     # deg
NEAR_STEPS = np.round(np.arange(NEAR[0], NEAR[1] + 1e-9, 0.1), 2)

INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
STATUS = {2: ("#0ca30c", "2 or more modalities"), 1: ("#fab219", "1 modality (no redundancy)"),
          0: ("#d03b3b", "0 (gap)")}
MOD_COLOR = {"camera": "#2a78d6", "lidar": "#008300", "radar": "#eda100", "thermal": "#e87ba4"}
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10,
                     "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE})


def wrap(a):
    return (a + 180) % 360 - 180


def load():
    models, mounts = load_suite()
    with open("sensors.yaml", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    pitch, veh = d.get("pitch", {}), d["vehicle"]
    sensors = []
    for mid, model, x, y, z, yaw in mounts:
        m = models[model]
        if m["modality"] not in MODS:
            continue
        down = m.get("vfov_down", m["vfov"] / 2)
        if m["modality"] == "radar":
            rmin = min(m["modes"][k][3] for k in m.get("operating_modes", ["extra_long"]))
        else:
            rmin = m.get("range_min", 0.0)
        sensors.append(dict(id=mid, m=m, mod=m["modality"], x=x, y=y, z=z, yaw=yaw, forward=abs(yaw) <= FORWARD_YAW,
                            lo=pitch.get(mid, 0) - down, hi=pitch.get(mid, 0) - down + m["vfov"], rmin=rmin))
    return sensors, veh


def body_edge(theta, veh):
    """Distance from the car's centre to its body edge along a bearing [m] (rectangle footprint)."""
    c, s = abs(np.cos(np.radians(theta))), abs(np.sin(np.radians(theta)))
    return min(veh["length"] / 2 / c if c > 1e-9 else np.inf, veh["width"] / 2 / s if s > 1e-9 else np.inf)


def seen_long(sen, px, py, target, sub):
    """Is a target at (px, py) inside the sensor's horizontal FOV and its effective range?"""
    dx, dy = px - sen["x"], py - sen["y"]
    phi = wrap(np.degrees(np.arctan2(dy, dx)) - sen["yaw"])
    if abs(phi) > sen["m"]["hfov"] / 2:
        return False
    if (sen["mod"] == "camera" and target == "pedestrian" and SUBCASES[sub]["night"]
            and abs(np.degrees(np.arctan2(py, px))) > LOW_BEAM_HALF):
        return False                                   # unlit road: only the low beam lights pedestrians
    return np.hypot(dx, dy) <= effective_range(sen["m"], target, sub, sen["forward"], phi)


def blocked_by_body(sen, p, veh):
    """Does the straight line from a sensor above the roof to point p pass through the car body (a box)?"""
    if sen["z"] <= veh["height"]:
        return False
    s0 = np.array([sen["x"], sen["y"], sen["z"]])
    d = np.asarray(p) - s0
    lo = np.array([-veh["length"] / 2, -veh["width"] / 2, 0.0])
    hi = np.array([veh["length"] / 2, veh["width"] / 2, veh["height"]])
    t0, t1 = 0.0, 1.0
    for k in range(3):
        if abs(d[k]) < 1e-12:
            if not lo[k] <= s0[k] <= hi[k]:
                return False
            continue
        a, b = sorted(((lo[k] - s0[k]) / d[k], (hi[k] - s0[k]) / d[k]))
        t0, t1 = max(t0, a), min(t1, b)
        if t0 > t1:
            return False
    return True


def seen_near(sen, px, py, veh):
    """Does the sensor see any part of a NEAR_H tall object standing at (px, py)?"""
    dx, dy = px - sen["x"], py - sen["y"]
    phi = wrap(np.degrees(np.arctan2(dy, dx)) - sen["yaw"])
    if abs(phi) > sen["m"]["hfov"] / 2:
        return False
    dh = np.hypot(dx, dy)
    el_bot, el_top = np.degrees(np.arctan2(0 - sen["z"], dh)), np.degrees(np.arctan2(NEAR_H - sen["z"], dh))
    lo, hi = max(el_bot, sen["lo"]), min(el_top, sen["hi"])
    if lo > hi:
        return False
    el = np.radians((lo + hi) / 2)                     # a visible point on the object
    pz = sen["z"] + dh * np.tan(el)
    if np.hypot(dh, pz - sen["z"]) < sen["rmin"]:
        return False
    return not blocked_by_body(sen, (px, py, pz), veh)


def near_field(sensors, veh):
    """{modality: bool[bearing]}: the modality sees the object at every distance in the near field."""
    out = {mod: np.zeros(len(BEARINGS), bool) for mod in MODS}
    for i, th in enumerate(BEARINGS):
        c, s, e = np.cos(np.radians(th)), np.sin(np.radians(th)), body_edge(th, veh)
        for mod in MODS:
            ss = [x for x in sensors if x["mod"] == mod]
            out[mod][i] = all(any(seen_near(x, (e + d) * c, (e + d) * s, veh) for x in ss) for d in NEAR_STEPS)
    return out


def long_range(sensors, veh, target, sub):
    """{modality: bool[bearing]} for a target at the required range in one sub-case."""
    out = {mod: np.zeros(len(BEARINGS), bool) for mod in MODS}
    for i, th in enumerate(BEARINGS):
        r = body_edge(th, veh) + required_range(th, target)
        px, py = r * np.cos(np.radians(th)), r * np.sin(np.radians(th))
        for x in sensors:
            if not out[x["mod"]][i] and seen_long(x, px, py, target, sub):
                out[x["mod"]][i] = True
    return out


def coverage(sensors, veh):
    """{group: {ring: {"count": int[bearing], "mods": {modality: bool[bearing]}}}}, worst sub-case per bearing."""
    near = near_field(sensors, veh)
    res = {}
    for g, subs in GROUPS.items():
        res[g] = {}
        for ring in ("car", "pedestrian"):
            per = [long_range(sensors, veh, ring, s) for s in subs]
            counts = np.min([sum(p[m].astype(int) for m in MODS) for p in per], axis=0)
            mods = {m: np.all([p[m] for p in per], axis=0) for m in MODS}
            res[g][ring] = dict(count=counts, mods=mods)
        res[g]["near"] = dict(count=sum(near[m].astype(int) for m in MODS), mods=near)
    return res


def runs(mask):
    """Contiguous bearing runs where mask is True (wrapping at +-180), as (start, end) in deg."""
    if mask.all():
        return [(-180, 179)]
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return []
    out, start = [], idx[0]
    for a, b in zip(idx, np.append(idx[1:], -1)):
        if b != a + 1:
            out.append([BEARINGS[start], BEARINGS[a]])
            start = b
    if len(out) > 1 and out[0][0] == -180 and out[-1][1] == 179:
        out[0][0] = out.pop()[0]
    return [tuple(r) for r in out]


def where(a, b):
    """Plain-words name of a bearing span."""
    mid = wrap((a + (b - a) % 360 / 2))
    w = (b - a) % 360 + 1
    side = "ahead" if abs(mid) <= 30 else "behind" if abs(mid) >= 150 else ("left" if mid > 0 else "right")
    if side in ("left", "right") and abs(mid) < 70:
        side = "front-" + side
    if side in ("left", "right") and abs(mid) > 110:
        side = "rear-" + side
    if side in ("ahead", "behind"):
        return f"{side} (±{(w - 1) // 2}°)"
    return f"{side} ({w}°)"


def summary(res):
    lines = []
    for g, rings in res.items():
        for ring in RINGS:
            c = rings[ring]["count"]
            worst = int(c.min())
            spans = [where(a, b) for a, b in runs(c == worst)] if worst < 2 else []
            lines.append((g, ring, worst, int((c >= 2).sum()), ", ".join(spans)))
    return lines


def status(c):
    return np.minimum(c, 2)


RADII = {"car": (0.78, 1.0), "pedestrian": (0.53, 0.75), "near": (0.28, 0.50)}


def text_on(status_value):
    """Label color inside a status fill: near-black on amber, white otherwise."""
    return INK if status_value == 1 else "#ffffff"


def draw_donut(ax, rings, first=False):
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(1)
    ax.set_ylim(0, 1.0)
    ax.axis("off")
    for ring, (r0, r1) in RADII.items():
        st = status(rings[ring]["count"])
        for k in (0, 1, 2):                              # one wedge per contiguous run: no hairline seams
            for a, b in runs(st == k):
                n = (b - a) % 360 + 1
                ax.bar(np.radians(a - 0.5 + n / 2), r1 - r0, width=np.radians(n), bottom=r0,
                       color=STATUS[k][0], edgecolor="none", align="center")
    L, W = 0.15, 0.06                                    # the car, front up
    xs = np.r_[np.linspace(L, -L, 40), np.full(20, -L), np.linspace(-L, L, 40), np.full(20, L)]
    ys = np.r_[np.full(40, W), np.linspace(W, -W, 20), np.full(40, -W), np.linspace(-W, W, 20)]
    ax.fill(np.arctan2(ys, xs), np.hypot(xs, ys), color=INK2, lw=0)
    ax.fill([np.radians(-25), 0, np.radians(25)], [0.13, 0.21, 0.13], color=INK2, lw=0)
    if first:                                            # ring names behind the car, required range ahead
        for ring, (r0, r1) in RADII.items():
            st = status(rings[ring]["count"])
            r = (r0 + r1) / 2
            back = {"car": "car  96 m", "pedestrian": "pedestrian  15 m", "near": "near field"}[ring]
            ax.text(np.pi, r, back, ha="center", va="center", fontsize=6.8, color=text_on(st[0]))
            if ring != "near":
                front = {"car": "253 m", "pedestrian": "82 m"}[ring]
                ax.text(0, r, front, ha="center", va="center", fontsize=6.8, color=text_on(st[180]))


def describe(rings):
    """Where each ring is weakest and which modality is left there, one line per ring."""
    parts = []
    for ring in RINGS:
        c = rings[ring]["count"]
        worst = int(c.min())
        if worst >= 2:
            continue
        mask = c == worst
        left = [m for m in MODS if rings[ring]["mods"][m][mask].all()]
        who = "no modality" if worst == 0 else f"{' + '.join(left) or 'one modality'} only"
        n = int(mask.sum())
        if n > 180:
            parts.append(f"{RING_NAME[ring].lower()}: {who} on {n}° of 360°")
        else:
            spans = runs(mask)
            big = max(spans, key=lambda ab: (ab[1] - ab[0]) % 360)
            parts.append(f"{RING_NAME[ring].lower()} {where(*big)}: {who}")
    return "; ".join(parts) if parts else "2+ modalities everywhere"


def figure(res):
    W, H, size, y0 = 10.0, 3.9, 1.9, 1.05          # sized for a 10 in wide slide (Google Slides default)
    fig = plt.figure(figsize=(W, H))
    for i, (g, rings) in enumerate(res.items()):
        xc = 0.1 + (i + 0.5) * (W - 0.2) / 4
        ax = fig.add_axes([(xc - size / 2) / W, y0 / H, size / W, size / H], projection="polar")
        draw_donut(ax, rings, first=(i == 0))
        top = (y0 + size) / H
        fig.text(xc / W, top + 0.3 / H, g, ha="center", color=INK, fontsize=12.5, fontweight="semibold")
        fig.text(xc / W, top + 0.07 / H, "ahead", ha="center", color=MUTED, fontsize=7.5)
        lines = describe(rings).split("; ")
        fig.text(xc / W, (y0 - 0.08) / H, "\n".join(lines), ha="center", va="top", color=INK, fontsize=8.3,
                 linespacing=1.25)
    handles = [Patch(color=c, label=l) for c, l in STATUS.values()]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=9, labelcolor=INK2,
               bbox_to_anchor=(0.5, 0.04))
    fig.text(0.5, 0.012, "Rings (not to scale): car 253 m ahead, 81 m sides, 96 m behind; pedestrian 82 m ahead, "
             "15 m around; near field 0.1-5 m, 0.5 m objects.", ha="center", color=MUTED, fontsize=7.3)
    os.makedirs("figures", exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"figures/coverage_conditions.{ext}", dpi=250)
    plt.close(fig)


def detail_figure(res, groups, path):
    """Backup: which modality covers which bearing, for some condition groups (one panel each)."""
    fig, axs = plt.subplots(len(groups), 1, figsize=(10, 2.75 * len(groups) + 0.4), sharex=True, squeeze=False)
    for ax, g in zip(axs[:, 0], groups):
        rings = res[g]
        rows = [(ring, mod) for ring in RINGS for mod in MODS]
        for k, (ring, mod) in enumerate(rows):
            for a, b in runs(rings[ring]["mods"][mod]):
                spans = [(a, b)] if b >= a else [(a, 179), (-180, b)]
                for s0, s1 in spans:
                    ax.barh(k, s1 - s0 + 1, left=s0 - 0.5, height=0.72, color=MOD_COLOR[mod], lw=0)
        for k in (3.5, 7.5):
            ax.axhline(k, color=GRID, lw=0.8)
        ax.set_yticks(range(len(rows)), [f"{RING_NAME[r]} · {m}" for r, m in rows], fontsize=8.5, color=INK2)
        ax.invert_yaxis()
        ax.set_title(g, loc="left", color=INK, fontsize=11, fontweight="semibold")
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", colors=MUTED, labelsize=8.5)
    ax = axs[-1, 0]
    ax.set_xticks([-180, -135, -90, -45, 0, 45, 90, 135, 180],
                  ["behind", "rear-right", "right", "front-right", "ahead", "front-left", "left", "rear-left", "behind"])
    ax.set_xlim(-180, 180)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def main():
    sensors, veh = load()
    res = coverage(sensors, veh)
    with open("coverage.csv", "w", encoding="utf-8") as f:
        f.write("condition,ring,bearing_deg,count," + ",".join(MODS) + "\n")
        for g, rings in res.items():
            for ring in RINGS:
                for i, th in enumerate(BEARINGS):
                    mods = rings[ring]["mods"]
                    f.write(f"{g},{ring},{th},{rings[ring]['count'][i]}," +
                            ",".join(str(int(mods[m][i])) for m in MODS) + "\n")
    print(f"{'condition':24s}{'ring':12s}{'min':>4s}{'deg with 2+':>13s}   worst sectors")
    for g, ring, worst, n2, spans in summary(res):
        print(f"{g:24s}{ring:12s}{worst:4d}{n2:13d}   {spans}")
    figure(res)
    names = list(res)
    detail_figure(res, names[:2], "figures/coverage_detail_1.png")
    detail_figure(res, names[2:], "figures/coverage_detail_2.png")
    print("wrote coverage.csv, figures/coverage_conditions.png/.pdf, figures/coverage_detail_1.png and _2.png")
    return res


if __name__ == "__main__":
    main()
