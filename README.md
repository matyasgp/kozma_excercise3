# Kozma Exercise 4: Sensor modality comparison (compare and design)

Task: pick cameras, lidars and radars for a self-driving car; compare the modalities on spider charts
under different conditions; design a sensor setup for city + highway; answer "Is Level 5 possible today?";
5-minute pitch.

- `PLAN.md`: agreed decisions, steps, originality rules (products earlier groups used are excluded).
- `sensors.yaml`: the 20-sensor lean suite (2 lidar, 5 radar, 11 camera, 1 thermal, 1 GNSS/INS) with mounts, official sources and the numbers the scripts use.

The course deck and datasheet PDFs stay local in `sources/` (gitignored).
- `requirements.py`: required detection range per direction, each from one driving scenario and one formula (`python requirements.py` prints the table).
- `model.py`: the physics model. For every sensor and condition it computes the pedestrian and car detection
  range and the six spider scores (professor's template axes). `python model.py` prints the tables and writes
  `ranges.csv` and `spider_scores.csv`.

## Model assumptions (ours, not from datasheets)

| Assumption | Value | Why |
|---|---|---|
| Lidar detection rule | ≥ 5 returns with 99 % probability | EBA rule from Exercise 3 |
| Lidar per-beam probability behind the 10 % range | 90 % | InnovizTwo datasheet; assumed for OT128 too |
| Camera/thermal detection rule | object ≥ 25 px high | KITTI "moderate" minimum box height |
| Minimum usable camera contrast | 0.05 | pedestrian 0.3, car 0.4 at zero range |
| Night | unlit road; low beam 4000 cd ahead, 1 lux needed on a pedestrian; cars carry their own lights | worst case for "general use" |
| Clear air | visibility 23 km | standard clear atmosphere (Exercise 3 used perfectly clear air, so its 235 m pedestrian range is 231 m here) |
| Fog / snow / heavy rain | V = 200 m / V = 1 km + 50 % lidar clutter / 25 mm/h | dense fog, moderate snow, heavy rain |
| Extinction | Koschmieder α = 3.912/V, same at 550/905/1550 nm below V = 500 m (Kim 2001); rain 0.365 R^0.63 /km | standard laws |
| LWIR in fog | 0.4 × visible extinction | depends on droplet size (literature ~0.2–1) |
| Radar | 77 GHz rain attenuation from ITU-R P.838-3; pedestrian RCS 0.3 m², car 10 m² | |
| Low-sun glare | veiling glare 3 × background on forward cameras | |
| Tunnel exit | 125 dB scene dynamic range vs camera HDR (140 dB OX08B40, 120 dB ISX031) | |
| Thermal contrast ΔT (pedestrian) | 5 K day, 10 K night, 3 K wet (fog/rain), 15 K snow | |
| Rule-based axes | Color: camera 1, lidar 0.15 (NIR intensity), thermal/radar 0. Living objects cap: thermal 1, camera 0.85, lidar 0.7, radar 0.3 | not physics; labelled as rules on the slide |
| Speed detection | radial-speed error known within 100 ms: radar Doppler (one cycle); lidar differences two ranges; camera/thermal use the change of the object's image height with 1 px box noise | the size prior cancels in the change |
| Radar off boresight | one-way gain −3 (φ/40°)² dB, so range × 0.58 at the ±50° FOV edge | datasheet: the 3 dB FOV is narrower than ±50° |
| Radar modes | every radar interleaves extra-long-range (240 m) and short-range (0.2–40 m) cycles | modes switch at runtime (datasheet) |
| InnovizTwo outside the ROI | 140 m at 10 %, 0.2° × 0.05° (datasheet side FOV) | ROI is the central 30° |
