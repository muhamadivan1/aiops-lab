"""Run the AIOps Lab pipeline and print a report.

Usage: python run.py [--k 3.0] [--seed 20261119]
"""
import argparse
import json
from pathlib import Path

from aiops_lab.pipeline import RUNBOOK, run


def hhmm(t):
    m = 480 + t
    return f"{m // 60:02d}:{m % 60:02d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--k", type=float, default=3.0, help="z-score threshold")
    ap.add_argument("--seed", type=int, default=20261119)
    args = ap.parse_args()

    res = run(seed=args.seed, k=args.k)
    n_alarm, n_inc = len(res["alarms"]), len(res["incidents"])
    pct = lambda x: "n/a" if x is None else f"{x:.0%}"

    print(f"Canonical records : {res['records']}")
    print(f"Raw alarms        : {n_alarm}")
    print(f"Incidents         : {n_inc}  (compression {1 - n_inc / n_alarm:.1%})" if n_alarm else "Incidents: 0")
    print(f"Z-score           : precision {pct(res['zscore']['precision'])}, recall {pct(res['zscore']['recall'])}")
    print(f"Isolation Forest  : precision {pct(res['isolation_forest']['precision'])}, "
          f"recall {pct(res['isolation_forest']['recall'])}  (device-minute level, for comparison)")
    print()
    for inc in res["incidents"]:
        print(f"{inc['id']}  {hhmm(inc['first'])}-{hhmm(inc['last'])}  root={inc['root']}  "
              f"metric={inc['main_metric']}  alarms={len(inc['alarms'])}  impacted={', '.join(inc['impacted']) or '-'}")
        for step in RUNBOOK[inc["main_metric"]]:
            print(f"    - {step}")

    out = Path("reports")
    out.mkdir(exist_ok=True)
    slim = [{k: v for k, v in i.items() if k != "alarms"} | {"alarm_count": len(i["alarms"])} for i in res["incidents"]]
    (out / "incidents.json").write_text(json.dumps(slim, indent=2))
    print(f"\nSaved {out / 'incidents.json'}")


if __name__ == "__main__":
    main()
