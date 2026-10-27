#!/usr/bin/env python3
"""
Metric translations for SMART Error Monitoring

Up to version 1.0.5 the error counter metrics had no plugin prefix
(read_bytes_processed, ...). These translations show the history recorded
under the old names in the graphs of the new, prefixed metrics.
"""

from cmk.graphing.v1 import translations

_OPERATIONS = ("read", "write", "verify")
_COUNTERS = (
    "errors_corrected_by_eccfast",
    "errors_corrected_by_eccdelayed",
    "errors_corrected_by_rereads_rewrites",
    "correction_algorithm_invocations",
    "bytes_processed",
    "total_uncorrected_errors",
    "errors_corrected_by_eccfast_per_tb",
    "errors_corrected_by_eccdelayed_per_tb",
    "errors_corrected_by_rereads_rewrites_per_tb",
    "correction_algorithm_invocations_per_tb",
)

# Keyed on the check command the services run today; the check name did not change.
translation_oposs_smart_error = translations.Translation(
    name="oposs_smart_error_unprefixed_metrics",
    check_commands=[translations.PassiveCheck("oposs_smart_error")],
    translations={
        f"{op}_{counter}": translations.RenameTo(f"oposs_smart_error_{op}_{counter}")
        for op in _OPERATIONS
        for counter in _COUNTERS
    },
)
