"""Anomaly detection: rolling z-score baseline, plus Isolation Forest for comparison."""
import numpy as np
from sklearn.ensemble import IsolationForest

FLOOR = {"cpu": 1.5, "latency": 0.4, "loss": 0.08, "traffic": None}  # minimum std to avoid noise alarms
TWO_SIDED = {"traffic"}
WINDOW = 30


def zscore_detect(series, metric, k=3.0, window=WINDOW):
    """Return z-score per minute (0 when normal). Anomalous points never enter the baseline."""
    z_out = np.zeros(len(series))
    normal = []
    for t, x in enumerate(series):
        if len(normal) >= window:
            w = np.array(normal[-window:])
            mean = w.mean()
            std = max(w.std(), FLOOR[metric] if FLOOR[metric] is not None else mean * 0.02)
            z = (x - mean) / std
            hit = abs(z) > k if metric in TWO_SIDED else z > k
            if hit:
                z_out[t] = z
                continue
        normal.append(x)
    return z_out


def isolation_forest_detect(device_metrics, contamination=0.08, seed=0):
    """Multivariate detector on one device: cpu, latency, loss, traffic together.

    Returns a boolean array per minute. Used only as a comparison to the z-score baseline.
    """
    X = np.column_stack([device_metrics[m] for m in ("cpu", "latency", "loss", "traffic")])
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-9)
    model = IsolationForest(contamination=contamination, random_state=seed)
    return model.fit_predict(X) == -1
