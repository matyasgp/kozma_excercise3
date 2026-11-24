# Kozma Exercise 4: Sensor modality comparison (compare and design)

Task (slide 1 of the course deck): pick cameras, lidars and radars for a self-driving car; compare the
modalities on spider charts under different conditions; design a sensor setup for a general city + highway
car; answer "Is Level 5 possible today?"; 5-minute pitch.

**Our answer in one line:** a 20-sensor, ~11k USD suite gives at least two independent modalities on every
bearing in clear weather and at night. In dense fog nothing reaches the 253 m highway stopping distance, so
the car has to slow to about 84 km/h, as a careful driver would. That makes it **Level 4 in city + highway
within a speed envelope**. True **Level 5 (anywhere, any weather) is not possible today**.

## How it fits together

One physics model drives every number. Requirements → physics → design → verdict:

```
requirements.py   required range per direction (driving scenarios)  ─┐
sensors.yaml      20 sensors: datasheet numbers + mounts             ─┤
model.py          range + spider scores per sensor and condition     ─┼─> spider.py    spider charts
                                                                      ├─> coverage.py  coverage map per condition
                                                                      ├─> odd.py       highest safe speed per condition
                                                                      ├─> layout.py    suite layout, reach, requirements figures
                                                                      └─> bom.py       cost table
```

Run everything (Python 3 with numpy, matplotlib, pyyaml; about 15 s):

```
python requirements.py && python model.py && python spider.py && python coverage.py && python odd.py && python layout.py && python bom.py
```

| File | What it is | Writes |
|---|---|---|
| `PLAN.md` | agreed decisions, steps, originality rules | |
| `sensors.yaml` | the suite: 2 lidar, 5 radar, 11 camera, 1 thermal, 1 GNSS/INS, with mounts, official sources, prices | |
| `requirements.py` | required detection range per direction, each from one scenario and one formula | |
| `model.py` | detection range and the six spider scores per sensor and condition | `ranges.csv`, `spider_scores.csv` |
| `spider.py` | one spider chart per condition (professor's axes), modalities overlaid + whole suite | `figures/spider_*.png/pdf` |
| `coverage.py` | per bearing and condition: how many modalities reach the required range (car, pedestrian, near field) | `coverage.csv`, `figures/coverage_*.png/pdf` |
| `odd.py` | highest speed with two modalities covering the stopping distance; fog visibility sweep | `safe_speed.csv`, `figures/safe_speed_fog.png/pdf` |
| `layout.py` | mounting layout, reach per modality, requirement contour | `figures/suite_layout.png`, `figures/reach_by_modality.png`, `figures/requirements.png` |
| `bom.py` | count × unit price per model | `bom.csv` |
| `slides/` | beamer draft of the pitch (`presentation.tex`) and backup slides (`backup.tex`) | PDFs |
| `docs/` | speaker notes and Q&A guide | |

The course deck and datasheet PDFs stay local in `sources/` (gitignored).

## Requirements (`requirements.py`)

Detection-to-action time 1 s, comfortable braking 3 m/s² (an automated car should plan to stop without
emergency braking).

| Direction | Target | Scenario | Range |
|---|---|---|---|
| front (±11°) | car | stop from 130 km/h: v·1 s + v²/(2·3 m/s²) | 253 m |
| front (±23°) | pedestrian | stop from 70 km/h (urban arterial) | 82 m |
| sides | car | pull out across two lanes (4.9 s) before cross traffic at 60 km/h arrives | 81 m |
| rear (±6°) | car | 3 s lane change, a car closing at 60 km/h then brakes at 3 m/s² | 96 m |
| sides, rear | pedestrian | a jogger (3 m/s) during the 4.9 s turn or pull-out | 15 m |
| all round | 0.5 m object | parking, kerbs, a child beside the car | 0.1–5 m |

The cones come from road geometry: a lane on a curve of radius Rc is d/(2Rc) off-axis at distance d, plus
the lane offset (720 m highway curve and 3.5 m lane for cars; 120 m urban curve and 5 m kerb offset for
pedestrians). **Design rule:** on every bearing at least two independent modalities (camera, lidar, radar,
thermal) must reach the required range, so one modality can fail or be fooled.

## Results

Detection range ahead (pedestrian / car, metres, `ranges.csv`):

| Sensor | Clear | Night | Fog 200 m | Rain 25 mm/h | Snow |
|---|---|---|---|---|---|
| InnovizTwo lidar | 231 / 300 | 231 / 300 | 98 / 114 | 178 / 240 | 150 / 197 |
| Hesai OT128 lidar | 153 / 230 | 153 / 230 | 86 / 100 | 145 / 193 | 126 / 162 |
| DRVEGRD 171 radar | 100 / 240 | 100 / 240 | 100 / 239 | 89 / 190 | 98 / 234 |
| 8 MP camera, 30° | 557 / 464 | 63 / 464 | 92 / 106 | 557 / 464 | 458 / 464 |
| Raytron LWIR | 90 / 75 | 90 / 75 | 90 / 75 | 90 / 75 | 90 / 75 |

Coverage (`coverage.py`, worst sub-case of each condition):

| Condition | Car ring | Pedestrian ring | Near field |
|---|---|---|---|
| Clear day | 2+ everywhere | 2+ everywhere | cameras only on 340° |
| Night (unlit) | 2+ everywhere | 2+ except 5° straight behind (lidar only) | cameras only on 340° |
| Fog / heavy rain | **gap ahead (±11°)**: radar 239 m, lidar 114 m < 253 m | 2+ everywhere | cameras only on 340° |
| Snow / glare / tunnel | camera only ahead (±11°) | 2+ everywhere | cameras only on 340° |

Highest safe speed with two modalities over the stopping distance (`odd.py`): clear 142 km/h, night with
pedestrians 78 km/h, fog (V = 200 m) 84 km/h for cars / 77 km/h with pedestrians, snow 124 / 98 km/h.
Below 50 m visibility: 40–70 km/h depending on how well LWIR sees through the fog (German law: 50 km/h).

Cost (`bom.py`): 10,986 USD for the 20 sensors (lidar 4,000, camera 3,936, radar 2,000, thermal 800,
GNSS/INS 250). Only the fisheye price is listed by its seller; the rest are our estimates.

## Model assumptions (ours, not from datasheets)

| Assumption | Value | Why |
|---|---|---|
| Lidar detection rule | ≥ 5 returns with 99 % probability | EBA rule from Exercise 3 |
| Lidar per-beam probability at the 10 % datasheet range | 90 % | InnovizTwo datasheet; assumed for OT128 too |
| OT128 range accuracy, vertical split, frame rate | 10 cm (InnovizTwo datasheet value), −25°/+15°, 10 FPS | not on Hesai's spec page |
| Camera/thermal detection rule | object ≥ 25 px high | KITTI "moderate" minimum box height |
| Minimum usable camera contrast | 0.05 | pedestrian 0.3, car 0.4 at zero range |
| Night | unlit road; low beam 4000 cd, ±30° spread, 1 lux needed on a pedestrian; cars carry their own lights | worst case for "general use" |
| Clear air | visibility 23 km | standard clear atmosphere (Exercise 3 used perfectly clear air, so its 235 m pedestrian range is 231 m here) |
| Fog / snow / heavy rain | V = 200 m / V = 1 km + 50 % lidar clutter / 25 mm/h | dense fog, moderate snow, heavy rain |
| Extinction | Koschmieder α = 3.912/V, same at 550/905 nm below V = 500 m (Kim 2001); rain 0.365 R^0.63 /km | standard laws |
| LWIR in fog | 0.4 × visible extinction | depends on droplet size (literature ~0.2–1); `odd.py` also shows 1.0 |
| Radar | 77 GHz rain attenuation from ITU-R P.838-3; pedestrian RCS 0.3 m², car 10 m² | |
| Radar off boresight | one-way gain −3 (φ/40°)² dB, so range × 0.58 at the ±50° FOV edge | datasheet: the 3 dB FOV is narrower than ±50° |
| Radar modes | every radar interleaves extra-long-range (240 m) and short-range (0.2–40 m) cycles | modes switch at runtime (datasheet) |
| InnovizTwo outside the ROI | 140 m at 10 %, 0.2° × 0.05° | datasheet side FOV; ROI is the central 30° |
| Low-sun glare | veiling glare 3 × background on forward cameras | |
| Tunnel exit | 125 dB scene dynamic range vs camera HDR (140 dB OX08B40, 120 dB ISX031) | |
| Thermal contrast ΔT (pedestrian) | 5 K day, 10 K night, 3 K wet (fog/rain), 15 K snow | |
| Surround fisheyes | pitched down 20° (front/rear) and 40° (mirrors) | typical surround-view mounting |
| Near field | geometry only (FOV, height, pitch, minimum range, roof lidar blocked by the body); the car's lamps light the first metres at night | |
| Rule-based axes | Color: camera 1, lidar 0.15 (NIR intensity), thermal/radar 0. Living objects cap: thermal 1, camera 0.85, lidar 0.7, radar 0.3 | not physics; labelled as rules on the slides |
| Speed detection | radial-speed error known within 100 ms: radar Doppler (one cycle); lidar differences two ranges; camera/thermal use the change of the object's image height with 1 px box noise | the size prior cancels in the change |
| Spider scores | log scale between a worst and a best value per axis, times the share of signal left in the condition at 50 m | see `sensor_scores` in `model.py` |

Known limits: no lens soiling, spray or sensor blockage (snow on the bumper); thermal range uses the 25 px
detection rule (90 m), while Raytron quotes 169 m with the looser Johnson identification rule; false
positives are not modelled.
