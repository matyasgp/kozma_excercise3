# kozma_excercise3

3DSSF (Kozma) Exercise 3: lidar performance, statistical modelling.

Does the **Hesai AT512** fulfil the Emergency Brake Assist requirements (250 m detection range, at least 5 returns per object)?

- `lidar_eba.py`: the model (beam geometry, per-beam detection probability, binomial P(K >= 5)). Run `python lidar_eba.py`; needs numpy and matplotlib.
- `lidar_eba.png`: the results plot produced by the script.
- `speaker_notes.md`: what to say on each slide, background, likely questions.
- `presentation.tex` / `presentation.pdf`: beamer draft of the 5-minute pitch (the final version will be in Google Slides).

## AT512 specs used, and where they come from
No official datasheet PDF found yet; Hesai does not publish one openly.

| Value | Used | Source / status |
| --- | --- | --- |
| Range | 300 m @ 10 % reflectivity, > 400 m max | [Hesai press release, Jan 2024](https://www.hesaitech.com/hesai-announces-two-revolutionary-new-adas-lidar-products-and-completion-of-its-state-of-the-art-rd-center-for-manufacturing/) |
| Resolution | 2400 x 512 points, 120° x 25.6° FoV | same press release |
| Point rate | 12.3 M pts/s | same press release |
| Angular resolution | 0.05° x 0.05° | Hesai web listing + [Gasgoo](https://autonews.gasgoo.com/articles/news/hesai-technology-launches-at512-high-performance-lidar-product-70030518); consistent with 120°/2400 |
| Frame rate | 10 Hz | **derived**: 12.288 M / (2400 x 512) = 10 |
| Detection probability behind the 300 m figure | 90 % | **assumed**, not published |

One hesaitech.com listing shows 0.1° x 0.1°, 250 m @ 10 % and 3.7 M pts/s for the AT512 (an older spec?). Not used. Ask Hesai or the lecturer if it matters.
