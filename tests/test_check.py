"""Tests for the check plugins (run on the Checkmk server)."""

import importlib.util
import json
import pathlib
import sys

import pytest

from cmk.agent_based.v2 import Metric, Result, Service, State

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK = ROOT / "local/lib/python3/cmk_addons/plugins/oposs_smart_error/agent_based/oposs_smart_error.py"

DAY = 86400
POH = 39841 * 60 + 21  # drive power-on time in minutes

MODE_PAGE = "001e001000000008ffffffff00000200dc01000c010003f00000000000000000"


@pytest.fixture(scope="module")
def check():
    name = "test_oposs_smart_error_check"
    spec = importlib.util.spec_from_file_location(name, CHECK)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    yield module
    sys.modules.pop(name, None)


def _device(**extra):
    data = {
        "device": "/dev/sdc",
        "protocol": "SCSI",
        "model": "WUH721818AL5204",
        "serial": "2JG5LEHB",
        "firmware": "C680",
        "capacity_bytes": 18000207937536,
        "error_counters": {
            "read": {
                "errors_corrected_by_eccfast": 0,
                "errors_corrected_by_eccdelayed": 321,
                "errors_corrected_by_rereads_rewrites": 0,
                "total_errors_corrected": 321,
                "correction_algorithm_invocations": 2211900,
                "gigabytes_processed": "1491706.280",
                "total_uncorrected_errors": 0,
            }
        },
    }
    data.update(extra)
    return data


def _scan(value=8, scans=35, progress="0.00%", **results):
    scan = {
        "status": {
            "value": value,
            "string": "some status",
            "number_scans_performed": scans,
            "scan_progress": progress,
            "number_medium_scans_performed": scans,
        }
    }
    scan.update(results)
    return scan


def _entry(pc, poh, reassign, lba=0x1234):
    return {
        "parameter_code": pc,
        "accumulated_power_on": {"minutes": poh},
        "lba": lba,
        "sense_key": {"value": 3, "string": "Medium Error"},
        "asc": 0x11,
        "ascq": 0,
        "reassign_status": {"value": reassign, "string": "x"},
    }


def _section(check, data):
    return check.parse_oposs_smart_error([["/dev/sdc", json.dumps(data)]])


def _bms(check, data, params=None, store=None):
    full = dict(check.BMS_DEFAULT_PARAMETERS)
    full.update(params or {})
    store = {} if store is None else store
    return list(check._check_bms("/dev/sdc (2JG5LEHB)", full, _section(check, data), store))


def _results(out):
    return [r for r in out if isinstance(r, Result)]


def _metrics(out):
    return {m.name: m.value for m in out if isinstance(m, Metric)}


def _worst(out):
    return State.worst(*(r.state for r in _results(out)))


# --- mode page --------------------------------------------------------------

def test_mode_page_decodes(check):
    page = check.parse_bms_mode_page(MODE_PAGE)
    assert page == {
        "enabled": True,
        "prescan": False,
        "interval_hours": 1008,
        "prescan_limit_hours": 0,
        "min_idle_ms": 0,
        "max_suspend_ms": 0,
    }


@pytest.mark.parametrize("raw", ["", "zz", "001e0010", MODE_PAGE.replace("dc01", "dc02")])
def test_mode_page_rejects_garbage(check, raw):
    assert check.parse_bms_mode_page(raw) is None


# --- discovery --------------------------------------------------------------

def test_bms_service_only_for_drives_with_scan_log(check):
    section = check.parse_oposs_smart_error([
        ["/dev/sdc", json.dumps(_device(background_scan=_scan(), power_on_minutes=POH))],
        ["/dev/sdd", json.dumps(_device(serial="NOBMS123"))],
        ["/dev/sde", "ERROR", "Failed to get SMART data"],
    ])
    assert list(check.discover_oposs_smart_bms(section)) == [Service(item="/dev/sdc (2JG5LEHB)")]


# --- status -----------------------------------------------------------------

@pytest.mark.parametrize("value,state", [
    (1, State.OK), (2, State.OK), (8, State.OK),
    (0, State.WARN),
    (3, State.CRIT), (4, State.CRIT),
    (5, State.WARN), (6, State.WARN), (7, State.WARN),
    (42, State.UNKNOWN),
])
def test_status_states(check, value, state):
    out = _bms(check, _device(background_scan=_scan(value=value), power_on_minutes=POH))
    assert _results(out)[0].state == state


def test_no_scan_state_is_configurable(check):
    out = _bms(check, _device(background_scan=_scan(value=0), power_on_minutes=POH),
               params={"state_no_scan": 0})
    assert _results(out)[0].state == State.OK


def test_progress_and_counters(check):
    out = _bms(check, _device(background_scan=_scan(value=1, scans=2, progress="54.08%"),
                              power_on_minutes=10845 * 60))
    metrics = _metrics(out)
    assert metrics["oposs_smart_bms_scan_progress"] == pytest.approx(54.08)
    assert metrics["oposs_smart_bms_scans_performed"] == 2
    assert metrics["oposs_smart_bms_lifetime_scan_interval"] == pytest.approx(10845 * 3600 / 2)
    assert "54.08%" in _results(out)[0].summary


def test_missing_device_is_unknown(check):
    out = list(check._check_bms("/dev/sdx (FOO)", check.BMS_DEFAULT_PARAMETERS, {}, {}))
    assert _worst(out) == State.UNKNOWN


# --- time since last completed scan -----------------------------------------

def test_first_run_reports_lower_bound(check):
    store = {}
    out = _bms(check, _device(background_scan=_scan(scans=35), power_on_minutes=POH), store=store)
    assert _metrics(out)["oposs_smart_bms_last_scan_age"] == 0
    assert any("at least" in r.summary for r in _results(out))
    assert store["last_scan"] == {"scans": 35, "poh": POH, "known": False}


def test_age_counts_drive_power_on_time(check):
    store = {"last_scan": {"scans": 35, "poh": POH - 100 * 24 * 60, "known": True}}
    out = _bms(check, _device(background_scan=_scan(scans=35), power_on_minutes=POH), store=store)
    assert _metrics(out)["oposs_smart_bms_last_scan_age"] == 100 * DAY
    assert _worst(out) == State.WARN  # default warn at 90 days


def test_completed_scan_resets_age(check):
    store = {"last_scan": {"scans": 35, "poh": POH - 100 * 24 * 60, "known": False}}
    out = _bms(check, _device(background_scan=_scan(scans=36), power_on_minutes=POH), store=store)
    assert _metrics(out)["oposs_smart_bms_last_scan_age"] == 0
    assert store["last_scan"] == {"scans": 36, "poh": POH, "known": True}
    assert _worst(out) == State.OK


def test_counter_going_back_restarts_tracking(check):
    store = {"last_scan": {"scans": 65535, "poh": POH - 10 * 24 * 60, "known": True}}
    _bms(check, _device(background_scan=_scan(scans=1), power_on_minutes=POH), store=store)
    assert store["last_scan"] == {"scans": 1, "poh": POH, "known": False}


def test_no_age_without_power_on_time(check):
    store = {}
    out = _bms(check, _device(background_scan=_scan()), store=store)
    assert "oposs_smart_bms_last_scan_age" not in _metrics(out)
    assert store == {}


# --- medium errors found by the scan ----------------------------------------

def test_no_medium_errors(check):
    out = _bms(check, _device(background_scan=_scan(), power_on_minutes=POH))
    assert _metrics(out)["oposs_smart_bms_medium_errors"] == 0
    assert _worst(out) == State.OK


def test_recent_unrecovered_error_is_crit(check):
    scan = _scan(result_1=_entry(1, POH - 60, reassign=1))
    out = _bms(check, _device(background_scan=scan, power_on_minutes=POH))
    assert _metrics(out)["oposs_smart_bms_medium_errors"] == 1
    assert _worst(out) == State.CRIT
    assert any("0x1234" in (r.details or "") for r in _results(out))


def test_recent_recovered_error_is_warn(check):
    scan = _scan(result_1=_entry(1, POH - 60, reassign=2))
    out = _bms(check, _device(background_scan=scan, power_on_minutes=POH))
    assert _worst(out) == State.WARN


def test_old_errors_are_ok_by_default(check):
    scan = _scan(
        result_1=_entry(1, POH - 30 * 24 * 60, reassign=1),
        result_2=_entry(2, POH - 20 * 24 * 60, reassign=2),
    )
    out = _bms(check, _device(background_scan=scan, power_on_minutes=POH))
    assert _metrics(out)["oposs_smart_bms_medium_errors"] == 2
    assert _worst(out) == State.OK


def test_old_error_state_is_configurable(check):
    scan = _scan(result_1=_entry(1, POH - 30 * 24 * 60, reassign=1))
    out = _bms(check, _device(background_scan=scan, power_on_minutes=POH),
               params={"state_old_errors": 1})
    assert _worst(out) == State.WARN


@pytest.mark.parametrize("reassign", [0, 1, 3, 4, 7, 8, 15])
def test_unrecovered_classes(check, reassign):
    scan = _scan(result_1=_entry(1, POH - 60, reassign=reassign))
    out = _bms(check, _device(background_scan=scan, power_on_minutes=POH))
    assert _worst(out) == State.CRIT


@pytest.mark.parametrize("reassign", [2, 5, 6])
def test_recovered_classes(check, reassign):
    scan = _scan(result_1=_entry(1, POH - 60, reassign=reassign))
    out = _bms(check, _device(background_scan=scan, power_on_minutes=POH))
    assert _worst(out) == State.WARN


# --- mode page in the service -----------------------------------------------

def test_mode_page_shown_in_details(check):
    out = _bms(check, _device(background_scan=_scan(), power_on_minutes=POH, bms_mode_page=MODE_PAGE))
    details = " ".join(r.details for r in _results(out))
    assert "1008 h" in details


# --- grown defect list in the error counter service --------------------------

def _errors(check, data, params=None):
    return list(check.check_oposs_smart_error("/dev/sdc (2JG5LEHB)", params or {}, _section(check, data)))


def test_grown_defects_metric(check):
    out = _errors(check, _device(grown_defects=3))
    assert _metrics(out)["oposs_smart_error_grown_defects"] == 3
    assert _worst(out) == State.OK


def test_grown_defects_levels(check):
    out = _errors(check, _device(grown_defects=3), params={"grown_defects_abs": ("fixed", (1, 10))})
    assert _worst(out) == State.WARN


def test_error_check_without_grown_defects_unchanged(check):
    out = _errors(check, _device())
    assert "oposs_smart_error_grown_defects" not in _metrics(out)


def test_raid_member_items_are_unique(check):
    lines = [
        ["/dev/bus/0 megaraid,0", json.dumps(_device(device="/dev/bus/0 megaraid,0", serial="B"))],
        ["/dev/bus/0 megaraid,1", json.dumps(_device(device="/dev/bus/0 megaraid,1", serial="C"))],
    ]
    section = check.parse_oposs_smart_error(lines)
    items = [s.item for s in check.discover_oposs_smart_error(section)]
    assert items == ["/dev/bus/0 megaraid,0 (B)", "/dev/bus/0 megaraid,1 (C)"]
    out = list(check.check_oposs_smart_error(items[1], {}, section))
    assert "(bus/0 megaraid,1)" in " ".join(r.summary for r in _results(out))


def test_medium_errors_listed_oldest_first(check):
    # result_10 must not sort before result_2
    entries = {f"result_{n}": _entry(n, POH - 30 * DAY // 60 + n, 2, lba=n) for n in (1, 2, 10)}
    out = _bms(check, _device(power_on_minutes=POH, background_scan=_scan(**entries)))
    details = " ".join(r.details for r in _results(out))
    assert details.index("LBA 0x2 ") < details.index("LBA 0xa ")


@pytest.mark.parametrize("progress", ["-", "n/a", None])
def test_odd_scan_progress_does_not_crash(check, progress):
    out = _bms(check, _device(power_on_minutes=POH, background_scan=_scan(progress=progress)))
    assert _worst(out) == State.OK
    assert "oposs_smart_bms_scan_progress" not in _metrics(out)


def test_omitted_medium_errors_are_counted(check):
    entries = {f"result_{n}": _entry(n, POH - 10, 2, lba=n) for n in (1, 2)}
    scan = _scan(**entries)
    scan["results_omitted"] = 7
    out = _bms(check, _device(power_on_minutes=POH, background_scan=scan))
    assert _metrics(out)["oposs_smart_bms_medium_errors"] == 9
    old = [r for r in _results(out) if "older medium error" in r.summary]
    assert old and old[0].summary.startswith("7 ")
    assert "7 older entries not sent by the agent" in old[0].details
