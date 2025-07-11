#!/usr/bin/env python3
"""
CheckMK Metrics and Graph Definitions for SMART Error Monitoring
Defines 6 combined graphs showing absolute and relative error metrics
Compatible with CheckMK 2.3
"""

from cmk.gui.i18n import _
from cmk.gui.plugins.metrics import (
    graph_info,
    metric_info,
    perfometer_info,
)

# Detailed metric definitions for READ operations
metric_info["read_errors_corrected_by_eccfast"] = {
    "title": _("Read Errors Corrected by ECC Fast"),
    "unit": "count",
    "color": "11/a",  # Blue
}

metric_info["read_errors_corrected_by_eccdelayed"] = {
    "title": _("Read Errors Corrected by ECC Delayed"),
    "unit": "count",
    "color": "12/a",  # Green
}

metric_info["read_errors_corrected_by_rereads_rewrites"] = {
    "title": _("Read Errors Corrected by Rereads/Rewrites"),
    "unit": "count",
    "color": "13/a",  # Orange
}

metric_info["read_correction_algorithm_invocations"] = {
    "title": _("Read Correction Algorithm Invocations"),
    "unit": "count",
    "color": "14/a",  # Purple
}

metric_info["read_bytes_processed"] = {
    "title": _("Read Bytes Processed"),
    "unit": "bytes",
    "color": "15/a",  # Yellow
}

metric_info["read_total_uncorrected_errors"] = {
    "title": _("Read Total Uncorrected Errors"),
    "unit": "count",
    "color": "16/a",  # Red
}

# Detailed metric definitions for WRITE operations
metric_info["write_errors_corrected_by_eccfast"] = {
    "title": _("Write Errors Corrected by ECC Fast"),
    "unit": "count",
    "color": "21/a",  # Light Blue
}

metric_info["write_errors_corrected_by_eccdelayed"] = {
    "title": _("Write Errors Corrected by ECC Delayed"),
    "unit": "count",
    "color": "22/a",  # Light Green
}

metric_info["write_errors_corrected_by_rereads_rewrites"] = {
    "title": _("Write Errors Corrected by Rereads/Rewrites"),
    "unit": "count",
    "color": "23/a",  # Light Orange
}

metric_info["write_correction_algorithm_invocations"] = {
    "title": _("Write Correction Algorithm Invocations"),
    "unit": "count",
    "color": "24/a",  # Light Purple
}

metric_info["write_bytes_processed"] = {
    "title": _("Write Bytes Processed"),
    "unit": "bytes",
    "color": "25/a",  # Light Yellow
}

metric_info["write_total_uncorrected_errors"] = {
    "title": _("Write Total Uncorrected Errors"),
    "unit": "count",
    "color": "26/a",  # Light Red
}

# Detailed metric definitions for VERIFY operations
metric_info["verify_errors_corrected_by_eccfast"] = {
    "title": _("Verify Errors Corrected by ECC Fast"),
    "unit": "count",
    "color": "31/a",  # Dark Blue
}

metric_info["verify_errors_corrected_by_eccdelayed"] = {
    "title": _("Verify Errors Corrected by ECC Delayed"),
    "unit": "count",
    "color": "32/a",  # Dark Green
}

metric_info["verify_errors_corrected_by_rereads_rewrites"] = {
    "title": _("Verify Errors Corrected by Rereads/Rewrites"),
    "unit": "count",
    "color": "33/a",  # Dark Orange
}

metric_info["verify_correction_algorithm_invocations"] = {
    "title": _("Verify Correction Algorithm Invocations"),
    "unit": "count",
    "color": "34/a",  # Dark Purple
}

metric_info["verify_bytes_processed"] = {
    "title": _("Verify Bytes Processed"),
    "unit": "bytes",
    "color": "35/a",  # Dark Yellow
}

metric_info["verify_total_uncorrected_errors"] = {
    "title": _("Verify Total Uncorrected Errors"),
    "unit": "count",
    "color": "36/a",  # Dark Red
}

# Detailed rate metrics for READ operations (per TB)
metric_info["read_errors_corrected_by_eccfast_per_tb"] = {
    "title": _("Read ECC Fast Errors per TB"),
    "unit": "count",
    "color": "11/b",  # Blue variant
}

metric_info["read_errors_corrected_by_eccdelayed_per_tb"] = {
    "title": _("Read ECC Delayed Errors per TB"),
    "unit": "count",
    "color": "12/b",  # Green variant
}

metric_info["read_errors_corrected_by_rereads_rewrites_per_tb"] = {
    "title": _("Read Rereads/Rewrites Errors per TB"),
    "unit": "count",
    "color": "13/b",  # Orange variant
}

metric_info["read_correction_algorithm_invocations_per_tb"] = {
    "title": _("Read Algorithm Invocations per TB"),
    "unit": "count",
    "color": "14/b",  # Purple variant
}


# Detailed rate metrics for WRITE operations (per TB)
metric_info["write_errors_corrected_by_eccfast_per_tb"] = {
    "title": _("Write ECC Fast Errors per TB"),
    "unit": "count",
    "color": "21/b",  # Light Blue variant
}

metric_info["write_errors_corrected_by_eccdelayed_per_tb"] = {
    "title": _("Write ECC Delayed Errors per TB"),
    "unit": "count",
    "color": "22/b",  # Light Green variant
}

metric_info["write_errors_corrected_by_rereads_rewrites_per_tb"] = {
    "title": _("Write Rereads/Rewrites Errors per TB"),
    "unit": "count",
    "color": "23/b",  # Light Orange variant
}

metric_info["write_correction_algorithm_invocations_per_tb"] = {
    "title": _("Write Algorithm Invocations per TB"),
    "unit": "count",
    "color": "24/b",  # Light Purple variant
}


# Detailed rate metrics for VERIFY operations (per TB)
metric_info["verify_errors_corrected_by_eccfast_per_tb"] = {
    "title": _("Verify ECC Fast Errors per TB"),
    "unit": "count",
    "color": "31/b",  # Dark Blue variant
}

metric_info["verify_errors_corrected_by_eccdelayed_per_tb"] = {
    "title": _("Verify ECC Delayed Errors per TB"),
    "unit": "count",
    "color": "32/b",  # Dark Green variant
}

metric_info["verify_errors_corrected_by_rereads_rewrites_per_tb"] = {
    "title": _("Verify Rereads/Rewrites Errors per TB"),
    "unit": "count",
    "color": "33/b",  # Dark Orange variant
}

metric_info["verify_correction_algorithm_invocations_per_tb"] = {
    "title": _("Verify Algorithm Invocations per TB"),
    "unit": "count",
    "color": "34/b",  # Dark Purple variant
}



# Graph definitions - 6 combined graphs with detailed metrics

# 1. Read Operation - Absolute Values (5 lines)
graph_info["oposs_smart_error_read_absolute"] = {
    "title": _("SMART Read Operations - Error Counts"),
    "metrics": [
        ("read_errors_corrected_by_eccfast", "line"),
        ("read_errors_corrected_by_eccdelayed", "line"),
        ("read_errors_corrected_by_rereads_rewrites", "line"),
        ("read_correction_algorithm_invocations", "line"),
        ("read_total_uncorrected_errors", "line"),
    ],
}

# 2. Write Operation - Absolute Values (5 lines)
graph_info["oposs_smart_error_write_absolute"] = {
    "title": _("SMART Write Operations - Error Counts"),
    "metrics": [
        ("write_errors_corrected_by_eccfast", "line"),
        ("write_errors_corrected_by_eccdelayed", "line"),
        ("write_errors_corrected_by_rereads_rewrites", "line"),
        ("write_correction_algorithm_invocations", "line"),
        ("write_total_uncorrected_errors", "line"),
    ],
}

# 3. Verify Operation - Absolute Values (5 lines)
graph_info["oposs_smart_error_verify_absolute"] = {
    "title": _("SMART Verify Operations - Error Counts"),
    "metrics": [
        ("verify_errors_corrected_by_eccfast", "line"),
        ("verify_errors_corrected_by_eccdelayed", "line"),
        ("verify_errors_corrected_by_rereads_rewrites", "line"),
        ("verify_correction_algorithm_invocations", "line"),
        ("verify_total_uncorrected_errors", "line"),
    ],
}

# 4. Read Operation - Relative Values per TB (4 lines)
graph_info["oposs_smart_error_read_relative"] = {
    "title": _("SMART Read Operations - Relative Values (per TB)"),
    "metrics": [
        ("read_errors_corrected_by_eccfast_per_tb", "line"),
        ("read_errors_corrected_by_eccdelayed_per_tb", "line"),
        ("read_errors_corrected_by_rereads_rewrites_per_tb", "line"),
        ("read_correction_algorithm_invocations_per_tb", "line"),
    ],
}

# 5. Write Operation - Relative Values per TB (4 lines)
graph_info["oposs_smart_error_write_relative"] = {
    "title": _("SMART Write Operations - Relative Values (per TB)"),
    "metrics": [
        ("write_errors_corrected_by_eccfast_per_tb", "line"),
        ("write_errors_corrected_by_eccdelayed_per_tb", "line"),
        ("write_errors_corrected_by_rereads_rewrites_per_tb", "line"),
        ("write_correction_algorithm_invocations_per_tb", "line"),
    ],
}

# 6. Verify Operation - Relative Values per TB (4 lines)
graph_info["oposs_smart_error_verify_relative"] = {
    "title": _("SMART Verify Operations - Relative Values (per TB)"),
    "metrics": [
        ("verify_errors_corrected_by_eccfast_per_tb", "line"),
        ("verify_errors_corrected_by_eccdelayed_per_tb", "line"),
        ("verify_errors_corrected_by_rereads_rewrites_per_tb", "line"),
        ("verify_correction_algorithm_invocations_per_tb", "line"),
    ],
}

# Bytes processed stacked graph - shows cumulative storage activity
graph_info["oposs_smart_error_bytes_processed"] = {
    "title": _("SMART Operations - Bytes Processed"),
    "metrics": [
        ("read_bytes_processed", "stack"),
        ("write_bytes_processed", "stack"),
        ("verify_bytes_processed", "stack"),
    ],
}

# Perfometer for service overview - using individual operation uncorrected errors
perfometer_info.append({
    "type": "linear",
    "segments": [
        "read_total_uncorrected_errors",
        "write_total_uncorrected_errors", 
        "verify_total_uncorrected_errors",
    ],
    "total": 100,
})