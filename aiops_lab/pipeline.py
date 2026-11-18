"""End-to-end pipeline: simulate -> encode -> normalize -> detect -> correlate -> evaluate."""
import numpy as np

from .adapters import ADAPTERS, ENCODERS
from .correlate import correlate
from .detect import WINDOW, isolation_forest_detect, zscore_detect
from .simulate import MINUTES, SCENARIOS, START_EPOCH, simulate
from .topology import NODES

METRICS = ("cpu", "latency", "loss", "traffic")
RUNBOOK = {
    "loss": ["Check optical power and interface errors on the root device uplink",
             "Verify fiber continuity with the field team",
             "Fail over to the backup path if available"],
    "latency": ["Check link utilization and queue drops", "Look for recent routing changes"],
    "cpu": ["Identify top control plane processes", "Check for route flapping or protocol storms",
            "Apply control plane protection or rate limits"],
    "traffic": ["Confirm local event or attack", "Check top talkers", "Apply QoS or temporary capacity"],
}


def normalize(true_values):
    """Send every device-minute through its vendor encoder and adapter. Returns canonical arrays."""
    canon = {d: {m: np.zeros(MINUTES) for m in METRICS} for d in NODES}
    records = 0
    for dev, node in NODES.items():
        for t in range(MINUTES):
            v = {m: float(true_values[dev][m][t]) for m in METRICS}
            raw = ENCODERS[node["vendor"]](dev, v, t)
            for r in ADAPTERS[node["vendor"]](raw):
                assert r["ts"] == START_EPOCH + t * 60 and r["device"] == dev
                canon[dev][r["metric"]][t] = r["value"]
                records += 1
    return canon, records


def run(seed=20261119, k=3.0, scenarios=SCENARIOS):
    canon, records = normalize(simulate(seed, scenarios))
    alarms = []
    for dev in NODES:
        for m in METRICS:
            z = zscore_detect(canon[dev][m], m, k)
            alarms += [{"t": int(t), "device": dev, "metric": m, "value": float(canon[dev][m][t]), "z": float(z[t])}
                       for t in np.nonzero(z)[0]]
    incidents = correlate(alarms)

    truth = {(d, m, t) for s in scenarios for d, m in s.truth for t in range(max(s.start, WINDOW), s.end)}
    flagged = {(a["device"], a["metric"], a["t"]) for a in alarms}
    tp = len(flagged & truth)

    # Isolation Forest comparison at device-minute level
    dev_truth = {(d, t) for s in scenarios for d, _ in s.truth for t in range(s.start, s.end)}
    if_flag = {(d, int(t)) for d in NODES for t in np.nonzero(isolation_forest_detect(canon[d]))[0]}
    if_tp = len(if_flag & dev_truth)

    return {
        "records": records,
        "alarms": alarms,
        "incidents": incidents,
        "zscore": {"precision": tp / len(flagged) if flagged else None,
                   "recall": tp / len(truth) if truth else None},
        "isolation_forest": {"precision": if_tp / len(if_flag) if if_flag else None,
                             "recall": if_tp / len(dev_truth) if dev_truth else None},
    }
