"""Group alarms into incidents by time window and topology, then pick a root cause."""
from collections import Counter

from .topology import depth, related

PRIORITY = {"loss": 0, "traffic": 1, "cpu": 2, "latency": 3}


def correlate(alarms, window_min=10):
    """alarms: list of dicts {t, device, metric, value, z}. Returns list of incidents."""
    alarms = sorted(alarms, key=lambda a: (a["t"], depth(a["device"])))
    incidents = []
    for a in alarms:
        inc = next((i for i in incidents
                    if a["t"] - i["last"] <= window_min and any(related(d, a["device"]) for d in i["devices"])), None)
        if inc is None:
            inc = {"alarms": [], "devices": [], "first": a["t"], "last": a["t"]}
            incidents.append(inc)
        inc["alarms"].append(a)
        inc["last"] = max(inc["last"], a["t"])
        if a["device"] not in inc["devices"]:
            inc["devices"].append(a["device"])

    for n, inc in enumerate(incidents, 1):
        first_seen = {}
        for a in inc["alarms"]:
            first_seen.setdefault(a["device"], a["t"])
        inc["id"] = f"INC-{n:04d}"
        inc["root"] = sorted(inc["devices"], key=lambda d: (depth(d), first_seen[d]))[0]
        counts = Counter(a["metric"] for a in inc["alarms"] if a["device"] == inc["root"])
        inc["main_metric"] = sorted(counts.items(), key=lambda kv: (-kv[1], PRIORITY[kv[0]]))[0][0]
        inc["impacted"] = [d for d in inc["devices"] if d != inc["root"]]
    return incidents
