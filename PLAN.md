# Exercise 4 – Sensor modality comparison: Compare and design (plan, redesigned 2026-11-24)

Task (slide 1 of the deck; slides 2–172 are earlier years' solutions and are ignored):
pick cameras, lidars and radars; compare the modalities on spider charts under different
conditions; design a sensor setup for a general city + highway car; answer "Is Level 5
possible today?"; pitch in 5 minutes, team of 3–5.

## Why the redesign

The first plan (2026-11-21) had five problems:
1. A "private car" with a Waymo-scale suite (9 lidars, ~$25k of lidar alone) contradicts itself.
2. "Yes, if L5 = city + highway" is Level 4 by the SAE definition (L5 has no operating-domain limit).
3. Our spider axes ignored the professor's template on slide 1.
4. Nothing connected the spider charts to the design.
5. 30 sensors and 16 charts don't fit 5 minutes.

## Core idea

**Requirements → physics → design → verdict, with one model behind all of it.**
One Python model gives every modality's performance per condition. The same numbers then feed:
- the spider charts (which modality wins when), and
- a coverage map per condition (in each direction, how many independent modalities still reach the
  required distance).

So every sensor on the car is there because a number asks for it, and the L5 answer reads straight off the
worst-condition coverage map.

## Decisions

| Topic | Choice |
|---|---|
| Vehicle | Lean private car, city + highway, no roof dome except the 360° lidar |
| Suite | 20 sensors: 2 lidar, 5 radar, 11 camera, 1 thermal, 1 GNSS/INS (see `sensors.yaml`) |
| Lidar layout | InnovizTwo front long-range (our Exercise 3 work) + Hesai OT128 360° on the roof |
| Spider axes | The professor's template: contrast/resolution, range, color, speed detection, 3D reconstruction, living objects |
| Spider layout | One chart per condition with camera, lidar, radar and thermal overlaid, plus a "whole suite" outline (best modality per axis) |
| Conditions | Clear day; night; fog / heavy rain; snow / low-sun glare / tunnel exit |
| Scores | Physics-based where physics applies, rule-based (and labelled so) where it doesn't (color) |
| Core figure | Coverage map per condition against a required-range ring |
| Cost | No target; the total is reported |
| L5 answer | Conditional yes, stated precisely: "In city + highway, in the conditions our map covers, the suite supports L4. True L5 (anywhere, anytime) is not possible today." |
| Products | Official datasheets or manufacturer spec pages only. A few sensors earlier groups used may be reused on purpose (now: Hesai OT128); no group's suite, layout or method is copied |
| Pitch | 6 slides, numbers first; details in backup |
| Workflow | Python + figures in github.com/matyasgp/kozma_excercise3 (reused; push after every change), beamer draft, final pitch in Google Slides |
| Team | Same as Ex3; names still "TBD" there |

## Steps

1. **Requirements** (`requirements.py` or a table in `model.py`): required detection range per direction.
   - Front: 250 m, the stopping distance at 130 km/h plus reaction time (the Exercise 3 EBA figure).
   - Rear: ~100 m, for a car closing at Δv ≈ 50 km/h during a 3 s lane change, plus margin.
   - Sides: ~80 m, for cross traffic at 50 km/h at an intersection (~5 s gap).
   - Near field: 0.1–5 m all round (parking, kerbs, children).
   - Reference objects: pedestrian 1.8 × 0.5 m (ρ ≈ 10 %), car 1.8 × 1.5 m, 0.5 m debris.
2. **Physics model** (`model.py`), one function per effect, per modality and condition:
   - Range:
     - lidar: datasheet range at 10 %, reduced by Beer–Lambert, solving ρ·e^(−2αR)/R² = threshold (the Exercise 3 model);
     - radar: datasheet mode ranges, with ITU-R P.838 rain attenuation at 77 GHz;
     - camera/thermal: Johnson-criterion pixels on the pedestrian, reduced by Koschmieder contrast loss (camera)
       or LWIR transmission (thermal).
   - Contrast/resolution: angular resolution → points or pixels on the pedestrian at 100 m, times the condition's contrast factor.
   - Speed detection: radar Doppler accuracy (0.07 m/s); lidar frame differencing σ_v ≈ √2·σ_r/Δt; camera/thermal
     optical flow + depth error.
   - 3D reconstruction: depth accuracy at 50 m (lidar σ_r, radar range accuracy, camera/thermal monocular/stereo z²·σ_d/(f·b))
     × point density.
   - Living objects: thermal ΔT/NETD contrast; camera and lidar pixels/points on the pedestrian; radar micro-Doppler (low).
   - Color: rule-based (camera 1 in day, reduced at night; thermal, lidar and radar 0), labelled as a rule.
   - Conditions:
     - night: camera limited to headlight range / SNR; lidar, radar and thermal unchanged;
     - fog/rain: α per wavelength (550 nm, 905 nm, 8–14 µm, 77 GHz);
     - snow: lidar backscatter, camera contrast;
     - glare/tunnel: scene dynamic range vs. camera HDR (140 dB / 120 dB).
   - Output: a CSV of every number for Q&A.
3. **Spider charts** (`spider.py`): 4 charts (one per condition), 4 modality polygons + the whole-suite outline.
4. **Coverage map** (`coverage.py`): from `sensors.yaml` mounts and the model's ranges. For each 1° direction and each
   condition, count the modalities whose effective range ≥ the requirement. Show a 2 × 2 polar map (one per condition):
   green ≥ 2 modalities, orange 1, red 0. Mark the near-field blind ring.
5. **Cost** (`bom.py` or a table): price per sensor (listed or estimated, marked) and the total.
6. **L5 slide**: the red/orange sectors of the worst condition are the gaps. The suite supports L4 in city + highway in
   the covered conditions; true L5 is not possible today, because of the sensor gaps plus non-sensor reasons
   (long-tail validation, regulation). Also say what would close the gaps (more thermal, imaging radar, V2X).
7. **Pitch** (beamer draft → Google Slides), 6 slides + backup:
   1) requirements ring, 2) spider charts per condition, 3) the 20-sensor suite + cost, 4) coverage map per condition,
   5) L5 answer, 6) summary. Backup: datasheet table, model equations, CSV highlights, Q&A doc.

## Originality

Checked against slides 3–172 of the deck (seven earlier groups) on 2026-11-21.

Rule (relaxed on 2026-11-24): a few products earlier groups used may be reused on purpose; no group's suite,
layout or method is copied. Reused now: Hesai OT128 (one group's roof lidar).

Products earlier groups used:
- Lidar: Hesai AT128/OT128, RoboSense M1/Airy, AEye Apollo, Luminar Iris/Hydra, Ouster, Quanergy M8, Velodyne, Cepton
- Radar: Continental ARS540/ARS640/ARS5xx/SRR52x/SRR308/SRR620, Bosch, Arbe, Aptiv
- Camera: Sony IMX490/IMX390/IMX424/IMX291/IMX219, onsemi AR0231/AR0233/AR0234, Leopard Imaging,
  Sekonix, Edge.Auto C2, Bosch camera heads
- Thermal: Teledyne FLIR ADK, FLIR Duo Pro R, FLIR Blackfly/Oryx

What no earlier group did, and is central here:
- Spider scores computed from datasheets and physics; every earlier chart was hand-scored.
- One model driving both the spider charts and a coverage map per condition against required ranges.
- An L5 answer read off our own worst-condition map.

Don't open the old slides for structure or wording while building ours.

## Open items
- Team names (missing in Ex3 too).
- Requirement numbers (rear 100 m, side 80 m) are our estimates; derive them on the requirements slide.
