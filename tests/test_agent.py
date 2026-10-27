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
        ("--log=error",): (0, json.dumps(INFO)),
        ("--log=background",): (0, json.dumps(BACKGROUND)),
        ("sg_modes",): (0, MODE_PAGE),
    }))
    agent.main()
    data = _output_records(capsys)["/dev/sdc"]
    assert data["error_counters"] == INFO["scsi_error_counter_log"]
    assert data["background_scan"] == BACKGROUND["scsi_background_scan"]
    assert data["power_on_minutes"] == 39841 * 60 + 21
    assert data["grown_defects"] == 0
    assert data["bms_mode_page"] == MODE_PAGE.hex()


def test_failing_background_query_keeps_error_counters(agent, monkeypatch, capsys):
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (0, json.dumps(INFO)),
        ("--log=background",): (64 + 128, "not json"),
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
        ("--log=error",): (0, json.dumps(INFO)),
        ("--log=background",): (0, json.dumps(BACKGROUND)),
    }))
    agent.main()
    data = _output_records(capsys)["/dev/sdc"]
    assert data["background_scan"]["status"]["value"] == 8
    assert "bms_mode_page" not in data


def test_mode_page_skipped_when_sg_modes_fails(agent, monkeypatch, capsys):
    monkeypatch.setattr(agent.shutil, "which", lambda name: "/usr/bin/sg_modes")
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (0, json.dumps(INFO)),
        ("--log=background",): (0, json.dumps(BACKGROUND)),
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
        ("--log=error",): (rc, json.dumps(INFO)),
        ("--log=background",): (rc, json.dumps(BACKGROUND)),
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
