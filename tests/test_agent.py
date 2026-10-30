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
def agent(tmp_path, monkeypatch):
    loader = SourceFileLoader("oposs_smart_error_agent", str(AGENT))
    module = module_from_spec(spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    # Never read the host's baked settings or write its state file
    monkeypatch.setattr(module, "CONFIG_FILE", str(tmp_path / "unbaked" / Path(module.CONFIG_FILE).name))
    monkeypatch.setattr(module, "STATE_FILE", str(tmp_path / "oposs_smart_error.state.json"))
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
# Without smartctl's text message the reason names the exit bit.
@pytest.mark.parametrize("rc,reason", [
    (1, "command line did not parse"),
    (2, "device open failed"),
    (2 + 4, "device open failed"),
])
def test_unusable_exit_status_is_reported(agent, monkeypatch, capsys, rc, reason):
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--json=c", "--log=error"): (rc, json.dumps(INFO)),
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


# --- a drive that names itself but returns no data -----------------------------

# smartctl 7.4 for a SAS drive that fails Test Unit Ready: its identity arrives
# as JSON, the reason only in the text output.
FAILED_JSON = {
    "smartctl": {"exit_status": 2},
    "device": {"name": "/dev/sdc", "type": "scsi", "protocol": "SCSI"},
    "scsi_model_name": "WDC WUH722222AL5204",
    "scsi_revision": "C7C0",
    "serial_number": "1RKH8LJG",
    "scsi_transport_protocol": {"name": "SAS (SPL-4)", "value": 6},
}

FAILED_TEXT = """smartctl 7.4 2023-08-01 r5530 [x86_64-linux-6.8.0-124-generic] (local build)
Copyright (C) 2002-23, Bruce Allen, Christian Franke, www.smartmontools.org

=== START OF INFORMATION SECTION ===
Vendor:               WDC
Product:              WUH722222AL5204
Revision:             C7C0
LU is fully provisioned
Serial number:        1RKH8LJG
Transport protocol:   SAS (SPL-4)
Local Time is:        Thu Oct 29 10:01:39 2026 CET
device Test Unit Ready  [medium or hardware error (serious)]
A mandatory SMART command failed: exiting. To continue, add one or more '-T permissive' options.
"""


def _failed_drive(agent, monkeypatch, capsys, text=FAILED_TEXT, data=FAILED_JSON):
    responses = {("--json=c", "--log=error"): (2, json.dumps(data))}
    if text is not None:
        responses[("--log=error",)] = (2, text)
    responses[("--scan",)] = (0, json.dumps(SCAN))
    monkeypatch.setattr(agent.subprocess, "run", _fake_run(responses))
    agent.main()
    (line,) = _output_lines(capsys)
    return line.split("|")


def test_failed_drive_reports_smartctl_message(agent, monkeypatch, capsys):
    fields = _failed_drive(agent, monkeypatch, capsys)
    assert fields[:3] == [
        "/dev/sdc", "ERROR",
        "Failed to get SMART data: device Test Unit Ready [medium or hardware error (serious)]"
        " (smartctl exit status 2)",
    ]


def test_failed_drive_reports_identity(agent, monkeypatch, capsys):
    fields = _failed_drive(agent, monkeypatch, capsys)
    assert json.loads(fields[3]) == {
        "model": "WDC WUH722222AL5204",
        "serial": "1RKH8LJG",
        "firmware": "C7C0",
        "protocol": "SCSI",
        "transport": "SAS (SPL-4)",
    }


def test_failed_drive_without_text_output_keeps_exit_bit_reason(agent, monkeypatch, capsys):
    fields = _failed_drive(agent, monkeypatch, capsys, text=None)
    assert fields[2] == "Failed to get SMART data: device open failed (smartctl exit status 2)"


def test_failed_drive_without_serial_has_no_identity(agent, monkeypatch, capsys):
    data = {k: v for k, v in FAILED_JSON.items() if k != "serial_number"}
    fields = _failed_drive(agent, monkeypatch, capsys, data=data)
    assert len(fields) == 3


def test_open_failure_message(agent, monkeypatch, capsys):
    text = ("smartctl 7.4 2023-08-01 r5530 [x86_64-linux-6.8.0-124-generic] (local build)\n"
            "Copyright (C) 2002-23, Bruce Allen, Christian Franke, www.smartmontools.org\n\n"
            "Smartctl open device: /dev/sdc failed: No such device\n")
    fields = _failed_drive(agent, monkeypatch, capsys, text=text, data={"smartctl": {"exit_status": 2}})
    assert fields == ["/dev/sdc", "ERROR",
                      "Failed to get SMART data: Smartctl open device: /dev/sdc failed: No such device"
                      " (smartctl exit status 2)"]


def test_separator_in_message_is_replaced(agent, monkeypatch, capsys):
    text = FAILED_TEXT.replace("(serious)", "(a|b)")
    fields = _failed_drive(agent, monkeypatch, capsys, text=text)
    assert "[medium or hardware error (a/b)]" in fields[2]
    assert len(fields) == 4


# --- disks in standby ----------------------------------------------------------

# smartctl -n standby,3 exits with 3 and reads nothing when the disk sleeps
ASLEEP = {"smartctl": {"exit_status": 3},
          "device": {"name": "/dev/sdc", "type": "scsi", "protocol": "SCSI"}}


def _sleepy_run(asleep, calls):
    """smartctl answering as a disk that sleeps while asleep[0] is true"""
    def run(cmd, **kwargs):
        calls.append(cmd)
        if "--scan" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(SCAN), stderr="")
        if asleep[0] and any(arg.startswith("standby") for arg in cmd):
            return subprocess.CompletedProcess(cmd, 3, stdout=json.dumps(ASLEEP), stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(FULL), stderr="")
    return run


def _standby_line(capsys):
    (line,) = _output_lines(capsys)
    device, status, data = line.split("|", 2)
    assert (device, status) == ("/dev/sdc", "STANDBY")
    return json.loads(data)


def _bake(agent, bakery, tmp_path, monkeypatch, conf):
    target, lines = _baked_config(bakery, conf)
    (tmp_path / target).write_text("\n".join(lines))
    monkeypatch.setattr(agent, "CONFIG_FILE", str(tmp_path / target))


def test_sleeping_disks_are_skipped_by_default(agent, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _sleepy_run([True], calls))
    agent.main()
    assert _standby_line(capsys) == {"skips": 1}
    (call,) = [c for c in calls if "--scan" not in c]
    assert call[call.index("-n") + 1] == "standby,3"
    # the device type still comes last, so autodetection cannot spin the disk up
    assert call[-3:] == ["-d", "scsi", "/dev/sdc"]


def test_waking_is_configurable(agent, bakery, monkeypatch, tmp_path, capsys):
    _bake(agent, bakery, tmp_path, monkeypatch, {"standby": "wake"})
    calls = []
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _sleepy_run([True], calls))
    agent.main()
    assert "/dev/sdc" in _output_records(capsys)
    assert not any("-n" in c for c in calls)


def test_exit_status_3_without_nocheck_is_still_an_error(agent, monkeypatch, capsys):
    # Without -n, bits 0 and 1 keep their meaning
    monkeypatch.setattr(agent, "get_config", lambda: dict(agent.DEFAULT_CONFIG, standby="wake"))
    monkeypatch.setattr(agent.subprocess, "run", _fake_run({
        ("--scan",): (0, json.dumps(SCAN)),
        ("--log=error",): (3, json.dumps(ASLEEP)),
    }))
    agent.main()
    (line,) = _output_lines(capsys)
    assert line.startswith("/dev/sdc|ERROR|")


def test_sleeping_disk_keeps_identity_of_last_read(agent, monkeypatch, capsys):
    asleep = [False]
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _sleepy_run(asleep, []))
    agent.main()
    capsys.readouterr()
    asleep[0] = True
    agent.main()
    agent.main()
    assert _output_lines(capsys)[-1] == "/dev/sdc|STANDBY|" + json.dumps({
        "skips": 2,
        "serial": "2JG5LEHB",
        "model": "WUH721818AL5204",
        "firmware": "C680",
        "capacity_bytes": 18000207937536,
        "background_scan": True,
    }, separators=(",", ":"))


def test_disk_that_wakes_up_is_read_again(agent, monkeypatch, capsys):
    asleep = [True]
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _sleepy_run(asleep, []))
    agent.main()
    asleep[0] = False
    agent.main()
    asleep[0] = True
    agent.main()
    lines = _output_lines(capsys)
    # the skip count starts over after a successful read
    assert json.loads(lines[-1].split("|", 2)[2])["skips"] == 1


def test_sleeping_disk_is_woken_after_n_skips(agent, bakery, monkeypatch, tmp_path, capsys):
    _bake(agent, bakery, tmp_path, monkeypatch, {"wake_after": 2})
    calls = []
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _sleepy_run([True], calls))
    for _ in range(4):
        agent.main()
    reads = [c for c in calls if "--scan" not in c]
    assert ["-n" in c for c in reads] == [True, True, False, True]
    lines = capsys.readouterr().out.splitlines()
    statuses = [line.split("|")[1] for line in lines if line.startswith("/dev/sdc")]
    assert statuses[0] == statuses[1] == statuses[3] == "STANDBY"
    assert statuses[2].startswith("{")


def test_unreadable_state_file_is_ignored(agent, monkeypatch, capsys):
    with open(agent.STATE_FILE, "w") as f:
        f.write("not json")
    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", _sleepy_run([True], []))
    agent.main()
    assert _standby_line(capsys) == {"skips": 1}


def test_raid_path_of_a_sleeping_listed_disk_is_skipped(agent, monkeypatch, capsys):
    # The JBOD disk sleeps; its /dev/bus/0 path must not add a second line
    scan = {"devices": [
        {"name": "/dev/sdc", "type": "scsi", "protocol": "SCSI"},
        {"name": "/dev/bus/0", "type": "megaraid,1", "protocol": "SCSI"},
    ]}
    asleep = [False]

    def run(cmd, **kwargs):
        if "--scan" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(scan), stderr="")
        if asleep[0]:
            return subprocess.CompletedProcess(cmd, 3, stdout=json.dumps(ASLEEP), stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(FULL), stderr="")

    monkeypatch.setattr(agent.shutil, "which", lambda name: None)
    monkeypatch.setattr(agent.subprocess, "run", run)
    agent.main()
    capsys.readouterr()
    asleep[0] = True
    agent.main()
    assert [line.split("|")[0] for line in _output_lines(capsys)] == ["/dev/sdc"]


def test_bakery_defaults(bakery):
    files = list(bakery.get_oposs_smart_error_files({}))
    (plugin,) = [f for f in files if "lines" not in f.kwargs]
    assert plugin.kwargs["interval"] == 1800
    (config,) = [f for f in files if "lines" in f.kwargs]
    assert json.loads("\n".join(config.kwargs["lines"])) == {
        "timeout": 5, "standby": "skip", "wake_after": 0}


def test_standby_defaults_are_the_same_with_and_without_bakery(agent, bakery, monkeypatch, tmp_path):
    unbaked = agent.get_config()
    _bake(agent, bakery, tmp_path, monkeypatch, {})
    assert agent.get_config() == unbaked
