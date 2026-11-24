# Kozma Exercise 4: Sensor modality comparison (compare and design)

Task: pick cameras, lidars and radars for a self-driving car; compare the modalities on spider charts
under different conditions; design a sensor setup for city + highway; answer "Is Level 5 possible today?";
5-minute pitch.

- `PLAN.md`: agreed decisions, steps, originality rules (products earlier groups used are excluded).
- `sensors.yaml`: the 20-sensor lean suite (2 lidar, 5 radar, 11 camera, 1 thermal, 1 GNSS/INS) with mounts, official sources and the numbers the scripts use.

The course deck and datasheet PDFs stay local in `sources/` (gitignored).
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
| Speed detection | radial speed: radar Doppler; others differentiate two range readings | camera depth from object size (~10 % error) |
