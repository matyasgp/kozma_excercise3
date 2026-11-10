# kozma_excercise3

3DSSF (Kozma) Exercise 3: lidar performance, statistical modelling.

Does the **InnovizTwo** fulfil the Emergency Brake Assist requirements (250 m detection range, at least 5 returns per object)?

**Result:** yes for cars and trucks; no for dark (10 %) pedestrians and motorcycles, which reach P(at least 5 returns) >= 99 % only up to about 235 m; small debris (0.5 m) only up to about 140 m.

**Weather** (visibility V → α = 3.912/V): rain (5 km) cuts the dark pedestrian's 99 % range to 215 m, fog (1 km) to 167 m; in fog even a car reaches 99 % only up to 221 m. Weighted with a rough Hungarian weather mix (88 % clear, 8 % rain, 4 % fog, our estimate), a dark pedestrian at 250 m is detected in 91 % of frames.

- `lidar_eba.py`: the model (beam geometry, per-beam detection probability, binomial P(K >= 5)). Run `python lidar_eba.py`; needs numpy and matplotlib.
- `lidar_eba.png`: the results plot produced by the script (P(K ≥ 5) vs distance, clear / rain / fog).
- `figures.py`: makes the slide visuals `fig_beams_250m.png`, `fig_k_distribution.png`, `fig_ranges.png` (uses the model from `lidar_eba.py`).
- `note.md`: status for the team, open fixes, Q&A prep.
- `slides/presentation.pdf`: beamer draft of the 5-minute pitch (the final version will be in Google Slides).
- `slides/backup_slides.pdf`: 10 backup slides (B1–B10) for the Q&A.
- `docs/speaker_notes.md`: what to say on each slide, background, likely questions.
- `docs/solution_explained.md`: the whole solution explained step by step, in the order of the final deck.
- `docs/qa_final_deck.md`: Q&A guide for the team's final 6-slide deck (InnovizTwo_EBA.pptx): slide-by-slide questions, answers and traps.
- `docs/full_report.md`: the complete record: how the work went, every decision, the full model with worked examples, all results, checks, assumptions and open issues.
- `docs/qa_cheatsheet.md`: one page to hold during the Q&A (numbers, top 10 questions, traps).
- `docs/qa_guide.md`: answers to every question we expect, with pointers to the backup slides.
- `docs/derivation.pdf`: short math derivation of the model, with the reasons for every parameter.
- `docs/code_explained.md`: walk-through of the code, list of assumptions, how robust the results are, alternative approaches.
- `sources/` (local only, not in the repo): the course deck and the datasheet PDF.

The figures (`*.png`) stay next to the scripts, which write them there; the slides read them from `..`. Build a PDF with `latexmk -pdf <file>.tex` inside `slides/` or `docs/`; LaTeX build files go to a `build/` folder (see `latexmkrc`), which is ignored.

## InnovizTwo specs used

Source: **InnovizTwo GMSL Series Production Datasheet v3.1** (© Innoviz Technologies, 2024), [PDF](https://levelfivesupplies.com/wp-content/uploads/2023/08/InnovizTwo-GMSL-Series-Production-Datasheet_v3.1-1.pdf). Values for the **Condor** configuration (front-facing consumer vehicles), region of interest.

| Value | Used | Datasheet |
| --- | --- | --- |
| Angular resolution (ROI, 30° x 9.6°) | 0.1° x 0.05° | "0.1°x0.05° in ROI" |
| Range at 10 % reflectivity (ROI) | 210 m | "0.1°x0.05°: 210m @ 10% Reflectivity" |
| Detection probability at that range | 90 % per beam | note 4: "True Positives = 90% per pixel and False Positives = 1% per pixel", 100 klx sunlight, 10 % Lambertian target |
| Max range | 300 m | "Detection Range 0.3m-300m" |
| Frame rate | 20 FPS | Condor configuration |

The model extrapolates from the 210 m datasheet point to 250 m with the ρ/R² law. False positives are not modelled. The datasheet values are for clear weather; rain and fog are added by the model.

Earlier draft used the Hesai AT512 (git history); it was dropped because no official datasheet is published.
