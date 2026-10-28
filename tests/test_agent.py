"""Tests for the agent plugin (runs on the monitored host)."""

import json
import subprocess
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import pytest

AGENT = Path(__file__).parent.parent / "local/share/check_mk/agents/plugins/oposs_smart_error"

# Real MODE SENSE(10) response for page 0x1c/1 from a WUH721818AL5204
MODE_PAGE = bytes.fromhex(
    "001e001000000008ffffffff00000200"
    "dc01000c010003f00000000000000000"
)

SCAN = {"devices": [{"name": "/dev/sdc", "type": "scsi", "protocol": "SCSI"}]}

INFO = {
    "device": {"name": "/dev/sdc", "type": "scsi", "protocol": "SCSI"},
    "model_name": "WUH721818AL5204",
    "serial_number": "2JG5LEHB",
    "firmware_version": "C680",
    "user_capacity": {"bytes": 18000207937536},
    "scsi_error_counter_log": {
        "read": {"total_errors_corrected": 321, "total_uncorrected_errors": 0},
    },
}

BACKGROUND = {
    "power_on_time": {"hours": 39841, "minutes": 21},
    "scsi_grown_defect_list": 0,
    "scsi_background_scan": {
        "status": {
            "value": 8,
            "string": "waiting until BMS interval timer expires",
            "number_scans_performed": 35,
            "scan_progress": "0.00%",
            "number_medium_scans_performed": 35,
        }
    },
}

# One smartctl call answers both the error log and the background scan log
FULL = {**INFO, **BACKGROUND}


@pytest.fixture
def agent():
    loader = SourceFileLoader("oposs_smart_error_agent", str(AGENT))
    module = module_from_spec(spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def _fake_run(responses):
    """Return a subprocess.run replacement answering by argv."""

    def run(cmd, **kwargs):
        for match, (rc, out) in responses.items():
            if all(part in cmd for part in match):
                if kwargs.get("text"):
                    out = out if isinstance(out, str) else out.decode()
                return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr="")
        raise FileNotFoundError(cmd[0])

    return run


def _output_records(capsys):
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "<<<oposs_smart_error:sep(124)>>>"
    return {line.split("|", 1)[0]: json.loads(line.split("|", 1)[1]) for line in lines[1:]}


def test_background_scan_data_is_added(agent, monkeypatch, capsys):
    monkeypatch.setattr(agent.shutil, "which", lambda name: "/usr/bin/sg_modes")
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (0, json.dumps(FULL)),
        ("sg_modes",): (0, MODE_PAGE),
    }))
    agent.main()
    data = _output_records(capsys)["/dev/sdc"]
    assert data["error_counters"] == INFO["scsi_error_counter_log"]
    assert data["background_scan"] == BACKGROUND["scsi_background_scan"]
    assert data["power_on_minutes"] == 39841 * 60 + 21
    assert data["grown_defects"] == 0
    assert data["bms_mode_page"] == MODE_PAGE.hex()


def test_drive_without_background_log_keeps_error_counters(agent, monkeypatch, capsys):
    # smartctl sets bit 2 when a requested log page is not supported
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (4, json.dumps(INFO)),
    }))
    agent.main()
    data = _output_records(capsys)["/dev/sdc"]
    assert data["error_counters"] == INFO["scsi_error_counter_log"]
    assert "background_scan" not in data
    assert "bms_mode_page" not in data


def test_mode_page_skipped_without_sg_modes(agent, monkeypatch, capsys):
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (0, json.dumps(FULL)),
    }))
    agent.main()
    data = _output_records(capsys)["/dev/sdc"]
    assert data["background_scan"]["status"]["value"] == 8
    assert "bms_mode_page" not in data


def test_mode_page_skipped_when_sg_modes_fails(agent, monkeypatch, capsys):
    monkeypatch.setattr(agent.shutil, "which", lambda name: "/usr/bin/sg_modes")
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (0, json.dumps(FULL)),
        ("sg_modes",): (5, b""),
    }))
    agent.main()
    assert "bms_mode_page" not in _output_records(capsys)["/dev/sdc"]


# --- timeout configured by the agent bakery ---------------------------------

BAKERY = Path(__file__).parent.parent / "local/lib/python3/cmk/base/cee/plugins/bakery/oposs_smart_error.py"


@pytest.fixture
def bakery():
    loader = SourceFileLoader("oposs_smart_error_bakery", str(BAKERY))
    module = module_from_spec(spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def _baked_config(bakery, conf):
    files = list(bakery.get_oposs_smart_error_files(conf))
    (config,) = [f for f in files if "lines" in f.kwargs]
    return config.kwargs["target"], config.kwargs["lines"]


def test_agent_reads_the_baked_timeout(agent, bakery, monkeypatch, tmp_path):
    target, lines = _baked_config(bakery, {"timeout": 12.0})
    (tmp_path / target).write_text("\n".join(lines))
    monkeypatch.setattr(agent, "CONFIG_FILE", str(tmp_path / Path(agent.CONFIG_FILE).name))
    assert agent.get_timeout() == 12


def test_default_timeout_is_the_same_with_and_without_bakery(agent, bakery, monkeypatch, tmp_path):
    target, lines = _baked_config(bakery, {})
    monkeypatch.setattr(agent, "CONFIG_FILE", str(tmp_path / "missing.json"))
    unbaked = agent.get_timeout()
    (tmp_path / target).write_text("\n".join(lines))
    monkeypatch.setattr(agent, "CONFIG_FILE", str(tmp_path / target))
    assert agent.get_timeout() == unbaked


# --- smartctl exit status ----------------------------------------------------

def _output_lines(capsys):
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "<<<oposs_smart_error:sep(124)>>>"
    return lines[1:]


# Bit 2 (a command failed) and bits 3 to 7 (drive health) still leave the JSON
# complete, so the counters are reported.
@pytest.mark.parametrize("rc", [4, 8, 64, 4 + 64, 4 + 128])
def test_counters_reported_despite_exit_status(agent, monkeypatch, capsys, rc):
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (rc, json.dumps(FULL)),
    }))
    agent.main()
    data = _output_records(capsys)["/dev/sdc"]
    assert data["error_counters"] == INFO["scsi_error_counter_log"]
    assert data["background_scan"] == BACKGROUND["scsi_background_scan"]


# Bit 0 (command line not parsed) and bit 1 (device open failed) mean no data.
@pytest.mark.parametrize("rc,reason", [
    (1, "command line did not parse"),
    (2, "device open failed"),
    (2 + 4, "device open failed"),
])
def test_unusable_exit_status_is_reported(agent, monkeypatch, capsys, rc, reason):
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (rc, json.dumps(INFO)),
    }))
    agent.main()
    (line,) = _output_lines(capsys)
    assert line.startswith("/dev/sdc|ERROR|Failed to get SMART data")
    assert reason in line
    assert f"exit status {rc}" in line


# --- drive identity ----------------------------------------------------------

def test_sas_drive_model_and_firmware(agent, monkeypatch, capsys):
    # smartctl names these fields differently for SCSI/SAS drives
    info = {k: v for k, v in INFO.items() if k not in ("model_name", "firmware_version")}
    info.update(scsi_vendor="WDC", scsi_product="WUH721818AL5204",
                scsi_model_name="WDC WUH721818AL5204", scsi_revision="C680")
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (0, json.dumps(info)),
    }))
    agent.main()
    data = _output_records(capsys)["/dev/sdc"]
    assert data["model"] == "WDC WUH721818AL5204"
    assert data["firmware"] == "C680"


def test_ata_style_model_and_firmware(agent, monkeypatch, capsys):
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (0, json.dumps(INFO)),
    }))
    agent.main()
    data = _output_records(capsys)["/dev/sdc"]
    assert data["model"] == "WUH721818AL5204"
    assert data["firmware"] == "C680"


# --- device type from the scan ----------------------------------------------

def _recording_run(info_by_type, calls):
    def run(cmd, **kwargs):
        calls.append(cmd)
        if "--scan" in cmd:
            out = json.dumps(MEGARAID_SCAN)
        elif cmd[0] == "sg_modes":
            out = MODE_PAGE
        elif "--log=error" in cmd:
            out = json.dumps(info_by_type[cmd[cmd.index("-d") + 1]])
        else:
            raise AssertionError(f"unexpected call {cmd}")
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")
    return run


MEGARAID_SCAN = {"devices": [
    {"name": "/dev/sdc", "info_name": "/dev/sdc", "type": "scsi", "protocol": "SCSI"},
    {"name": "/dev/bus/0", "info_name": "/dev/bus/0 [megaraid_disk_00]", "type": "megaraid,0", "protocol": "SCSI"},
    {"name": "/dev/bus/0", "info_name": "/dev/bus/0 [megaraid_disk_01]", "type": "megaraid,1", "protocol": "SCSI"},
]}


def _info(serial):
    return dict(FULL, serial_number=serial)


def test_scan_device_type_is_used(agent, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(agent.shutil, "which", lambda name: "/usr/bin/sg_modes")
    monkeypatch.setattr(agent.subprocess, "run", _recording_run(
        {"scsi": _info("A"), "megaraid,0": _info("B"), "megaraid,1": _info("C")}, calls))
    agent.main()
    records = _output_records(capsys)
    # A plain device keeps its name, so existing services keep their item
    assert sorted(records) == ["/dev/bus/0 megaraid,0", "/dev/bus/0 megaraid,1", "/dev/sdc"]
    assert records["/dev/bus/0 megaraid,1"]["serial"] == "C"
    assert records["/dev/bus/0 megaraid,1"]["device"] == "/dev/bus/0 megaraid,1"
    smartctl = [c for c in calls if c[0] == "smartctl" and "--scan" not in c]
    # one call per device answers info, error log and background scan log
    assert len(smartctl) == 3
    assert all("--log=error" in c and "--log=background" in c and "--attributes" in c for c in smartctl)
    assert all(c[-3] == "-d" for c in smartctl)
    assert ["-d", "megaraid,1", "/dev/bus/0"] in [c[-3:] for c in smartctl]


def test_mode_page_not_read_behind_raid_controller(agent, monkeypatch, capsys):
    # sg_modes on /dev/bus/0 would ask the controller, not the disk
    calls = []
    monkeypatch.setattr(agent.shutil, "which", lambda name: "/usr/bin/sg_modes")
    monkeypatch.setattr(agent.subprocess, "run", _recording_run(
        {"scsi": _info("A"), "megaraid,0": _info("B"), "megaraid,1": _info("C")}, calls))
    agent.main()
    records = _output_records(capsys)
    assert "bms_mode_page" in records["/dev/sdc"]
    assert "bms_mode_page" not in records["/dev/bus/0 megaraid,0"]
    assert [c[-1] for c in calls if c[0] == "sg_modes"] == ["/dev/sdc"]


@pytest.mark.parametrize("configured", [0, 0.4])
def test_baked_timeout_is_at_least_one_second(agent, bakery, monkeypatch, tmp_path, configured):
    target, lines = _baked_config(bakery, {"timeout": configured})
    (tmp_path / target).write_text("\n".join(lines))
    monkeypatch.setattr(agent, "CONFIG_FILE", str(tmp_path / target))
    assert agent.get_timeout() >= 1


def test_raid_path_of_a_listed_disk_is_skipped(agent, monkeypatch, capsys):
    # A JBOD disk on a MegaRAID controller shows up as /dev/sdX and as
    # /dev/bus/0 megaraid,N; one service is enough, and the plain one keeps
    # the item it had before.
    scan = {"devices": [
        {"name": "/dev/bus/0", "type": "megaraid,1", "protocol": "SCSI"},
        {"name": "/dev/sdc", "type": "scsi", "protocol": "SCSI"},
        {"name": "/dev/bus/0", "type": "megaraid,2", "protocol": "SCSI"},
    ]}
    serials = {"megaraid,1": "A", "scsi": "A", "megaraid,2": "B"}

    def run(cmd, **kwargs):
        if "--scan" in cmd:
            out = scan
        elif "--log=error" in cmd:
            out = _info(serials[cmd[cmd.index("-d") + 1]])
        else:
            out = {}
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(out), stderr="")

    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", run)
    agent.main()
    assert sorted(_output_records(capsys)) == ["/dev/bus/0 megaraid,2", "/dev/sdc"]


def test_large_background_scan_log_is_trimmed(agent, monkeypatch, capsys):
    results = {
        f"result_{n}": {"parameter_code": n, "accumulated_power_on": {"minutes": 1000 + n}, "lba": n}
        for n in range(1, 201)
    }
    full = dict(FULL, scsi_background_scan=dict(BACKGROUND["scsi_background_scan"], **results))
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (0, json.dumps(full)),
    }))
    agent.main()
    scan = _output_records(capsys)["/dev/sdc"]["background_scan"]
    kept = sorted(int(k.split("_")[1]) for k in scan if k.startswith("result_"))
    assert kept == list(range(151, 201))  # the newest ones
    assert scan["results_omitted"] == 150
    assert scan["status"] == BACKGROUND["scsi_background_scan"]["status"]
