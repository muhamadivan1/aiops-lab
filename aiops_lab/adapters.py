"""Vendor encoders (fake raw telemetry) and adapters into one canonical record.

Canonical record: {ts, device, metric, value, unit}
Same adapter + canonical data model pattern as my thesis (Flowbeat).
"""
import json
import re
from datetime import datetime, timedelta, timezone

from .simulate import START_EPOCH

WIB = timezone(timedelta(hours=7))
UNITS = {"cpu": "%", "latency": "ms", "loss": "%", "traffic": "Mbps"}


# ---------- encoders: what each vendor would send ----------
def encode_a(device, v, minute):
    """Vendor A: JSON, fractions, microseconds, bits per second."""
    return json.dumps({
        "hostname": device,
        "timestamp": START_EPOCH + minute * 60,
        "cpu_util": round(v["cpu"] / 100, 4),
        "rtt_us": round(v["latency"] * 1000),
        "pkt_loss": round(v["loss"] / 100, 5),
        "tx_bps": round(v["traffic"] * 1e6),
    })


def encode_b(device, v, minute):
    """Vendor B: pipe separated key=value line with units in the value."""
    ts = datetime.fromtimestamp(START_EPOCH + minute * 60, WIB).isoformat()
    return (f"{ts}|{device}|CPU={v['cpu']:.1f}%|LAT={v['latency']:.2f}ms|"
            f"LOSS={v['loss']:.2f}%|TRAF={v['traffic'] / 1000:.3f}Gbps")


def encode_c(device, v, minute):
    """Vendor C: SNMP-style lines, scaled integers."""
    ep = START_EPOCH + minute * 60
    return "\n".join([
        f"{ep} 1.3.6.1.4.1.99999.1.1.{device} = Gauge32: {round(v['cpu'])}",
        f"{ep} 1.3.6.1.4.1.99999.1.2.{device} = Gauge32: {round(v['latency'] * 10)}",
        f"{ep} 1.3.6.1.4.1.99999.1.3.{device} = Gauge32: {round(v['loss'] * 100)}",
        f"{ep} 1.3.6.1.4.1.99999.1.4.{device} = Counter64: {round(v['traffic'] * 1000)}",
    ])


# ---------- adapters: raw -> canonical ----------
def _rec(ts, device, metric, value):
    return {"ts": ts, "device": device, "metric": metric, "value": float(value), "unit": UNITS[metric]}


def adapt_a(raw):
    o = json.loads(raw)
    d, ts = o["hostname"], o["timestamp"]
    return [_rec(ts, d, "cpu", o["cpu_util"] * 100), _rec(ts, d, "latency", o["rtt_us"] / 1000),
            _rec(ts, d, "loss", o["pkt_loss"] * 100), _rec(ts, d, "traffic", o["tx_bps"] / 1e6)]


def adapt_b(raw):
    parts = raw.split("|")
    ts = int(datetime.fromisoformat(parts[0]).timestamp())
    kv = dict(p.split("=") for p in parts[2:])
    num = lambda s: float(re.match(r"[-\d.]+", s).group())
    return [_rec(ts, parts[1], "cpu", num(kv["CPU"])), _rec(ts, parts[1], "latency", num(kv["LAT"])),
            _rec(ts, parts[1], "loss", num(kv["LOSS"])), _rec(ts, parts[1], "traffic", num(kv["TRAF"]) * 1000)]


_OID = {"1": ("cpu", 1), "2": ("latency", 10), "3": ("loss", 100), "4": ("traffic", 1000)}
_LINE = re.compile(r"^(\d+) 1\.3\.6\.1\.4\.1\.99999\.1\.(\d)\.(\S+) = \w+: (\d+)$")


def adapt_c(raw):
    out = []
    for line in raw.splitlines():
        m = _LINE.match(line)
        if not m:
            raise ValueError(f"Unrecognized vendor C line: {line!r}")
        metric, scale = _OID[m.group(2)]
        out.append(_rec(int(m.group(1)), m.group(3), metric, int(m.group(4)) / scale))
    return out


ENCODERS = {"A": encode_a, "B": encode_b, "C": encode_c}
ADAPTERS = {"A": adapt_a, "B": adapt_b, "C": adapt_c}
