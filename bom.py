"""Sensor bill of materials (Exercise 4, step 5): count, unit price and total per model from sensors.yaml.

Prices are the listed price where the source gives one (price_usd) and otherwise our rough estimate
(price_usd_est, marked "est."). There is no cost target; the total is reported. Compute, wiring,
cleaning and calibration are not included.
Run `python bom.py`: prints the table and writes bom.csv.
"""
from collections import Counter

from model import load_suite


def bom(path="sensors.yaml"):
    models, mounts = load_suite(path)
    n = Counter(model for _, model, *_ in mounts)
    rows = []
    for key, cnt in n.items():
        m = models[key]
        listed = "price_usd" in m
        unit = m["price_usd"] if listed else m["price_usd_est"]
        rows.append(dict(model=key, name=m["name"], modality=m["modality"], count=cnt, unit=unit,
                         listed=listed, subtotal=cnt * unit))
    return rows


if __name__ == "__main__":
    rows = bom()
    with open("bom.csv", "w", encoding="utf-8") as f:
        f.write("modality,model,count,unit_usd,price_source,subtotal_usd\n")
        for r in rows:
            f.write(f"{r['modality']},{r['name']},{r['count']},{r['unit']},{'listed' if r['listed'] else 'estimate'},"
                    f"{r['subtotal']}\n")
    for r in rows:
        print(f"{r['modality']:9s}{r['name'][:62]:64s}{r['count']:3d} x {r['unit']:6,d} "
              f"{'' if r['listed'] else 'est.':5s}= {r['subtotal']:7,d} USD")
    by_mod = Counter()
    for r in rows:
        by_mod[r["modality"]] += r["subtotal"]
    total = sum(by_mod.values())
    print("per modality: " + ", ".join(f"{k} {v:,d}" for k, v in by_mod.items()))
    print(f"total: {sum(r['count'] for r in rows)} sensors, {total:,d} USD")
