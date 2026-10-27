"""Metric names: prefixed, declared, and translated from the old names."""

import importlib.util
import json
import pathlib
import sys

import pytest

from cmk.agent_based.v2 import Metric
from cmk.graphing.v1 import graphs, metrics, perfometers, translations

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "local/lib/python3/cmk_addons/plugins/oposs_smart_error"

OPERATIONS = ("read", "write", "verify")
COUNTERS = (
    "errors_corrected_by_eccfast",
    "errors_corrected_by_eccdelayed",
    "errors_corrected_by_rereads_rewrites",
    "correction_algorithm_invocations",
    "bytes_processed",
    "total_uncorrected_errors",
)
RATES = (
    "errors_corrected_by_eccfast_per_tb",
    "errors_corrected_by_eccdelayed_per_tb",
    "errors_corrected_by_rereads_rewrites_per_tb",
    "correction_algorithm_invocations_per_tb",
)
# Metric names emitted up to 1.0.5, before they carried the plugin prefix.
OLD_NAMES = [f"{op}_{name}" for op in OPERATIONS for name in COUNTERS + RATES]


def _load(path):
    name = "test_graphing_" + path.stem + "_" + path.parent.name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def check():
    return _load(PLUGIN / "agent_based/oposs_smart_error.py")


@pytest.fixture(scope="module")
def graphing_objects():
    objects = []
    for path in sorted((PLUGIN / "graphing").glob("*.py")):
        objects.extend(vars(_load(path)).values())
    return objects


@pytest.fixture(scope="module")
def declared(graphing_objects):
    return {o.name for o in graphing_objects if isinstance(o, metrics.Metric)}


def _counters(value):
    return {
        "errors_corrected_by_eccfast": value,
        "errors_corrected_by_eccdelayed": value,
        "errors_corrected_by_rereads_rewrites": value,
        "total_errors_corrected": 3 * value,
        "correction_algorithm_invocations": value,
        "gigabytes_processed": "1024.000",
        "total_uncorrected_errors": value,
    }


@pytest.fixture(scope="module")
def emitted(check):
    """Every metric the error check yields when every counter and level is set."""
    data = {
        "device": "/dev/sdc",
        "serial": "S1",
        "grown_defects": 1,
        "error_counters": {op: _counters(5) for op in OPERATIONS},
    }
    params = {
        f"{op}_{kind}": ("fixed", (1, 10))
        for op in OPERATIONS
        for kind in (
            "uncorrected_errors_abs",
            "eccfast_errors_abs",
            "eccdelayed_errors_abs",
            "rereads_rewrites_errors_abs",
            "algorithm_invocations_abs",
        )
    }
    params["grown_defects_abs"] = ("fixed", (1, 10))
    section = check.parse_oposs_smart_error([["/dev/sdc", json.dumps(data)]])
    out = check.check_oposs_smart_error("/dev/sdc (S1)", params, section)
    return [m.name for m in out if isinstance(m, Metric)]


def test_every_emitted_metric_is_prefixed(emitted):
    assert emitted
    assert [n for n in emitted if not n.startswith("oposs_smart_error_")] == []


def test_every_emitted_metric_is_declared(emitted, declared):
    assert sorted(set(emitted) - declared) == []


def test_each_metric_is_emitted_once(emitted):
    assert len(emitted) == len(set(emitted))


def test_every_declared_name_is_prefixed(graphing_objects):
    kinds = (metrics.Metric, graphs.Graph, perfometers.Perfometer)
    names = [o.name for o in graphing_objects if isinstance(o, kinds)]
    assert [n for n in names if not n.startswith(("oposs_smart_error", "oposs_smart_bms"))] == []


def test_graphs_and_perfometers_use_declared_metrics(graphing_objects, declared):
    used = set()
    for o in graphing_objects:
        if isinstance(o, graphs.Graph):
            used.update(o.simple_lines)
        elif isinstance(o, perfometers.Perfometer):
            used.update(o.segments)
    assert sorted(used - declared) == []


def test_old_names_translate_to_declared_metrics(graphing_objects, declared):
    found = [o for o in graphing_objects if isinstance(o, translations.Translation)]
    assert len(found) == 1
    translation = found[0]
    # The lookup key is the check command a live service runs today.
    assert translation.check_commands == [translations.PassiveCheck("oposs_smart_error")]
    assert sorted(translation.translations) == sorted(OLD_NAMES)
    for old, rule in translation.translations.items():
        assert rule == translations.RenameTo(f"oposs_smart_error_{old}")
        assert rule.metric_name in declared
