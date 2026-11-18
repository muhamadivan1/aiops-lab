import unittest

import numpy as np

from aiops_lab.adapters import ADAPTERS, ENCODERS
from aiops_lab.correlate import correlate
from aiops_lab.detect import zscore_detect
from aiops_lab.pipeline import run
from aiops_lab.simulate import SCENARIOS
from aiops_lab.topology import related


class TestAdapters(unittest.TestCase):
    v = {"cpu": 47.3, "latency": 8.25, "loss": 0.12, "traffic": 2512.5}

    def test_every_vendor_roundtrips_to_canonical(self):
        for vendor in "ABC":
            recs = {r["metric"]: r for r in ADAPTERS[vendor](ENCODERS[vendor]("AGG-BDG-01", self.v, 10))}
            self.assertEqual(set(recs), {"cpu", "latency", "loss", "traffic"})
            for m, val in self.v.items():
                self.assertAlmostEqual(recs[m]["value"], val, delta=max(0.6, val * 0.002), msg=f"{vendor} {m}")
            self.assertEqual(recs["traffic"]["unit"], "Mbps")

    def test_same_timestamp_across_vendors(self):
        ts = {ADAPTERS[x](ENCODERS[x]("CORE-JKT-01", self.v, 5))[0]["ts"] for x in "ABC"}
        self.assertEqual(len(ts), 1)

    def test_bad_vendor_c_line_raises(self):
        with self.assertRaises(ValueError):
            ADAPTERS["C"]("garbage")


class TestDetect(unittest.TestCase):
    def test_flat_series_has_no_anomaly(self):
        s = 50 + np.random.default_rng(1).normal(0, 1, 120)
        self.assertEqual(np.count_nonzero(zscore_detect(s, "cpu")), 0)

    def test_step_change_is_detected_and_stays_detected(self):
        s = np.r_[np.full(60, 0.1), np.full(60, 30.0)]
        z = zscore_detect(s, "loss")
        self.assertTrue(all(z[60:] > 0), "outage must not become the new baseline")


class TestCorrelate(unittest.TestCase):
    def test_topology(self):
        self.assertTrue(related("AGG-BDG-02", "ACC-BDG-05"))
        self.assertFalse(related("AGG-BDG-01", "ACC-BDG-05"))

    def test_downstream_alarms_group_under_upstream_root(self):
        alarms = [{"t": 80, "device": "ACC-BDG-04", "metric": "loss", "value": 20, "z": 9},
                  {"t": 80, "device": "AGG-BDG-02", "metric": "loss", "value": 30, "z": 9},
                  {"t": 81, "device": "ACC-BDG-06", "metric": "loss", "value": 22, "z": 9}]
        inc = correlate(alarms)
        self.assertEqual(len(inc), 1)
        self.assertEqual(inc[0]["root"], "AGG-BDG-02")


class TestPipeline(unittest.TestCase):
    def test_default_run_finds_three_incidents_with_correct_roots(self):
        res = run()
        roots = [i["root"] for i in res["incidents"]]
        self.assertEqual(roots, ["CORE-JKT-01", "AGG-BDG-02", "ACC-BDG-02"])
        self.assertGreater(res["zscore"]["recall"], 0.9)

    def test_no_faults_false_alarm_rate_below_half_percent(self):
        res = run(scenarios=[])
        self.assertLess(len(res["alarms"]) / res["records"], 0.005)

    def test_lower_k_trades_precision_for_recall(self):
        hi, lo = run(k=4.0), run(k=2.0)
        self.assertGreaterEqual(lo["zscore"]["recall"], hi["zscore"]["recall"])
        self.assertLessEqual(lo["zscore"]["precision"], hi["zscore"]["precision"])


if __name__ == "__main__":
    unittest.main()
