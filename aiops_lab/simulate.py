"""Generate synthetic per-minute metrics and inject known faults."""
from dataclasses import dataclass, field
import numpy as np

from .topology import NODES

MINUTES = 120
START_EPOCH = 1795051200  # 2026-11-19 08:00:00 WIB
BASE = {
    "core": {"cpu": 45, "latency": 4, "loss": 0.05, "traffic": 8000},
    "aggregation": {"cpu": 35, "latency": 8, "loss": 0.1, "traffic": 2500},
    "access": {"cpu": 25, "latency": 12, "loss": 0.2, "traffic": 600},
}


@dataclass
class Scenario:
    name: str
    start: int
    end: int
    truth: list = field(default_factory=list)  # (device, metric) pairs that should alarm


SCENARIOS = [
    Scenario("Core CPU overload", 40, 55, [("CORE-JKT-01", "cpu"), ("CORE-JKT-01", "latency")]),
    Scenario("Fiber cut on AGG-BDG-02 uplink", 80, 120,
             [("AGG-BDG-02", "loss"), ("AGG-BDG-02", "latency")]
             + [(d, m) for d in ("ACC-BDG-04", "ACC-BDG-05", "ACC-BDG-06") for m in ("loss", "latency", "traffic")]),
    Scenario("Traffic surge at ACC-BDG-02", 95, 108, [("ACC-BDG-02", "traffic"), ("ACC-BDG-02", "cpu")]),
]


def simulate(seed: int = 20261119, scenarios=SCENARIOS) -> dict:
    """Return {device: {metric: np.ndarray}} with true values in canonical units."""
    rng = np.random.default_rng(seed)
    t = np.arange(MINUTES)
    wave = 1 + 0.08 * np.sin((t + 20) / 120 * np.pi * 1.4)
    names = {s.name for s in scenarios}
    data = {}
    for dev, node in NODES.items():
        b = BASE[node["layer"]]
        cpu = b["cpu"] * wave + rng.normal(0, 1.6, MINUTES)
        lat = b["latency"] * (1 + rng.normal(0, 0.04, MINUTES))
        loss = np.clip(b["loss"] + rng.normal(0, 0.03, MINUTES), 0, None)
        tr = b["traffic"] * wave * (1 + rng.normal(0, 0.015, MINUTES))
        for s in SCENARIOS:
            if s.name not in names:
                continue
            w = slice(s.start, s.end)
            n = s.end - s.start
            if s.name.startswith("Core") and dev == "CORE-JKT-01":
                cpu[w] = 92 + rng.random(n) * 5
                lat[w] = b["latency"] * 1.7
            if s.name.startswith("Fiber"):
                if dev == "AGG-BDG-02":
                    loss[w] = 28 + rng.random(n) * 10
                    lat[w] = b["latency"] * 4
                if node["parent"] == "AGG-BDG-02":
                    loss[w] = 20 + rng.random(n) * 10
                    lat[w] = b["latency"] * 3
                    tr[w] = tr[w] * 0.4
            if s.name.startswith("Traffic") and dev == "ACC-BDG-02":
                tr[w] = tr[w] * 3.2
                cpu[w] = cpu[w] + 30
        data[dev] = {"cpu": cpu, "latency": lat, "loss": loss, "traffic": tr}
    return data
