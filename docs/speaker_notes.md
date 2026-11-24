# Speaker notes: 5-minute pitch (slides/presentation.pdf)

About 130 words per slide at a calm pace, so 45–50 s each. Numbers in **bold** are the ones to say out loud.
Who says which slide is up to the team; a split for three speakers is suggested at the end.

## Title (10 s)

"Our question was: what does a normal private car need to see to drive itself in the city and on the
highway, and is Level 5 possible today? One physics model, fed by official datasheets, answers both."

## 1. Requirements (45 s)

"We started from what the car must see, not from the sensors. Each number is one driving scenario and one
formula. To stop for a car from 130 km/h with one second to react and comfortable braking, the car must see
**253 m** ahead. For a pedestrian on a 70 km/h city road, **82 m**. At the sides, cross traffic at 60 km/h
needs **81 m** so we can pull out. Behind, a lane change with a faster car coming needs **96 m**. Around the
car, 15 m for pedestrians and the near field down to 10 cm.

Our design rule: on every bearing, at least **two independent modalities** must reach that range, so one
can fail or be fooled."

## 2. Compare: spider charts (50 s)

"Here are the four modalities on the professor's six axes, under four conditions. The scores are not hand-set:
each one comes from datasheet numbers and one physics law per effect, for example Koschmieder for fog or
the radar equation with rain attenuation.

The camera wins on detail and color in daylight, but at night its contrast falls to **0.16**, because only
the low beam lights a pedestrian. In fog the optical sensors lose about half their range; radar keeps
**0.75** and owns speed measurement with **0.07 m/s** Doppler. Lidar gives the best 3D, day and night.
Thermal sees living objects in the dark.

The gray area is the whole suite: the best modality on each axis. No single modality covers it, so we need
all four."

## 3. Design (50 s)

"So the suite has **20 sensors**, and every one is there because a number asks for it. An InnovizTwo lidar
in the bumper sees a dark car at **300 m**: it covers the 253 m requirement day and night. A 360-degree lidar
on the roof covers the sides and the rear. Five 4D radars, front and corners, measure speed and still reach
**239 m** in fog. Seven 8-megapixel cameras give color, signs and lights; the tele camera sees a car at
464 m. Four fisheyes cover the near field. One thermal camera is there because at night the camera only
reaches **63 m** but we need 82. GNSS with RTK and an HD map give lane-level position.

Total: about **11,000 USD** for the sensors."

## 4. Coverage (50 s)

"This is the core result. For every direction and condition we count how many modalities still reach the
required range. Green is two or more, amber one, red none. Outer ring cars, middle ring pedestrians, inner
ring the near field.

In clear weather and at night it's green all round. In dense fog, **nothing reaches 253 m ahead**: the radar
gets 239 m, the lidar 114 m. In snow only the camera does. And the near field is amber everywhere: below
about 30 cm and beside the doors only the cameras see, because lidar and radar have a minimum range. That's
our first thing to fix."

## 5. Is Level 5 possible today? (50 s)

"Level 5 means no limit at all on roads or weather. So we asked: how fast may our car drive so that two
modalities still cover its stopping distance? In clear weather, 142 km/h. At night with pedestrians around,
**78**. In fog with 200 m visibility, **84** for cars and **77** with pedestrians. Below 50 m visibility,
roughly 35 to 65, close to the 50 km/h a German driver is allowed.

So the car can drive, but it has to slow down like a careful human. On top of that, no datasheet covers a
sensor blocked by snow or ice, rare events need billions of test kilometres, and the law approves only
defined operating domains."

## 6. Summary (30 s)

"To sum up: **20 sensors, 11,000 dollars, two modalities on every bearing in clear weather and at night, and
84 km/h in dense fog.** Our answer: Level 4 in city and highway inside a speed envelope, yes. True Level 5,
anywhere and in any weather, is not possible today. The next gaps to close are an ultrasonic ring for the
near field, a rear thermal camera, and longer-range imaging radar for fog. Thank you."

## Suggested split (team of 3)

| Speaker | Slides | Time |
|---|---|---|
| A | title, 1, 2 | 1:45 |
| B | 3, 4 | 1:40 |
| C | 5, 6 | 1:20 |
