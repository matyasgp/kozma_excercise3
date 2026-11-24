# Q&A guide

Likely questions, a short answer to give, and the backup slide to show (`slides/backup.pdf`, B1–B13).
All numbers come from the scripts; the CSV files in the repo root have the rest.

## The verdict

**"You say Level 5 is not possible but your car drives in city and highway. Isn't that Level 5?"**
No. SAE J3016 defines Level 5 as driving everywhere a human could, with no limit on the operating domain.
A system limited to city + highway, or one that has to slow down or stop in some weather, is Level 4. That is
our answer: Level 4 in city + highway inside a speed envelope, yes; Level 5, no. (Slide 5, B10)

**"Why is Level 5 impossible? Just add more sensors."**
Three reasons, only one about sensors. (1) Physics: in dense fog every optical sensor loses half its range or
more; radar alone sees far but nothing confirms it, so the car must slow. A human must too (German law: 50 km/h
below 50 m visibility). (2) Sensors get blocked by snow, ice or spray, and no datasheet covers that. (3) Rare
events: showing a system is safer than humans needs hundreds of millions to billions of test miles (RAND
2016), and the law approves only defined domains (UNECE R157 for L3, the German 2021 L4 law).

**"What would close your gaps?"**
An ultrasonic ring for the near field, a rear thermal camera (night, behind), and a slightly longer-range
imaging radar (ours reaches 240 m, 5 % short of 253 m). (B13)

## Requirements

**"Where does 253 m come from? Exercise 3 used 250 m and you computed 127 m there."**
Stopping from 130 km/h with 1 s reaction and comfortable braking (3 m/s²): 36 + 217 = 253 m. An automated car
should plan to stop without emergency braking. With the Exercise 3 emergency values (0.5 s, 6 m/s²) it would
be 127 m, so 253 m leaves the margin for confirming a detection. (B5)

**"Why does the front requirement only hold within ±11°?"**
A lane that curves with the tightest highway radius (720 m) is d/(2R) = 10° off-axis at 253 m; the 3.5 m lane
offset adds about 1°. Further out, a lane at 253 m along the road can't be there. (B5)

**"Why 81 m at the sides and 96 m behind?"**
Sides: pulling out across two lanes takes 4.9 s (1 s + accelerating 15 m at 2 m/s²); cross traffic at 60 km/h
covers 81 m. Rear: a 3 s lane change while a car 60 km/h faster approaches, which then has to brake at
3 m/s²: 50 + 46 = 96 m. These are our scenario choices; the formula is on B5.

**"Why two modalities?"**
Diverse redundancy: one modality may fail (a fault) or be fooled (glare, fog, a radar ghost) without the car
going blind. Camera and lidar are both optical and both suffer in fog, which the coverage map shows: in fog
the second modality ahead is missing.

## The comparison (spider charts)

**"Are the spider scores your opinion?"**
No, four of six axes are computed from datasheet numbers and one physics law per effect. Two parts are rules
and labelled so: the color axis and the cap on the living-objects axis. Every score is in
`spider_scores.csv`. (B4)

**"Why is the camera so weak on speed detection?"**
The axis is radial speed known within 100 ms. Radar measures it directly by Doppler (0.07 m/s). A camera
infers it from how fast the object's image grows; with a 1-pixel box noise on a pedestrian at 50 m that is
2.5 m/s. Cameras are good at sideways (angular) speed, which this axis doesn't score. (B4)

**"Why does glare not shorten the camera's range?"**
Glare cuts contrast (score 0.25), but in clear air contrast fades so slowly with distance that the 25-pixel
rule still sets the range. The 140 dB HDR covers a 125 dB tunnel exit. Range would drop with glare and haze
together, or with the sun within a few degrees of the object; we don't model that case. (B3)

**"Thermal reaches only 90 m but Raytron says 169 m."**
Raytron's 169 m uses the Johnson criterion for identification, which needs fewer pixels. We use one rule for
all imagers: the object must be 25 pixels tall (KITTI's minimum box). With 0.8 mrad pixels that is 90 m for a
pedestrian. (B3)

**"How did you model fog for the lidar? 905 nm vs 1550 nm?"**
Koschmieder, α = 3.912/V. Below 500 m visibility the extinction is about the same at 550, 905 and 1550 nm
(Kim et al. 2001), so the wavelength doesn't save you in dense fog. (B2)

**"The night case looks harsh for cameras."**
It is the worst case: an unlit road, where only the low beam (4000 cd, ±30°) lights a pedestrian, 63 m
ahead. On lit city streets the camera does much better; cars carry their own lights, so the camera still sees
them at full range. (B3)

## The design

**"Why two lidars?"**
The front InnovizTwo has a 30° high-resolution ROI that sees a dark car at 300 m; that is the only lidar
reaching the 253 m requirement. The roof OT128 sees 360° for the sides and the rear (a car at 230 m against
81–96 m needed). (Slide 3, B7)

**"Why only one thermal camera?"**
The thermal case is pedestrians at night ahead, where the camera reaches only 63 m of the 82 m needed. At the
sides and behind, lidar and radar already give two modalities at 15 m. The one exception is 5° straight
behind at night, which is why a rear thermal camera is on our list. (B8, B13)

**"Why no ultrasonic sensors? Every car has them."**
Our coverage map found exactly that: the near field rests on the fisheye cameras alone on 340°, because lidar
and radar have minimum ranges (0.2–0.3 m) and nothing else looks down beside the doors. An ultrasonic ring is
the first thing we would add. (Slide 4, B13)

**"Five radars and two lidars: interference?"**
Not modelled. The DRVEGRD 171 offers four non-overlapping frequency bands in extra-long-range mode, meant for
this. (B11)

**"Is the cost realistic?"**
Order of magnitude only. The fisheye price is listed by its seller; the rest are our estimates. Sensors only:
no compute, cleaning, wiring or calibration. (B12)

**"Didn't an earlier group use the OT128?"**
Yes, one group did, and we reused it on purpose: it is a sourced 360° lidar. Its spec page does not give range
accuracy, the vertical split or the frame rate, so we use the InnovizTwo's 10 cm (conservative) and mark the
rest as assumptions. Everything else in the suite is new to the course. (B1, B11)

## The model

**"How do you know the coverage map is right?"**
It is plain geometry: mounts and fields of view from `sensors.yaml`, ranges from the same model as the spider
charts, checked bearing by bearing (B8–B9, `coverage.csv`). The model agrees with Exercise 3: InnovizTwo dark
pedestrian at 231 m here vs 235 m there; the 4 m difference is that clear air now has 23 km visibility.

**"What is not modelled?"**
Lens dirt, spray and blocked sensors; raindrops on lenses; false positives; interference; occlusion by other
road users; classification quality; compute and latency. (B11)

**"Which assumption matters most?"**
The LWIR fog extinction ratio (0.4 × visible). If thermal sees no further than visible light in fog, the safe
speed at 50 m visibility drops from 66 to 52 km/h. The fog chart shows both as a band. (B10, B11)

**"Your table says 142 km/h in clear weather, above the 130 km/h you designed for."**
That is the highest speed the sensors would support. The design speed and the legal limit still apply.
