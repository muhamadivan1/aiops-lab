"""Network topology: one core, two aggregation, six access devices."""

NODES = {
    "CORE-JKT-01": {"layer": "core", "vendor": "A", "parent": None},
    "AGG-BDG-01": {"layer": "aggregation", "vendor": "B", "parent": "CORE-JKT-01"},
    "AGG-BDG-02": {"layer": "aggregation", "vendor": "B", "parent": "CORE-JKT-01"},
    "ACC-BDG-01": {"layer": "access", "vendor": "C", "parent": "AGG-BDG-01"},
    "ACC-BDG-02": {"layer": "access", "vendor": "C", "parent": "AGG-BDG-01"},
    "ACC-BDG-03": {"layer": "access", "vendor": "C", "parent": "AGG-BDG-01"},
    "ACC-BDG-04": {"layer": "access", "vendor": "C", "parent": "AGG-BDG-02"},
    "ACC-BDG-05": {"layer": "access", "vendor": "C", "parent": "AGG-BDG-02"},
    "ACC-BDG-06": {"layer": "access", "vendor": "C", "parent": "AGG-BDG-02"},
}


def depth(device: str) -> int:
    d, node = 0, NODES[device]
    while node["parent"]:
        d += 1
        node = NODES[node["parent"]]
    return d


def is_ancestor(a: str, b: str) -> bool:
    """True if device a is upstream of device b."""
    node = NODES[b]
    while node["parent"]:
        if node["parent"] == a:
            return True
        node = NODES[node["parent"]]
    return False


def related(a: str, b: str) -> bool:
    return a == b or is_ancestor(a, b) or is_ancestor(b, a)
