# AIOps Lab

A small, explainable AIOps pipeline on synthetic telecom network data, written in Python.

It follows the path an operations team cares about: **collect** telemetry from three vendors in three formats, **normalize** it into one canonical model, **detect** anomalies, **correlate** hundreds of alarms into a few incidents, find the **root cause**, and suggest a **runbook**.

> Personal learning project. All data is synthetic. Built to understand the AIOps workflow end to end, not to claim production performance.

## Example output

```
$ python run.py
Canonical records : 4320
Raw alarms        : 500
Incidents         : 3  (compression 99.4%)
Z-score           : precision 99%, recall 100%
Isolation Forest  : precision 56%, recall 27%  (device-minute level, for comparison)

INC-0001  08:40-09:03  root=CORE-JKT-01  metric=cpu      alarms=33   impacted=AGG-BDG-01, ACC-BDG-01, ACC-BDG-06
INC-0002  09:20-09:59  root=AGG-BDG-02  metric=loss     alarms=441  impacted=ACC-BDG-04, ACC-BDG-05, ACC-BDG-06
INC-0003  09:35-09:47  root=ACC-BDG-02  metric=traffic  alarms=26   impacted=-
```

## How it works

| Step | Module | What it does |
|---|---|---|
| Simulate | `simulate.py` | 9 devices (core, aggregation, access), 4 metrics, 120 minutes, three injected faults with known ground truth |
| Collect | `adapters.py` | Vendor A sends JSON (fractions, µs, bps), vendor B a key=value line, vendor C SNMP-style integers |
| Normalize | `adapters.py` | One adapter per vendor converts everything into `{ts, device, metric, value, unit}` |
| Detect | `detect.py` | Rolling 30-minute z-score. Anomalous points never enter the baseline, so a long outage does not become "normal" |
| Correlate | `correlate.py` | Alarms within 10 minutes on the same topology branch form one incident. Root cause is the most upstream device that alarmed first |
| Evaluate | `pipeline.py` | Precision and recall against the injected faults, plus an Isolation Forest comparison |

The adapter + canonical model pattern comes from my master's thesis, **Flowbeat**, which integrates data from different medical IoT devices for remote patient monitoring.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                    # default k = 3
python run.py --k 2              # more sensitive: recall stays, precision drops
python -m unittest discover tests
```

## What I learned

- **Lower threshold is not always better.** With `k = 2`, precision drops to about 53% and noise alarms merge unrelated faults into one big incident.
- **Simple can beat fancy.** Untuned Isolation Forest scored lower than the z-score baseline here, because the faults are single-metric spikes. Always compare against a simple baseline first.
- **Topology rules have side effects.** Because the core router is upstream of everything, the core CPU incident also absorbs a few unrelated noise alarms during its window. A real system needs service paths, not only a parent-child tree.

## Next steps

- Seasonality-aware baselines or a forecasting model for daily traffic patterns
- Tuned multivariate detection (Isolation Forest, autoencoder) with proper validation
- Topology from a CMDB or network controller
- LLM incident summary with retrieval over runbooks (RAG)

## Interactive version

A browser version of the same pipeline with charts and a topology view is part of my portfolio at [muhamadivan1.github.io](https://muhamadivan1.github.io).

## License

[MIT](LICENSE) © 2026 Muhamad Ivan Fadilah
