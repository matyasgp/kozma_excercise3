"""Physics model behind the spider charts and the coverage maps (Exercise 4).

For every sensor in sensors.yaml and every condition it computes
  - the effective detection range for a pedestrian and for a car, and
  - the six spider-chart scores of the professor's template (0..1),
from datasheet numbers plus one small physics law per effect. One function per effect:

  atmosphere   extinction alpha per band [1/m]: Koschmieder alpha = 3.912/V for fog/snow (Kim et al. 2001:
               no wavelength dependence below V = 500 m, so the same for 550/905/1550 nm), rain
               alpha = 0.365 R^0.63 [1/km] (R in mm/h, Carbonneau 1998), LWIR in fog/snow = a ratio x visible
               (the `lwir` column of SUBCASES; fog: LWIR_FOG_RATIO).
               Radar: rain attenuation gamma = k R^a dB/km (ITU-R P.838-3, ~77 GHz), fog/snow small.
  lidar        per-beam return probability p = 1 - exp(-c rho/R^2 exp(-2 alpha R)), c calibrated to the
               datasheet range at 10 %; the object is detected when P(>= 5 returns) >= 99 %
               (the Exercise 3 model, here for every lidar and condition). Outside the InnovizTwo ROI the
               datasheet's side-FOV numbers apply (140 m at 10 %, 0.2 deg horizontal). The Hesai OT128 is
               modelled channel by channel from its user manual (Appendix A.1, hesai_ot128_channels.csv):
               the channels that hit the target from the mounting height, each with its own 10 % range
               (detection probability 70 %) and horizontal resolution, sum their returns.
  radar        radar equation with attenuation: R^4 10^(2 gamma R/10) = R0^4 sigma/sigma_car,
               R0 = datasheet range on a passenger car, reduced off boresight by the antenna pattern.
  camera       range = min(geometry, contrast, light):
               geometry  - the object must be >= N_PX pixels high (KITTI's minimum box height, 25 px);
               contrast  - C(R) = C0 exp(-alpha R) / (1 + G) must stay >= EPS (Koschmieder; G = veiling glare);
               light     - at night a pedestrian is lit only by the low beam: E = I/R^2 >= E_MIN
                           (a car carries its own lights, so it is not light-limited).
               Tunnel exit: scene dynamic range above the camera's HDR costs 10^(-excess/20) of contrast.
  thermal      range = min(geometry (same N_PX rule), radiometry dT exp(-alpha R) >= SNR_REQ * NETD).

Assumptions that are ours (not from a datasheet) are in CAPITALS below and listed in the README.
Run `python model.py` to print the tables and write ranges.csv and spider_scores.csv.
"""
from math import comb, log10

import numpy as np
import yaml

from requirements import REQ

# --- targets: (width, height) [m], lidar reflectivity, radar cross-section [m^2], camera contrast, thermal dT [K] ---
TARGETS = {
    "pedestrian": dict(w=0.5, h=1.8, rho=0.10, rcs=0.3, c0=0.3),
    "car":        dict(w=1.8, h=1.5, rho=0.10, rcs=10.0, c0=0.4),
}
RCS_CAR = 10.0          # radar datasheet ranges are "on passenger car"; ~10 dBsm
K_MIN, CONF = 5, 0.99   # lidar: >= 5 returns with 99 % probability (Exercise 3 / EBA)
P0_DEFAULT = 0.90       # lidar detection probability behind the datasheet range (InnovizTwo states 90 %)
RHO_SPEC = 0.10         # lidar datasheet ranges are quoted for a 10 % reflective target
N_PX = 25               # camera/thermal: minimum object height in pixels (KITTI "moderate" minimum)
EPS = 0.05              # camera: minimum usable contrast
I_LOW_BEAM = 4000.0     # cd, low beam towards a pedestrian ahead
LOW_BEAM_HALF = 30.0    # deg, horizontal half-spread of the low beam (pedestrians outside it are unlit at night)
E_MIN = 1.0             # lux needed on a pedestrian for a usable image
E_GOOD = 10.0           # lux for full image quality (contrast/resolution axis at night)
SNR_REQ = 5.0           # thermal: dT must exceed 5 x NETD
LWIR_FOG_RATIO = 0.4    # LWIR / visible extinction in fog (small droplets; literature ~0.2-1)
RADAR_RAIN = (1.02, 0.73)  # ITU-R P.838-3 k, a near 77 GHz (horizontal), gamma = k R^a [dB/km]
RADAR_HALF_3DB = 40.0   # deg, one-way 3 dB half-width (datasheet: the 3 dB FOV is narrower than the +-50 deg total)
FORWARD_YAW = 60        # glare and tunnel exit hit sensors looking within +-60 deg of ahead
T_SPEED = 0.1           # speed axis: the speed must be known within 100 ms
BOX_JITTER_PX = 1.0     # camera/thermal: noise of the detected box height [px]

# --- conditions (sub-cases); the spider groups take the worst sub-case per sensor ---
SUBCASES = {
    # V: visibility m, rain: mm/h, G: veiling glare, scene_db: scene dynamic range dB, clutter: lidar snow clutter,
    # radar_db: extra radar attenuation dB/km, dT: thermal contrast ped/car K,
    # lwir: LWIR / visible extinction when V < 5 km (fog: small droplets; snow: large flakes block both alike)
    "clear_day":     dict(V=23000, rain=0,  night=False, G=0, scene_db=0,   clutter=1.0, radar_db=0.0, dT=(5, 5),   lwir=1.0),
    "night":         dict(V=23000, rain=0,  night=True,  G=0, scene_db=0,   clutter=1.0, radar_db=0.0, dT=(10, 8),  lwir=1.0),
    "fog":           dict(V=200,   rain=0,  night=False, G=0, scene_db=0,   clutter=1.0, radar_db=0.1, dT=(3, 3),
                          lwir=LWIR_FOG_RATIO),
    "heavy_rain":    dict(V=23000, rain=25, night=False, G=0, scene_db=0,   clutter=1.0, radar_db=0.0, dT=(3, 3),   lwir=1.0),
    "snow":          dict(V=1000,  rain=0,  night=False, G=0, scene_db=0,   clutter=0.5, radar_db=1.0, dT=(15, 10), lwir=1.0),
    "low_sun_glare": dict(V=23000, rain=0,  night=False, G=3, scene_db=0,   clutter=1.0, radar_db=0.0, dT=(5, 5),   lwir=1.0),
    "tunnel_exit":   dict(V=23000, rain=0,  night=False, G=0, scene_db=125, clutter=1.0, radar_db=0.0, dT=(5, 5),   lwir=1.0),
}
GROUPS = {
    "Clear day": ["clear_day"],
    "Night": ["night"],
    "Fog / heavy rain": ["fog", "heavy_rain"],
    "Snow / glare / tunnel": ["snow", "low_sun_glare", "tunnel_exit"],
}
AXES = ["Contrast, resolution", "Range", "Color", "Speed detection", "3D reconstruction", "Living objects"]
RANGE_REQ = REQ[("front", "car")]   # range axis: car range relative to the 253 m front requirement


# ---------------- atmosphere ----------------
def alpha(band, sc):
    """Extinction coefficient [1/m] for 'vis' (camera), 'nir' (lidar) or 'lwir' (thermal)."""
    a = 3.912 / sc["V"]                                            # Koschmieder
    if band == "lwir":
        a = a * sc["lwir"] if sc["V"] < 5000 else 1.5e-4           # clear humid air: water-vapour absorption
    return a + 0.365 * sc["rain"] ** 0.63 / 1000


def radar_gamma(sc):
    """Two-way-ready one-way attenuation at 77 GHz [dB/m]."""
    k, a = RADAR_RAIN
    return (k * sc["rain"] ** a if sc["rain"] else 0.0) / 1000 + sc["radar_db"] / 1000


# ---------------- lidar (Exercise 3 model) ----------------
def return_probability(p0, range_10pct, rho, R, a, clutter):
    """Probability that one beam returns from a target of reflectivity rho at R [m] through extinction a [1/m].
    c is calibrated so that p = p0 for a 10 % target at the datasheet range; snow clutter scales it down."""
    c = -np.log(1 - p0) * range_10pct**2 / RHO_SPEC * clutter
    return 1 - np.exp(-c * rho / R**2 * np.exp(-2 * a * R))


def lidar_p_beam(m, R, sc, rho=RHO_SPEC):
    return return_probability(m.get("p0", P0_DEFAULT), m["range_10pct"], rho, R, alpha("nir", sc), sc["clutter"])


def p_at_least(k, n, p):
    n = int(n)
    return 1 - sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(min(k, n + 1)))


def beam_counts(size, R, dth):
    """Beams across one side of the object: floor(L) or floor(L)+1, depending on the random grid offset."""
    L = size / (R * dth)
    lo = np.floor(L)
    return (lo, lo + 1), (1 - (L - lo), L - lo)


def lidar_p_detect(m, t, R, sc):
    """P(>= K_MIN returns), averaged over the 2 x 2 possible beam counts (Exercise 3, step 3)."""
    (nh, ph), (nv, pv) = beam_counts(t["w"], R, np.radians(m["res_h"])), beam_counts(t["h"], R, np.radians(m["res_v"]))
    p = lidar_p_beam(m, R, sc, t["rho"])
    return sum(ph[i] * pv[j] * p_at_least(K_MIN, nh[i] * nv[j], p) for i in range(2) for j in range(2))


def binom_pmf(n, p):
    n = int(n)
    return np.array([comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(n + 1)])


def channels_on_target(m, t, R):
    """Channels of a per-channel lidar whose elevation hits a target standing on flat ground R m away,
    and that are inside their instrumented range."""
    ch, z = m["ch"], m["mount_z"]
    lo, hi = np.degrees(np.arctan2(-z, R)), np.degrees(np.arctan2(t["h"] - z, R))
    return (ch["elevation_deg"] >= lo) & (ch["elevation_deg"] <= hi) & (R >= ch["range_min_m"]) & (R <= ch["range_max_m"])


def lidar_channels_p_detect(m, t, R, sc):
    """P(>= K_MIN returns) for a lidar with a per-channel table (Hesai OT128, manual Appendix A.1): each channel
    that hits the target has its own 10 % range and horizontal resolution; the number of returns is the sum of
    the channels' binomials (the horizontal grid offset of each channel averaged as in beam_counts)."""
    ch, a, hit = m["ch"], alpha("nir", sc), channels_on_target(m, t, R)
    dist = np.array([1.0])                               # distribution of the number of returns so far
    for r10, resh in zip(ch["range_10pct_m"][hit], ch["res_h_deg"][hit]):
        p = return_probability(m["p0"], r10, t["rho"], R, a, sc["clutter"])
        (n0, n1), (w0, w1) = beam_counts(t["w"], R, np.radians(resh))
        pmf = np.zeros(int(n1) + 1)
        pmf[: int(n0) + 1] += w0 * binom_pmf(n0, p)
        pmf += w1 * binom_pmf(n1, p)
        dist = np.convolve(dist, pmf)
    return float(1 - dist[:K_MIN].sum())


def lidar_at(m, phi):
    """The lidar's parameters at phi deg off boresight (InnovizTwo: side FOV outside the central ROI)."""
    if "side_fov" in m and abs(phi) > m["roi_hfov"] / 2:
        return {**m, **m["side_fov"]}
    return m


_LIDAR_CACHE = {}


def lidar_range(m, t, sc):
    """Largest R with P(>= 5 returns) >= 99 %, capped at the datasheet maximum range."""
    key = (m["name"], m["res_h"], m["range_10pct"], m.get("mount_z"), t["w"], t["h"], tuple(sorted(sc.items())))
    if key not in _LIDAR_CACHE:
        R = np.arange(1, int(m.get("range_max", m["range_10pct"])) + 1)
        p_detect = lidar_channels_p_detect if "ch" in m else lidar_p_detect
        ok = [r for r in R if p_detect(m, t, r, sc) >= CONF]
        _LIDAR_CACHE[key] = int(max(ok)) if ok else 0
    return _LIDAR_CACHE[key]


# ---------------- radar ----------------
def radar_pattern(phi):
    """Range factor phi deg off boresight: one-way gain -3 (phi/phi_3dB)^2 dB, two ways, R ~ gain^(1/4)."""
    return 10 ** (-2 * 3 * (phi / RADAR_HALF_3DB) ** 2 / 40)


def radar_range(m, t, sc, mode="extra_long", phi=0.0):
    R0 = m["modes"][mode][0] * radar_pattern(phi) * (t["rcs"] / RCS_CAR) ** 0.25
    g = radar_gamma(sc)
    R = np.arange(0.5, R0 + 0.5, 0.5)
    ok = R**4 * 10 ** (2 * g * R / 10) <= R0**4
    return float(R[ok].max()) if ok.any() else 0.0


# ---------------- camera ----------------
def ifov(m):
    """Angular size of one pixel [rad] (vertical, from VFOV / rows)."""
    return np.radians(m["vfov"]) / m["resolution"][1]


def camera_contrast0(m, t, sc, forward):
    """Contrast at zero range after glare and HDR clipping."""
    c = t["c0"]
    if forward:
        c /= 1 + sc["G"]
        c *= 10 ** (-max(0, sc["scene_db"] - m["hdr_db"]) / 20)
    return c


def camera_range(m, t, sc, forward=True, name="pedestrian"):
    r_geo = t["h"] / (N_PX * ifov(m))
    c0 = camera_contrast0(m, t, sc, forward)
    r_con = np.log(c0 / EPS) / alpha("vis", sc) if c0 > EPS else 0.0
    r_light = np.inf
    if sc["night"] and name == "pedestrian":
        r_light = np.sqrt(I_LOW_BEAM / E_MIN) if forward else 0.0   # unlit road: only the low beam ahead
    return float(min(r_geo, r_con, r_light))


# ---------------- thermal ----------------
def thermal_range(m, t, sc, name="pedestrian"):
    r_geo = t["h"] / (N_PX * m["ifov_mrad"] / 1000)
    dT = sc["dT"][0 if name == "pedestrian" else 1]
    tau_min = SNR_REQ * m["netd_mk"] / 1000 / dT
    r_rad = -np.log(tau_min) / alpha("lwir", sc) if tau_min < 1 else 0.0
    return float(min(r_geo, r_rad))


def effective_range(m, target, sub, forward=True, phi=0.0):
    """Detection range [m] of one sensor model for 'pedestrian' or 'car' in one sub-case,
    phi deg off the sensor's boresight (only lidar ROI and radar antenna pattern depend on it).
    `sub` is a SUBCASES name or a condition dict of the same form."""
    t, sc, mod = TARGETS[target], SUBCASES[sub] if isinstance(sub, str) else sub, m["modality"]
    if mod == "lidar":
        return lidar_range(lidar_at(m, phi), t, sc)
    if mod == "radar":
        return max(radar_range(m, t, sc, mode, phi) for mode in m.get("operating_modes", ["extra_long"]))
    if mod == "camera":
        return camera_range(m, t, sc, forward, target)
    if mod == "thermal":
        return thermal_range(m, t, sc, target)
    return 0.0


# ---------------- spider scores ----------------
def log_score(x, worst, best):
    """0 at `worst`, 1 at `best`, logarithmic in between (works for both directions)."""
    return float(np.clip(log10(x / worst) / log10(best / worst), 0, 1))


def pixel_angle(m):
    """Vertical angle of one image pixel [rad] (camera or thermal)."""
    return ifov(m) if m["modality"] == "camera" else m["ifov_mrad"] / 1000


def samples_on_pedestrian(m, R=50.0):
    """Pixels / points / radar cells on a pedestrian at R (before weather)."""
    t = TARGETS["pedestrian"]
    if m["modality"] == "lidar" and "ch" in m:
        return float(sum(t["w"] / (R * np.radians(r)) for r in m["ch"]["res_h_deg"][channels_on_target(m, t, R)]))
    if m["modality"] == "lidar":
        return t["w"] / (R * np.radians(m["res_h"])) * t["h"] / (R * np.radians(m["res_v"]))
    if m["modality"] == "radar":
        return 1.0                                      # ~2 deg azimuth separation: one cell
    if m["modality"] == "camera":
        a = np.radians(m["hfov"]) / m["resolution"][0]
        return t["w"] / (R * a) * t["h"] / (R * ifov(m))
    a = pixel_angle(m)
    return t["w"] / (R * a) * t["h"] / (R * a)


def availability(m, sub, R=50.0):
    """How much of the clear-weather signal is left at R in this sub-case (0..1)."""
    sc, mod, t = SUBCASES[sub], m["modality"], TARGETS["pedestrian"]
    if mod == "lidar":
        return float(lidar_p_beam(m, R, sc) / lidar_p_beam(m, R, SUBCASES["clear_day"]))
    if mod == "radar":
        return float(10 ** (-2 * radar_gamma(sc) * R / 10))
    if mod == "camera":
        c = camera_contrast0(m, t, sc, True) * np.exp(-alpha("vis", sc) * R) / t["c0"]
        if sc["night"]:
            c *= min(1.0, I_LOW_BEAM / R**2 / E_GOOD)
        return float(min(1.0, c))
    dT = sc["dT"][0]
    return float(min(1.0, dT * np.exp(-alpha("lwir", sc) * R) / SUBCASES["clear_day"]["dT"][0]))


def depth_sigma(m, R=50.0):
    """Range (depth) error at R [m]."""
    if m["modality"] == "lidar":
        return m.get("range_accuracy", 0.1)
    if m["modality"] == "radar":                        # best operating mode that reaches R
        return min(m["modes"][k][1] for k in m.get("operating_modes", m["modes"]) if m["modes"][k][0] >= R)
    return 0.10 * R                                     # monocular: depth from object size, ~10 % size prior


def speed_sigma(m, R=50.0):
    """Radial-speed error [m/s] at R, known within T_SPEED: radar measures Doppler in one cycle, lidar
    differences two ranges, camera/thermal use the change of the object's image height (the size prior
    cancels; only the box-height noise counts)."""
    mod = m["modality"]
    if mod == "radar":
        return m["modes"]["extra_long"][2]
    if mod == "lidar":
        return np.sqrt(2) * m.get("range_accuracy", 0.1) / T_SPEED
    h_px = TARGETS["pedestrian"]["h"] / (R * pixel_angle(m))
    return np.sqrt(2) * R * BOX_JITTER_PX / h_px / T_SPEED


LIVING_CAP = {"thermal": 1.0, "camera": 0.85, "lidar": 0.7, "radar": 0.3}   # rule: heat > appearance > shape > micro-Doppler
COLOR = {"camera": 1.0, "lidar": 0.15, "thermal": 0.0, "radar": 0.0}        # rule: colour channels (lidar: NIR intensity)


def sensor_scores(m, sub):
    """The six axis scores (0..1) of one sensor model in one sub-case."""
    mod, sc = m["modality"], SUBCASES[sub]
    av = availability(m, sub)
    res = log_score(max(samples_on_pedestrian(m), 1), 1, 1000)
    car_range = effective_range(m, "car", sub)
    color = COLOR[mod] * av * (0.3 if (mod == "camera" and sc["night"]) else 1.0)
    living = LIVING_CAP[mod] * av
    if mod in ("camera", "thermal"):
        living *= min(1.0, effective_range(m, "pedestrian", sub) / 50)
    return {
        "Contrast, resolution": res * av,
        "Range": min(1.0, car_range / RANGE_REQ),
        "Color": color,
        "Speed detection": log_score(speed_sigma(m), 5.0, 0.05) * av,
        "3D reconstruction": 0.5 * (log_score(depth_sigma(m), 5.0, 0.02) + res) * av,
        "Living objects": living,
    }


def load_suite(path="sensors.yaml"):
    with open(path, encoding="utf-8") as f:
        d = yaml.safe_load(f)
    models, mounts = d["models"], d["mounts"]
    for _, model, _, _, z, _ in mounts:          # per-channel lidars need their table and mounting height
        m = models[model]
        if "channels" in m and "ch" not in m:
            with open(m["channels"], encoding="utf-8") as f:
                rows = [line.strip().split(",") for line in f if line.strip() and not line.startswith("#")]
            m["ch"] = {k: np.array([float(r[i]) for r in rows[1:]]) for i, k in enumerate(rows[0])}
            m["mount_z"] = z
    return models, mounts


def spider_scores(models, mounts):
    """{group: {modality: {axis: score}}}; a modality's score is its best forward-looking sensor,
    in the worst sub-case of the group. 'Whole suite' is the best modality per axis."""
    fwd = {mid for _, mid, *_, yaw in mounts if abs(yaw) <= FORWARD_YAW and models[mid]["modality"] != "gnss_ins"}
    out = {}
    for g, subs in GROUPS.items():
        out[g] = {}
        for mod in ("camera", "lidar", "radar", "thermal"):
            mids = [k for k in fwd if models[k]["modality"] == mod]
            per = [{a: min(sensor_scores(models[k], s)[a] for s in subs) for a in AXES} for k in mids]
            out[g][mod] = {a: max(p[a] for p in per) for a in AXES}
        out[g]["whole suite"] = {a: max(out[g][mod][a] for mod in ("camera", "lidar", "radar", "thermal")) for a in AXES}
    return out


def range_table(models):
    rows = []
    for mid, m in models.items():
        if m["modality"] == "gnss_ins":
            continue
        for sub in SUBCASES:
            rows.append((mid, m["modality"], sub,
                         effective_range(m, "pedestrian", sub), effective_range(m, "car", sub)))
    return rows


def main():
    models, mounts = load_suite()
    rows = range_table(models)
    with open("ranges.csv", "w", encoding="utf-8") as f:
        f.write("model,modality,condition,pedestrian_m,car_m\n")
        f.writelines(f"{a},{b},{c},{p:.0f},{q:.0f}\n" for a, b, c, p, q in rows)
    print(f"{'model':24s}" + "".join(f"{s:>15s}" for s in SUBCASES))
    for mid in dict.fromkeys(r[0] for r in rows):
        cells = [f"{p:6.0f}/{q:<6.0f}  " for a, _, _, p, q in rows if a == mid]
        print(f"{mid:24s}" + "".join(f"{c:>15s}" for c in cells))
    print("(pedestrian / car detection range in metres)\n")

    sp = spider_scores(models, mounts)
    with open("spider_scores.csv", "w", encoding="utf-8") as f:
        f.write("condition,modality," + ",".join(f'"{a}"' for a in AXES) + "\n")
        for g, mods in sp.items():
            for mod, s in mods.items():
                f.write(f"{g},{mod}," + ",".join(f"{s[a]:.2f}" for a in AXES) + "\n")
    for g, mods in sp.items():
        print(g)
        for mod, s in mods.items():
            print(f"  {mod:12s}" + "  ".join(f"{a.split(',')[0][:8]:>8s} {s[a]:.2f}" for a in AXES))


if __name__ == "__main__":
    main()
