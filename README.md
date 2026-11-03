# kozma_excercise3

3DSSF (Kozma) Exercise 3: lidar performance, statistical modelling.

Does the **Hesai AT512** fulfil the Emergency Brake Assist requirements (250 m detection range, at least 5 returns per object)?

- `lidar_eba.py`: the model (beam geometry, per-beam detection probability, binomial P(K >= 5)). Run `python lidar_eba.py`; needs numpy and matplotlib.
- `lidar_eba.png`: the results plot produced by the script.
- `presentation.tex` / `presentation.pdf`: beamer draft of the 5-minute pitch (the final version will be in Google Slides).
