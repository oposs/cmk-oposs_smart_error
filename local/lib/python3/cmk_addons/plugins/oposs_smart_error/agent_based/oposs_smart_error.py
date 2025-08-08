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
        # Extract device name from path (e.g., sda from /dev/sda)
        device_name = device_path.split('/')[-1] if '/' in device_path else device_path
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


def discover_oposs_smart_error(section: Section) -> DiscoveryResult:
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


def check_oposs_smart_error(item: str, params: Mapping[str, Any], section: Section) -> CheckResult:
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
        yield Metric(f"{operation}_errors_corrected_by_eccfast", eccfast)
        yield Metric(f"{operation}_errors_corrected_by_eccdelayed", eccdelayed)
        yield Metric(f"{operation}_errors_corrected_by_rereads_rewrites", rereads)
        yield Metric(f"{operation}_correction_algorithm_invocations", algorithm_invocations)
        yield Metric(f"{operation}_bytes_processed", processed_bytes)
        yield Metric(f"{operation}_total_uncorrected_errors", uncorrected)
        
        # Generate detailed relative metrics per TB (4 values - excluding uncorrected errors)
        if processed_gb > 0:
            processed_tb = processed_gb / 1024  # Convert GB to TB
            yield Metric(f"{operation}_errors_corrected_by_eccfast_per_tb", eccfast / processed_tb)
            yield Metric(f"{operation}_errors_corrected_by_eccdelayed_per_tb", eccdelayed / processed_tb)
            yield Metric(f"{operation}_errors_corrected_by_rereads_rewrites_per_tb", rereads / processed_tb)
            yield Metric(f"{operation}_correction_algorithm_invocations_per_tb", algorithm_invocations / processed_tb)
    
    
    # Device info summary
    yield Result(state=State.OK, summary=device_desc)
    
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
                    
                    # Handle SimpleLevels format from rulesets
                    if levels_param and isinstance(levels_param, dict) and 'levels_upper' in levels_param:
                        levels_upper = ("fixed", levels_param['levels_upper'])
                    else:
                        # Default behavior - any uncorrected errors are critical
                        levels_upper = ("fixed", (1, 1)) 
                    
                    yield from check_levels(
                        uncorrected,
                        levels_upper=levels_upper,
                        metric_name=f"{operation}_uncorrected_check",
                        label=f"{operation.capitalize()} uncorrected errors",
                        render_func=_render_error_count,
                    )
                
                # ECC fast errors
                if eccfast > 0:
                    param_key = f"{operation}_eccfast_errors_abs"
                    levels_param = params.get(param_key)
                    
                    if levels_param and isinstance(levels_param, dict) and 'levels_upper' in levels_param:
                        yield from check_levels(
                            eccfast,
                            levels_upper=("fixed", levels_param['levels_upper']),
                            metric_name=f"{operation}_eccfast_check",
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
                    
                    if levels_param and isinstance(levels_param, dict) and 'levels_upper' in levels_param:
                        yield from check_levels(
                            eccdelayed,
                            levels_upper=("fixed", levels_param['levels_upper']),
                            metric_name=f"{operation}_eccdelayed_check",
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
                    
                    if levels_param and isinstance(levels_param, dict) and 'levels_upper' in levels_param:
                        yield from check_levels(
                            rereads,
                            levels_upper=("fixed", levels_param['levels_upper']),
                            metric_name=f"{operation}_rereads_rewrites_check",
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
                    
                    if levels_param and isinstance(levels_param, dict) and 'levels_upper' in levels_param:
                        yield from check_levels(
                            algorithm_invocations,
                            levels_upper=("fixed", levels_param['levels_upper']),
                            metric_name=f"{operation}_algorithm_invocations_check",
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