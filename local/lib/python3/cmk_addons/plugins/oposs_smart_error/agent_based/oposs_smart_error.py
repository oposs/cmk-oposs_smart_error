#!/usr/bin/env python3
"""
CheckMK Check Plugin for SMART Error Monitoring
Processes SMART error counter logs and generates metrics
This runs on the CheckMK server
Compatible with CheckMK 2.3
"""

import json
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Metric,
    Result,
    Service,
    State,
    StringTable,
    render,
    check_levels,
    get_value_store,
)


Section = Dict[str, Dict[str, Any]]


def _render_error_count(value: float) -> str:
    """Render error count as integer."""
    return f"{int(value)}"


def _create_device_description(device_path: str, model: str, serial: str, capacity_bytes: int) -> str:
    """Create a friendly device description"""
    parts = []
    
    if model:
        parts.append(model)
    
    if capacity_bytes > 0:
        capacity_str = render.bytes(capacity_bytes)
        parts.append(f"({capacity_str})")
    
    if serial:
        # Show last 8 characters of serial for identification
        serial_short = serial[-8:] if len(serial) > 8 else serial
        parts.append(f"S/N: {serial_short}")
    
    if parts:
        # Drop the /dev/ prefix (sda from /dev/sda, bus/0 megaraid,1 from /dev/bus/0 megaraid,1)
        device_name = device_path[len("/dev/"):] if device_path.startswith("/dev/") else device_path
        return f"{' '.join(parts)} ({device_name})"
    else:
        return device_path


def parse_oposs_smart_error(string_table: StringTable) -> Section:
    """Parse SMART error data from agent output"""
    section = {}
    
    for line in string_table:
        if len(line) < 2:
            continue
            
        device_name = line[0]
        
        if line[1] == "ERROR":
            # Handle error cases
            error_msg = line[2] if len(line) > 2 else "Unknown error"
            section[device_name] = {"error": error_msg}
            continue
        
        try:
            data = json.loads(line[1])
            section[device_name] = data
        except json.JSONDecodeError:
            section[device_name] = {"error": "Invalid JSON data"}
    
    return section


def _service_item(device_name: str, data: Dict[str, Any]) -> str:
    """Service item with device name and serial number for unique identification"""
    serial = data.get("serial", "")
    if serial:
        # Use last 8 chars of serial for uniqueness
        serial_short = serial[-8:] if len(serial) > 8 else serial
        return f"{device_name} ({serial_short})"
    # Fallback to device name with "no-serial" if no serial available
    return f"{device_name} (no-serial)"


def _device_from_item(item: str) -> str:
    """Extract device name from service item format: "/dev/sda (serial)" """
    if " (" in item and item.endswith(")"):
        return item.split(" (")[0].strip()
    # Should not happen with current discovery logic, but handle gracefully
    return item.strip()


def discover_oposs_smart_error(section: Section) -> DiscoveryResult:
    """Discover SMART error services"""
    for device_name, data in section.items():
        if "error" not in data:
            yield Service(item=_service_item(device_name, data))


def check_oposs_smart_error(item: str, params: Mapping[str, Any], section: Section) -> CheckResult:
    """Check SMART error counters and generate metrics"""
    device_name = _device_from_item(item)
    
    if device_name not in section:
        yield Result(state=State.UNKNOWN, summary=f"Device {device_name} not found")
        return
    
    data = section[device_name]
    
    if "error" in data:
        yield Result(state=State.CRIT, summary=f"Error: {data['error']}")
        return
    
    error_counters = data.get("error_counters", {})
    device_info = data.get("device", device_name)
    protocol = data.get("protocol", "unknown")
    model = data.get("model", "")
    serial = data.get("serial", "")
    capacity_bytes = data.get("capacity_bytes", 0)
    
    # Create friendly device description
    device_desc = _create_device_description(device_info, model, serial, capacity_bytes)
    
    if not error_counters:
        yield Result(state=State.UNKNOWN, summary=f"{device_desc}: No error counter data available")
        return
    
    # Process each operation type (read, write, verify)
    read_processed_gb = 0.0
    write_processed_gb = 0.0
    verify_processed_gb = 0.0
    
    for operation, counters in error_counters.items():
        if not isinstance(counters, dict):
            continue
        
        # Extract all detailed fields from SMART data
        eccfast = counters.get("errors_corrected_by_eccfast", 0)
        eccdelayed = counters.get("errors_corrected_by_eccdelayed", 0)
        rereads = counters.get("errors_corrected_by_rereads_rewrites", 0)
        corrected = counters.get("total_errors_corrected", 0)
        algorithm_invocations = counters.get("correction_algorithm_invocations", 0)
        processed_gb = float(counters.get("gigabytes_processed", "0"))
        processed_bytes = processed_gb * (1024 ** 3)  # Convert GB to bytes
        uncorrected = counters.get("total_uncorrected_errors", 0)
        
        # Track operation-specific processed bytes
        if operation == "read":
            read_processed_gb += processed_gb
        elif operation == "write":
            write_processed_gb += processed_gb
        elif operation == "verify":
            verify_processed_gb += processed_gb
        
        # Generate detailed absolute metrics (6 values - excluding redundant total_errors_corrected)
        yield Metric(f"oposs_smart_error_{operation}_errors_corrected_by_eccfast", eccfast)
        yield Metric(f"oposs_smart_error_{operation}_errors_corrected_by_eccdelayed", eccdelayed)
        yield Metric(f"oposs_smart_error_{operation}_errors_corrected_by_rereads_rewrites", rereads)
        yield Metric(f"oposs_smart_error_{operation}_correction_algorithm_invocations", algorithm_invocations)
        yield Metric(f"oposs_smart_error_{operation}_bytes_processed", processed_bytes)
        yield Metric(f"oposs_smart_error_{operation}_total_uncorrected_errors", uncorrected)
        
        # Generate detailed relative metrics per TB (4 values - excluding uncorrected errors)
        if processed_gb > 0:
            processed_tb = processed_gb / 1024  # Convert GB to TB
            yield Metric(f"oposs_smart_error_{operation}_errors_corrected_by_eccfast_per_tb", eccfast / processed_tb)
            yield Metric(f"oposs_smart_error_{operation}_errors_corrected_by_eccdelayed_per_tb", eccdelayed / processed_tb)
            yield Metric(f"oposs_smart_error_{operation}_errors_corrected_by_rereads_rewrites_per_tb", rereads / processed_tb)
            yield Metric(f"oposs_smart_error_{operation}_correction_algorithm_invocations_per_tb", algorithm_invocations / processed_tb)
    
    
    # Device info summary
    yield Result(state=State.OK, summary=device_desc)

    # Grown defect list: sectors the drive has remapped since it left the factory
    grown_defects = data.get("grown_defects")
    if grown_defects is not None:
        levels_param = params.get("grown_defects_abs")
        if levels_param is not None:
            yield from check_levels(
                grown_defects,
                levels_upper=levels_param,
                metric_name="oposs_smart_error_grown_defects",
                label="Grown defects",
                render_func=_render_error_count,
            )
        else:
            yield Result(state=State.OK, notice=f"Grown defects: {grown_defects}")
            yield Metric("oposs_smart_error_grown_defects", grown_defects)
    
    # Individual error type results with their own states
    for operation in ["read", "write", "verify"]:
        if operation in error_counters:
            counters = error_counters[operation]
            if isinstance(counters, dict):
                uncorrected = counters.get("total_uncorrected_errors", 0)
                eccfast = counters.get("errors_corrected_by_eccfast", 0)
                eccdelayed = counters.get("errors_corrected_by_eccdelayed", 0)
                rereads = counters.get("errors_corrected_by_rereads_rewrites", 0)
                algorithm_invocations = counters.get("correction_algorithm_invocations", 0)
                
                # Uncorrected errors
                if uncorrected > 0:
                    param_key = f"{operation}_uncorrected_errors_abs"
                    levels_param = params.get(param_key)
                    
                    # SimpleLevels already produces ("fixed", (warn, crit)) format directly
                    if levels_param is None:
                        # Default behavior - any uncorrected errors are critical
                        levels_param = ("fixed", (1, 1))
                    
                    yield from check_levels(
                        uncorrected,
                        levels_upper=levels_param,
                        label=f"{operation.capitalize()} uncorrected errors",
                        render_func=_render_error_count,
                    )
                
                # ECC fast errors
                if eccfast > 0:
                    param_key = f"{operation}_eccfast_errors_abs"
                    levels_param = params.get(param_key)
                    
                    if levels_param is not None:
                        # SimpleLevels already produces ("fixed", (warn, crit)) format directly
                        yield from check_levels(
                            eccfast,
                            levels_upper=levels_param,
                            label=f"{operation.capitalize()} ECC fast errors",
                            render_func=_render_error_count,
                        )
                    else:
                        # No threshold configured - just report the value
                        yield Result(state=State.OK, summary=f"{operation.capitalize()} ECC fast: {eccfast}")
                
                # ECC delayed errors
                if eccdelayed > 0:
                    param_key = f"{operation}_eccdelayed_errors_abs"
                    levels_param = params.get(param_key)
                    
                    if levels_param is not None:
                        # SimpleLevels already produces ("fixed", (warn, crit)) format directly
                        yield from check_levels(
                            eccdelayed,
                            levels_upper=levels_param,
                            label=f"{operation.capitalize()} ECC delayed errors",
                            render_func=_render_error_count,
                        )
                    else:
                        # No threshold configured - just report the value
                        yield Result(state=State.OK, summary=f"{operation.capitalize()} ECC delayed: {eccdelayed}")
                
                # Rereads/rewrites errors
                if rereads > 0:
                    param_key = f"{operation}_rereads_rewrites_errors_abs"
                    levels_param = params.get(param_key)
                    
                    if levels_param is not None:
                        # SimpleLevels already produces ("fixed", (warn, crit)) format directly
                        yield from check_levels(
                            rereads,
                            levels_upper=levels_param,
                            label=f"{operation.capitalize()} rereads/rewrites errors",
                            render_func=_render_error_count,
                        )
                    else:
                        # No threshold configured - just report the value
                        yield Result(state=State.OK, summary=f"{operation.capitalize()} rereads/rewrites: {rereads}")
                
                # Algorithm invocations (only if configured)
                if algorithm_invocations > 0:
                    param_key = f"{operation}_algorithm_invocations_abs"
                    levels_param = params.get(param_key)
                    
                    if levels_param is not None:
                        # SimpleLevels already produces ("fixed", (warn, crit)) format directly
                        yield from check_levels(
                            algorithm_invocations,
                            levels_upper=levels_param,
                            label=f"{operation.capitalize()} algorithm invocations",
                            render_func=_render_error_count,
                        )
                    # If no levels configured, don't report algorithm invocations
    
    # Show operation-specific processed bytes
    if read_processed_gb > 0:
        yield Result(state=State.OK, summary=f"Read: {render.bytes(read_processed_gb * 1024**3)} processed")
    if write_processed_gb > 0:
        yield Result(state=State.OK, summary=f"Write: {render.bytes(write_processed_gb * 1024**3)} processed")
    if verify_processed_gb > 0:
        yield Result(state=State.OK, summary=f"Verify: {render.bytes(verify_processed_gb * 1024**3)} processed")


# Register the section and check plugin
agent_section_oposs_smart_error = AgentSection(
    name="oposs_smart_error",
    parse_function=parse_oposs_smart_error,
)

check_plugin_oposs_smart_error = CheckPlugin(
    name="oposs_smart_error",
    service_name="SMART Errors %s",
    discovery_function=discover_oposs_smart_error,
    check_function=check_oposs_smart_error,
    check_ruleset_name="oposs_smart_error",
    check_default_parameters={},
)


# Background medium scan (BMS): SAS drives read their whole surface on their
# own while idle. The check below reports how often that happens and what
# the scans found. See SBC-3, background scan results log page and mode
# page 0x1c/1.

BMS_STATUS = {
    0: "no scans active",
    1: "scan is active",
    2: "pre-scan is active",
    3: "halted due to fatal error",
    4: "halted due to a vendor specific pattern of error",
    5: "halted due to medium formatted without P-List",
    6: "halted - vendor specific cause",
    7: "halted due to temperature out of range",
    8: "waiting until BMS interval timer expires",
}

# Fixed states per status; status 0 comes from the "state_no_scan" parameter
BMS_STATUS_STATE = {
    1: State.OK,
    2: State.OK,
    3: State.CRIT,
    4: State.CRIT,
    5: State.WARN,
    6: State.WARN,
    7: State.WARN,
    8: State.OK,
}

# Reassign status values that mean the drive fixed the sector with its data
# intact. Everything else (needs a write, reassignment failed, data lost,
# reserved values) counts as unrecovered.
BMS_RECOVERED = {
    2: "successfully reassigned",
    5: "recovered via rewrite in-place",
    6: "reassigned by application, data valid",
}

BMS_DEFAULT_PARAMETERS = {
    "last_scan_age": ("fixed", (90 * 86400.0, 365 * 86400.0)),
    "recent_window": 7 * 86400.0,
    "state_no_scan": 1,
    "state_recent_unrecovered": 2,
    "state_recent_recovered": 1,
    "state_old_errors": 0,
}


def parse_bms_mode_page(raw_hex: str) -> Optional[Dict[str, Any]]:
    """Decode a MODE SENSE(10) response holding the Background Control page"""
    try:
        raw = bytes.fromhex(raw_hex)
    except ValueError:
        return None
    if len(raw) < 8:
        return None
    page = raw[8 + int.from_bytes(raw[6:8], "big"):]
    if len(page) < 14 or page[0] & 0x3F != 0x1C or not page[0] & 0x40 or page[1] != 0x01:
        return None
    return {
        "enabled": bool(page[4] & 0x01),
        "prescan": bool(page[5] & 0x01),
        "interval_hours": int.from_bytes(page[6:8], "big"),
        "prescan_limit_hours": int.from_bytes(page[8:10], "big"),
        "min_idle_ms": int.from_bytes(page[10:12], "big"),
        "max_suspend_ms": int.from_bytes(page[12:14], "big"),
    }


def _render_poh(minutes: int) -> str:
    """Render a drive power-on timestamp the way smartctl prints it"""
    return f"{minutes // 60}:{minutes % 60:02d} h"


def discover_oposs_smart_bms(section: Section) -> DiscoveryResult:
    """One service per drive that keeps a background scan results log"""
    for device_name, data in section.items():
        if "error" not in data and isinstance(data.get("background_scan", {}).get("status"), dict):
            yield Service(item=_service_item(device_name, data))


def _check_bms_age(
    scans: int, poh: int, params: Mapping[str, Any], value_store: Dict[str, Any]
) -> CheckResult:
    """Time since the scan counter last went up, in drive power-on time.

    The drive does not log when a scan finished, so the check remembers the
    power-on time at which it saw the counter change. Until it has seen one
    change, the age is only a lower bound.
    """
    last = value_store.get("last_scan")
    if last is None or scans < last["scans"]:
        last = {"scans": scans, "poh": poh, "known": False}
    elif scans > last["scans"]:
        last = {"scans": scans, "poh": poh, "known": True}
    value_store["last_scan"] = last

    label = "Time since last completed scan"
    if not last["known"]:
        label += " (at least, counted since first seen)"
    yield from check_levels(
        max(poh - last["poh"], 0) * 60,
        levels_upper=params.get("last_scan_age"),
        metric_name="oposs_smart_bms_last_scan_age",
        label=label,
        render_func=render.timespan,
    )


def _check_bms_results(scan: Dict[str, Any], poh: Optional[int], params: Mapping[str, Any]) -> CheckResult:
    """Medium errors the background scan has logged"""
    entries = sorted(
        (v for k, v in scan.items() if k.startswith("result_") and isinstance(v, dict)),
        key=lambda e: (e.get("accumulated_power_on", {}).get("minutes", 0), e.get("parameter_code", 0)),
    )
    yield Metric("oposs_smart_bms_medium_errors", len(entries))
    if not entries:
        yield Result(state=State.OK, notice="No medium errors logged by background scan")
        return

    window_min = params["recent_window"] / 60
    groups: Dict[str, List[str]] = {"recent_unrecovered": [], "recent_recovered": [], "old": []}
    for entry in entries:
        when = entry.get("accumulated_power_on", {}).get("minutes", 0)
        reassign = entry.get("reassign_status", {}).get("value", 0)
        sense = entry.get("sense_key", {}).get("string", "?")
        reassign_text = BMS_RECOVERED.get(reassign) or entry.get("reassign_status", {}).get(
            "string", f"reassign status {reassign}")
        line = (f"LBA 0x{entry.get('lba', 0):x} at {_render_poh(when)}: {sense} "
                f"[asc 0x{entry.get('asc', 0):02x}, ascq 0x{entry.get('ascq', 0):02x}], {reassign_text}")
        if poh is not None and poh - when <= window_min:
            groups["recent_recovered" if reassign in BMS_RECOVERED else "recent_unrecovered"].append(line)
        else:
            groups["old"].append(line)

    window = render.timespan(params["recent_window"])
    for key, text in (
        ("recent_unrecovered", f"unrecovered medium error(s) in the last {window}"),
        ("recent_recovered", f"recovered medium error(s) in the last {window}"),
        ("old", "older medium error(s) logged by background scan"),
    ):
        lines = groups[key]
        if lines:
            yield Result(
                state=State(params[f"state_{key}" if key != "old" else "state_old_errors"]),
                summary=f"{len(lines)} {text}",
                details="\n".join(lines),
            )


def _check_bms(
    item: str, params: Mapping[str, Any], section: Section, value_store: Dict[str, Any]
) -> CheckResult:
    device_name = _device_from_item(item)
    data = section.get(device_name)
    if data is None:
        yield Result(state=State.UNKNOWN, summary=f"Device {device_name} not found")
        return
    scan = data.get("background_scan", {})
    status = scan.get("status")
    if not isinstance(status, dict):
        yield Result(state=State.UNKNOWN, summary="No background scan data")
        return

    value = status.get("value")
    try:
        progress: Optional[float] = float(str(status.get("scan_progress", "0")).rstrip("%") or 0)
    except ValueError:
        progress = None
    text = BMS_STATUS.get(value, f"unknown status {value}")
    if value == 0:
        state = State(params["state_no_scan"])
    else:
        state = BMS_STATUS_STATE.get(value, State.UNKNOWN)
    if value in (1, 2) and progress is not None:
        text += f" ({progress:.2f}%)"
    yield Result(state=state, summary=f"Status: {text}")
    if progress is not None:
        yield Metric("oposs_smart_bms_scan_progress", progress, boundaries=(0, 100))

    scans = status.get("number_scans_performed", 0)
    poh = data.get("power_on_minutes")
    yield Result(state=State.OK, notice=f"Scans performed: {scans}")
    yield Metric("oposs_smart_bms_scans_performed", scans)
    if poh is not None:
        if scans > 0:
            interval = poh * 60 / scans
            yield Result(state=State.OK, notice=f"Lifetime average: one scan every {render.timespan(interval)}")
            yield Metric("oposs_smart_bms_lifetime_scan_interval", interval)
        yield from _check_bms_age(scans, poh, params, value_store)

    yield from _check_bms_results(scan, poh, params)

    page = parse_bms_mode_page(data.get("bms_mode_page", ""))
    if page:
        yield Result(
            state=State.OK,
            notice=(f"BMS {'enabled' if page['enabled'] else 'disabled'}, "
                    f"interval {page['interval_hours']} h, "
                    f"pre-scan {'on' if page['prescan'] else 'off'}, "
                    f"minimum idle before scan {page['min_idle_ms']} ms"),
        )


def check_oposs_smart_bms(item: str, params: Mapping[str, Any], section: Section) -> CheckResult:
    """Check background medium scan status, frequency and findings"""
    yield from _check_bms(item, params, section, get_value_store())


check_plugin_oposs_smart_bms = CheckPlugin(
    name="oposs_smart_bms",
    service_name="SMART Background Scan %s",
    sections=["oposs_smart_error"],
    discovery_function=discover_oposs_smart_bms,
    check_function=check_oposs_smart_bms,
    check_ruleset_name="oposs_smart_bms",
    check_default_parameters=BMS_DEFAULT_PARAMETERS,
)