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
)


Section = Dict[str, Dict[str, Any]]


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
        # Extract device name from path (e.g., sda from /dev/sda)
        device_name = device_path.split('/')[-1] if '/' in device_path else device_path
        return f"{' '.join(parts)} ({device_name})"
    else:
        return device_path


def parse_smart_errors(string_table: StringTable) -> Section:
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


def discover_smart_errors(section: Section) -> DiscoveryResult:
    """Discover SMART error services"""
    for device_name, data in section.items():
        if "error" not in data:
            # Always create service item with device name and serial number for unique identification
            serial = data.get("serial", "")
            if serial:
                # Use last 8 chars of serial for uniqueness
                serial_short = serial[-8:] if len(serial) > 8 else serial
                service_item = f"{device_name} ({serial_short})"
            else:
                # Fallback to device name with "no-serial" if no serial available
                service_item = f"{device_name} (no-serial)"
            yield Service(item=service_item)


def check_smart_errors(item: str, params: Mapping[str, Any], section: Section) -> CheckResult:
    """Check SMART error counters and generate metrics"""
    # Extract device name from service item format: "/dev/sda (serial)"
    if " (" in item and item.endswith(")"):
        device_name = item.split(" (")[0].strip()
    else:
        # Should not happen with current discovery logic, but handle gracefully
        device_name = item.strip()
    
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
    total_corrected = 0
    total_uncorrected = 0
    total_processed_gb = 0.0
    
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
        
        # Update totals for summary
        total_corrected += corrected
        total_uncorrected += uncorrected
        total_processed_gb += processed_gb
        
        # Generate detailed absolute metrics (6 values - excluding redundant total_errors_corrected)
        yield Metric(f"{operation}_errors_corrected_by_eccfast", eccfast)
        yield Metric(f"{operation}_errors_corrected_by_eccdelayed", eccdelayed)
        yield Metric(f"{operation}_errors_corrected_by_rereads_rewrites", rereads)
        yield Metric(f"{operation}_correction_algorithm_invocations", algorithm_invocations)
        yield Metric(f"{operation}_bytes_processed", processed_bytes)
        yield Metric(f"{operation}_total_uncorrected_errors", uncorrected)
        
        # Generate detailed relative metrics per TB (5 values - excluding redundant total_errors_corrected)
        if processed_gb > 0:
            processed_tb = processed_gb / 1024  # Convert GB to TB
            yield Metric(f"{operation}_errors_corrected_by_eccfast_per_tb", eccfast / processed_tb)
            yield Metric(f"{operation}_errors_corrected_by_eccdelayed_per_tb", eccdelayed / processed_tb)
            yield Metric(f"{operation}_errors_corrected_by_rereads_rewrites_per_tb", rereads / processed_tb)
            yield Metric(f"{operation}_correction_algorithm_invocations_per_tb", algorithm_invocations / processed_tb)
            yield Metric(f"{operation}_total_uncorrected_errors_per_tb", uncorrected / processed_tb)
    
    # Generate only bytes processed summary metric (error summaries are redundant)
    yield Metric("total_bytes_processed", total_processed_gb * (1024 ** 3))
    
    # Determine service state based on operation-specific counter thresholds
    state = State.OK
    summary_parts = []
    
    # Check operation-specific thresholds for each error type
    for operation in ["read", "write", "verify"]:
        if operation not in error_counters:
            continue
        
        op_data = error_counters[operation]
        uncorrected = op_data.get("total_uncorrected_errors", 0)
        eccfast = op_data.get("errors_corrected_by_eccfast", 0)
        eccdelayed = op_data.get("errors_corrected_by_eccdelayed", 0)
        rereads = op_data.get("errors_corrected_by_rereads_rewrites", 0)
        algorithm_invocations = op_data.get("correction_algorithm_invocations", 0)
        
        # Check uncorrected errors for this operation
        param_key = f"{operation}_uncorrected_errors_abs"
        if param_key in params:
            levels = params[param_key]
            if isinstance(levels, tuple) and len(levels) == 2:
                warn, crit = levels
                if uncorrected >= crit:
                    state = max(state, State.CRIT)
                elif uncorrected >= warn:
                    state = max(state, State.WARN)
        else:
            # Default behavior - any uncorrected errors are critical
            if uncorrected > 0:
                state = max(state, State.CRIT)
        
        # Check ECC fast errors for this operation
        param_key = f"{operation}_eccfast_errors_abs"
        if param_key in params:
            levels = params[param_key]
            if isinstance(levels, tuple) and len(levels) == 2:
                warn, crit = levels
                if eccfast >= crit:
                    state = max(state, State.CRIT)
                elif eccfast >= warn:
                    state = max(state, State.WARN)
        
        # Check ECC delayed errors for this operation
        param_key = f"{operation}_eccdelayed_errors_abs"
        if param_key in params:
            levels = params[param_key]
            if isinstance(levels, tuple) and len(levels) == 2:
                warn, crit = levels
                if eccdelayed >= crit:
                    state = max(state, State.CRIT)
                elif eccdelayed >= warn:
                    state = max(state, State.WARN)
        
        # Check rereads/rewrites errors for this operation
        param_key = f"{operation}_rereads_rewrites_errors_abs"
        if param_key in params:
            levels = params[param_key]
            if isinstance(levels, tuple) and len(levels) == 2:
                warn, crit = levels
                if rereads >= crit:
                    state = max(state, State.CRIT)
                elif rereads >= warn:
                    state = max(state, State.WARN)
        
        # Check algorithm invocations for this operation
        param_key = f"{operation}_algorithm_invocations_abs"
        if param_key in params:
            levels = params[param_key]
            if isinstance(levels, tuple) and len(levels) == 2:
                warn, crit = levels
                if algorithm_invocations >= crit:
                    state = max(state, State.CRIT)
                elif algorithm_invocations >= warn:
                    state = max(state, State.WARN)
    
    # Check rate-based thresholds
    if total_processed_gb > 0:
        total_processed_tb = total_processed_gb / 1024  # Convert GB to TB
        total_uncorrected_rate = total_uncorrected / total_processed_tb
        
        if "uncorrected_errors_per_tb" in params:
            levels = params["uncorrected_errors_per_tb"]
            if isinstance(levels, tuple) and len(levels) == 2:
                warn, crit = levels
                if total_uncorrected_rate >= crit:
                    state = max(state, State.CRIT)
                elif total_uncorrected_rate >= warn:
                    state = max(state, State.WARN)
    
    # Calculate totals for summary by error type
    total_eccfast = 0
    total_eccdelayed = 0
    total_rereads = 0
    
    for operation, counters in error_counters.items():
        if not isinstance(counters, dict):
            continue
        total_eccfast += counters.get("errors_corrected_by_eccfast", 0)
        total_eccdelayed += counters.get("errors_corrected_by_eccdelayed", 0)
        total_rereads += counters.get("errors_corrected_by_rereads_rewrites", 0)
    
    # Build summary with specific error types
    if total_uncorrected > 0:
        summary_parts.append(f"{total_uncorrected} uncorrected errors")
    
    # Show breakdown of correction types if any exist
    correction_parts = []
    if total_eccfast > 0:
        correction_parts.append(f"{total_eccfast} ECC fast")
    if total_eccdelayed > 0:
        correction_parts.append(f"{total_eccdelayed} ECC delayed")
    if total_rereads > 0:
        correction_parts.append(f"{total_rereads} rereads/rewrites")
    
    if correction_parts:
        summary_parts.append(f"Corrected: {', '.join(correction_parts)}")
    
    if not summary_parts:
        summary_parts.append("No errors detected")
    
    if total_processed_gb > 0:
        summary_parts.append(f"{render.bytes(total_processed_gb * 1024**3)} processed")
    
    summary = f"{device_desc}: {', '.join(summary_parts)}"
    
    yield Result(state=state, summary=summary)


# Register the section and check plugin
agent_section_smart_errors = AgentSection(
    name="smart_errors",
    parse_function=parse_smart_errors,
)

check_plugin_smart_errors = CheckPlugin(
    name="smart_errors",
    service_name="SMART Errors %s",
    discovery_function=discover_smart_errors,
    check_function=check_smart_errors,
    check_ruleset_name="smart_errors",
    check_default_parameters={},
)