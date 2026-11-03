# Note for the team (status 2026-11-03)

## Where we are
- **Model is done** (`lidar_eba.py`, `figures.py`): InnovizTwo, binomial P(K ≥ 5), random grid offset, clear / rain / fog plus a Hungary-weighted result. Run `python lidar_eba.py` and `python figures.py` to regenerate the table and all figures.
- **Beamer draft is done** (`slides/presentation.pdf`, 5 slides; Q&A backup: `slides/backup_slides.pdf`). The final pitch goes into Google Slides: copy the figures (`fig_beams_250m.png`, `fig_k_distribution.png`, `lidar_eba.png`, `fig_ranges.png`) and the text.
- **Speaker notes** (`docs/speaker_notes.md`; full Q&A answers in `docs/qa_guide.md`): what to say per slide, about 5 minutes in total, plus likely questions.
- **Background:** `docs/derivation.pdf` (the math, plus the reason for every parameter) and `docs/code_explained.md` (code walk-through, assumptions, sensitivity).
- **Datasheet:** [InnovizTwo GMSL Series Production Datasheet v3.1](https://levelfivesupplies.com/wp-content/uploads/2023/08/InnovizTwo-GMSL-Series-Production-Datasheet_v3.1-1.pdf). The key line is footnote 4: "True Positives = 90% per pixel" at 210 m, 10 % reflectivity, 100 klx sunlight.

## Main result (10 % reflectivity)
| | P(K ≥ 5) at 250 m: clear / rain / fog | Weighted (88/8/4 %) | 99 % range: clear / rain / fog |
|---|---|---|---|
| car | 100 / 100 / 71 % | 98.8 % | ≥ 300 / 296 / 221 m |
| pedestrian | 96.2 / 80 / 5 % | 91.3 % | 235 / 215 / 167 m |
| motorcycle | 95.7 / 90 / 9 % | 91.8 % | 237 / 232 / 184 m |

The truck passes in all three conditions; the tyre fails in all three (≤ 143 m). Key message: **the average passes, the probability fails** (dark pedestrian: 7.6 returns on average, but only 96 % of frames have ≥ 5).

## Still to fix (wording only, no code changes)
1. **Slide 4 table:** car weighted 98.8 % is below 99 % but not shown in red. Mark it, or say that the verdict applies per weather condition.
2. **Slide 5 title** "EBA met for vehicles" is true only in clear weather. Suggested: "Clear weather: EBA met for vehicles, not for dark road users".
3. **Slide 3 formula** has no weather factor. Add `× e^(−2αR)` or one line on slide 4.
4. **Title slide:** "Team: names TBD" → our names.
5. **`docs/code_explained.md` line 88** still mentions the "right-hand plot", which no longer exists.

## Be ready for these questions
- **"250 m is beyond the 210 m datasheet range?"** Yes: we calibrate at 210 m and extrapolate with ρ/R². Another common curve shape (speckle model) gives 248 m instead of 235 m for the pedestrian, so ours is the cautious one.
- **"Last year's InnovizTwo team said it passes."** They used the 0.05° × 0.05° maximum resolution (footnote 1: possible, but it costs frame rate, field of view or range) and judged at 200 m. We use the forward configuration's region of interest (0.1° × 0.05°) and the task's 250 m.
- **"Where do the weather shares come from?"** Our estimate, not HungaroMet statistics. The method doesn't depend on them: change `WEATHER` in `lidar_eba.py` and rerun.
- **"Why 99 %?"** Our choice. 95 % → 253 m, 99.9 % → 219 m for the pedestrian.
- **"Returns" means points on the object**, not the multiple echoes per pulse from lecture 3, slide 16.

## Known limitations (stated on slide 5 / in the docs)
- Objects are modelled as flat rectangles.
- Beams are treated as points and as independent of each other.
- False positives are ignored.
- The verdict judges a single frame.
- The weather formula (Koschmieder) is for visible light; spray and a wet sensor window are ignored.
- The 50 % reflectivity results are probably optimistic. The datasheet's side-region numbers don't follow ρ/R².

## Rules for the repo
- Commit and push after every change so everyone can follow.
- Keep `sources/` out of the repo: the course `.pptx` (100 MB, other students' names) and the datasheet PDF (Innoviz's copyright). Both are in `.gitignore`.
