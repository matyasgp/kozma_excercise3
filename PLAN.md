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

## Status (2026-11-24): all steps done

| Step | Where | Result |
|---|---|---|
| 1 Requirements | `requirements.py`, `figures/requirements*.png` | ahead 253 m car / 82 m pedestrian, sides 81 m, rear 96 m, 15 m pedestrians around, near field 0.1–5 m; front/rear cones from road curvature |
| 2 Physics model | `model.py` | ranges and spider scores; camera speed from image-height change; radar antenna pattern and interleaved modes; InnovizTwo side FOV |
| 3 Spider charts | `spider.py` | one chart per condition, modalities overlaid + whole suite (validated colorblind-safe palette) |
| 4 Coverage map | `coverage.py` | three rings (car, pedestrian, near field) per condition; gaps: fog ahead (none), snow ahead (camera only), near field (cameras only), straight behind (5° at night, 1° in fog) |
| 5 Cost | `bom.py` | 10,986 USD |
| 6 L5 slide | `odd.py` | safe speed with two modalities: 142 clear, 78 night with pedestrians, 84 fog (200 m), 124 snow; fog sweep with LWIR sensitivity band |
| 7 Pitch | `slides/`, `docs/` | beamer pitch + backup (B1–B13), `pitch.pptx` for Google Slides, speaker notes, Q&A guide |

Changes against the plan above, and why:
- Coverage figure: four donuts in one row (fits a 16:9 slide better than 2 × 2), with three rings instead of one.
- Requirement sectors come from road geometry (curve radius + lane offset) instead of a linear taper, which
  had produced a false 1° gap at the edge of the InnovizTwo ROI.
- Rear requirement 96 m (scenario-derived) instead of the ~100 m estimate; side 81 m instead of ~80 m.
- Added: safe speed per condition (`odd.py`) as the quantitative L4/L5 argument.
- Teacher's direction (2026-11-24): use the specs of a specific, existing model. Every sensor now cites its maker's
  own document. The Hesai OT128 moved from the spec web page to the full user manual (O01-en-260110): ±3 cm, the
  −25°/+15° split, 10 Hz, 70 % detection probability, and the per-channel table, modelled channel by channel
  (car 214 m instead of 230 m). The slides name every camera model (Supertek STC-OX08BC, SENSING SG3S-ISX031C).

## Open items
- Team names (missing in Ex3 too).
- Decide whether to add an ultrasonic ring to the suite (our coverage map asks for it; the deck lists it as the next gap to close).
- Import `slides/pitch.pptx` into Google Slides (File > Import slides) and share with the team.
