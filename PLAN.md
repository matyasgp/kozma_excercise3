# Exercise 4 – Sensor modality comparison: Compare and design (plan)

Task (slide 1 of the deck; slides 2–172 are earlier years' solutions and are ignored):
pick cameras, lidars and radars; compare the modalities on spider charts under different
conditions; design a sensor setup for a general city + highway car; answer "Is Level 5
possible today?"; pitch in 5 minutes, team of 3–5.

## Decisions (agreed 2026-11-21)

| Topic | Choice |
|---|---|
| Vehicle | Generic private car, city + highway |
| Philosophy | Lidar-heavy (Waymo-like), Waymo-scale suite (~30+ sensors) |
| Front long-range lidar | InnovizTwo (datasheet v3.1), reusing the Exercise 3 EBA result at 250 m |
| Extra modalities | Thermal (LWIR) cameras; GNSS/IMU + HD map as a "virtual sensor" |
| Products | Only sensors with a public official datasheet, cited on the slide |
| Spider scores | Physics-derived in Python, reproducible from datasheet numbers |
| Conditions | Day clear; night; fog / heavy rain; snow / low-sun glare / tunnel |
| Axes | Range, angular resolution, velocity, depth accuracy, color/semantics, small/living objects |
| Chart layout | One chart per modality (camera, lidar, radar, thermal), with the conditions as overlaid polygons |
| Layout figure | Python top-down FOV map built from a sensor config, with overlap counts per zone |
| Budget | Rough BOM: price per sensor and a total |
| L5 answer | Conditional yes: within the task's "general use" (city + highway) the suite suffices; true "anywhere, anytime" L5 does not |
| Workflow | As in Ex3: Python + figures in the Ex3 GitHub repo (kozma_excercise3, reused; push after every change), beamer draft, final pitch in Google Slides |
| Team | Same as Ex3; the names are still "TBD" there too, so fill them in |

## Steps

1. **Repo setup** – `git init` in Excercise4, add a `.gitignore` (the .pptx, `sources/`, LaTeX build), create
   github.com/matyasgp/kozma_excercise3 (the Ex3 repo, reused; Ex3 files removed, still in its history), and push.
2. **Sensor selection** (`sensors.yaml`: model, datasheet URL, mount x/y/z, yaw, HFOV/VFOV, range,
   resolution, wavelength/frequency, HDR dB / NETD, price). **Done**: 30 sensors, none on the excluded list below:
   - Lidar (9): front InnovizTwo (our Ex3 work); roof ring of 3 × Seyond Falcon K2 Pro (front, left, right)
     + Valeo SCALA 3 (rear); 4 × Seyond Robin W1G near-field corners.
   - Radar (6): smartmicro DRVEGRD 171 4D radar, front, rear and 4 corners (mode chosen per position).
   - Camera (12): Supertek OX08B40 8 MP modules (30°/60°/120° lenses): front tele/main/wide, 4 side, rear;
     4 × SENSING ISX031 196° fisheyes.
   - Thermal (2): Raytron Horus640-D, 32° (highway) and 48° (city) lenses, both forward.
   - GNSS/INS: OxTS RT3000 v4 + HD map (no FOV; listed in the BOM and the localization argument).
   - Dropped on 2026-11-24 because they have no public datasheet: Aeva Atlas, AdaSky Viper, and OX03F10
     fisheyes (only Leopard modules exist). Valeo SCALA 3 and OxTS have official spec pages, not PDFs.
3. **Physics scoring model** (`spider.py`). Each axis is normalised 0–1 against a requirement
   (e.g. range against the 250 m EBA / braking distance at 130 km/h):
   - Range: lidar/radar from the datasheet at 10 % reflectivity / pedestrian RCS; camera/thermal from
     pixels-on-target (Johnson-style detection criterion for a 1.8 m pedestrian).
   - Angular resolution: datasheet IFOV.
   - Velocity: radar direct Doppler; lidar by frame differencing, σ_v ≈ √2·σ_r/Δt; camera by optical flow + depth error.
   - Depth accuracy: lidar ranging precision; radar c/2B; camera/thermal σ_z = z²·σ_d/(f·b) (or monocular prior).
   - Color/semantics: spectral channels × resolution (camera full, thermal partial, lidar intensity only, radar none).
   - Small/living objects: points or pixels on a 0.5 m object at 50 m; living-object bonus from thermal contrast.
   - Condition modifiers:
     - Fog/rain: Beer–Lambert with wavelength-dependent α (Kim/Kruse for fog, empirical rain laws at 905/1550 nm,
       ITU-R P.838 at 77 GHz, LWIR transmission); lidar range found by solving ρ·e^(−2αR)/R² = threshold.
     - Night: camera range capped by headlight illumination / SNR; lidar, radar and thermal unaffected.
     - Snow: lidar backscatter clutter, loss of camera contrast.
     - Glare/tunnel: scene dynamic range (~140 dB) vs. the camera's HDR dB.
   - Output: 4 spider charts with 4 condition polygons each, plus a CSV of every number for Q&A.
4. **Coverage map** (`coverage.py`): top-down FOV wedges per modality, an overlap-count heatmap and a check that
   every 360° sector has ≥2 modalities, with the near-field blind zone marked.
5. **BOM**: a table with price per sensor (public or estimated, with the source marked) and the total.
6. **L5 argument**: the Conditional yes, built from our own numbers: which conditions the fused suite still loses
   (e.g. dense fog + snow, sensor contamination) and why those fall outside city + highway "general use".
7. **Beamer draft → Google Slides** (~6 slides / 5 min): concept, suite and coverage map, spider charts,
   BOM, the L5 answer, plus backup slides and a Q&A doc like in Ex3.

## Originality (don't copy old solutions)

Checked against slides 3–172 of the deck (seven earlier groups) on 2026-11-21.

**Excluded products** (already used by earlier groups):
- Lidar: Hesai AT128/OT128, RoboSense M1/Airy, AEye Apollo, Luminar Iris/Hydra, Ouster, Quanergy M8, Velodyne, Cepton
- Radar: Continental ARS540/ARS640/ARS5xx/SRR52x/SRR308/SRR620, Bosch, Arbe, Aptiv
- Camera: Sony IMX490/IMX390/IMX424/IMX291/IMX219, onsemi AR0231/AR0233/AR0234, Leopard Imaging,
  Sekonix, Edge.Auto C2, Bosch camera heads
- Thermal: Teledyne FLIR ADK, FLIR Duo Pro R, FLIR Blackfly/Oryx
- Compute: NVIDIA Drive Orin/Thor (we have no compute section anyway)

**Ideas no earlier group used, which we make central:**
- Physics-derived scores. Every earlier spider chart was hand-scored, and none modelled attenuation,
  pixels-on-target or Doppler.
- An auto-generated coverage map with an overlap count per sector, instead of a hand-drawn diagram.
- The L5 answer framed as "yes, if L5 = city + highway", backed by our own numbers. Earlier groups said "No",
  "Well yes, but actually no", or gave generic feasibility lists.

**Overlaps we keep but must argue differently:**
- Thermal cameras (several groups used FLIR ADK): we use Raytron Horus640-D and justify it with LWIR fog
  transmission and pedestrian contrast numbers.
- Roof 360° lidar + corner lidars (group 6): the layout must come out of the coverage check, not a stock picture.

Don't open the old slides for structure or wording while building ours.

## Open items
- Team names (missing in Ex3 too).
- Confirm that each candidate sensor has an official public datasheet; swap any that don't.
