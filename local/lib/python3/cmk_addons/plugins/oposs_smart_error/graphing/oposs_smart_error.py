#!/usr/bin/env python3
"""
CheckMK Metrics and Graph Definitions for SMART Error Monitoring
Defines 6 combined graphs showing absolute and relative error metrics
Compatible with CheckMK 2.3
"""


from cmk.graphing.v1 import Title
from cmk.graphing.v1.metrics import (
    Color,
    DecimalNotation,
    IECNotation,
    Metric,
    Unit,
)
from cmk.graphing.v1.graphs import (
    Graph,
    MinimalRange,
)
from cmk.graphing.v1.perfometers import (
    Perfometer,
    FocusRange,
    Closed,
)

# Define units
unit_count = Unit(DecimalNotation(""))
unit_bytes = Unit(IECNotation("B"))

# Detailed metric definitions for READ operations
metric_read_errors_corrected_by_eccfast = Metric(
    name="read_errors_corrected_by_eccfast",
    title=Title("Read Errors Corrected by ECC Fast"),
    unit=unit_count,
    color=Color.BLUE,
)

metric_read_errors_corrected_by_eccdelayed = Metric(
    name="read_errors_corrected_by_eccdelayed",
    title=Title("Read Errors Corrected by ECC Delayed"),
    unit=unit_count,
    color=Color.GREEN,
)

metric_read_errors_corrected_by_rereads_rewrites = Metric(
    name="read_errors_corrected_by_rereads_rewrites",
    title=Title("Read Errors Corrected by Rereads/Rewrites"),
    unit=unit_count,
    color=Color.ORANGE,
)

metric_read_correction_algorithm_invocations = Metric(
    name="read_correction_algorithm_invocations",
    title=Title("Read Correction Algorithm Invocations"),
    unit=unit_count,
    color=Color.PURPLE,
)

metric_read_bytes_processed = Metric(
    name="read_bytes_processed",
    title=Title("Read Bytes Processed"),
    unit=unit_bytes,
    color=Color.BLUE,
)

metric_read_total_uncorrected_errors = Metric(
    name="read_total_uncorrected_errors",
    title=Title("Read Total Uncorrected Errors"),
    unit=unit_count,
    color=Color.RED,
)

# Detailed metric definitions for WRITE operations
metric_write_errors_corrected_by_eccfast = Metric(
    name="write_errors_corrected_by_eccfast",
    title=Title("Write Errors Corrected by ECC Fast"),
    unit=unit_count,
    color=Color.LIGHT_BLUE,
)

metric_write_errors_corrected_by_eccdelayed = Metric(
    name="write_errors_corrected_by_eccdelayed",
    title=Title("Write Errors Corrected by ECC Delayed"),
    unit=unit_count,
    color=Color.LIGHT_GREEN,
)

metric_write_errors_corrected_by_rereads_rewrites = Metric(
    name="write_errors_corrected_by_rereads_rewrites",
    title=Title("Write Errors Corrected by Rereads/Rewrites"),
    unit=unit_count,
    color=Color.LIGHT_ORANGE,
)

metric_write_correction_algorithm_invocations = Metric(
    name="write_correction_algorithm_invocations",
    title=Title("Write Correction Algorithm Invocations"),
    unit=unit_count,
    color=Color.LIGHT_PURPLE,
)

metric_write_bytes_processed = Metric(
    name="write_bytes_processed",
    title=Title("Write Bytes Processed"),
    unit=unit_bytes,
    color=Color.GREEN,
)

metric_write_total_uncorrected_errors = Metric(
    name="write_total_uncorrected_errors",
    title=Title("Write Total Uncorrected Errors"),
    unit=unit_count,
    color=Color.LIGHT_RED,
)

# Detailed metric definitions for VERIFY operations
metric_verify_errors_corrected_by_eccfast = Metric(
    name="verify_errors_corrected_by_eccfast",
    title=Title("Verify Errors Corrected by ECC Fast"),
    unit=unit_count,
    color=Color.DARK_BLUE,
)

metric_verify_errors_corrected_by_eccdelayed = Metric(
    name="verify_errors_corrected_by_eccdelayed",
    title=Title("Verify Errors Corrected by ECC Delayed"),
    unit=unit_count,
    color=Color.DARK_GREEN,
)

metric_verify_errors_corrected_by_rereads_rewrites = Metric(
    name="verify_errors_corrected_by_rereads_rewrites",
    title=Title("Verify Errors Corrected by Rereads/Rewrites"),
    unit=unit_count,
    color=Color.DARK_ORANGE,
)

metric_verify_correction_algorithm_invocations = Metric(
    name="verify_correction_algorithm_invocations",
    title=Title("Verify Correction Algorithm Invocations"),
    unit=unit_count,
    color=Color.DARK_PURPLE,
)

metric_verify_bytes_processed = Metric(
    name="verify_bytes_processed",
    title=Title("Verify Bytes Processed"),
    unit=unit_bytes,
    color=Color.ORANGE,
)

metric_verify_total_uncorrected_errors = Metric(
    name="verify_total_uncorrected_errors",
    title=Title("Verify Total Uncorrected Errors"),
    unit=unit_count,
    color=Color.DARK_RED,
)

# Detailed rate metrics for READ operations (per TB)
metric_read_errors_corrected_by_eccfast_per_tb = Metric(
    name="read_errors_corrected_by_eccfast_per_tb",
    title=Title("Read ECC Fast Errors per TB"),
    unit=unit_count,
    color=Color.CYAN,
)

metric_read_errors_corrected_by_eccdelayed_per_tb = Metric(
    name="read_errors_corrected_by_eccdelayed_per_tb",
    title=Title("Read ECC Delayed Errors per TB"),
    unit=unit_count,
    color=Color.LIGHT_CYAN,
)

metric_read_errors_corrected_by_rereads_rewrites_per_tb = Metric(
    name="read_errors_corrected_by_rereads_rewrites_per_tb",
    title=Title("Read Rereads/Rewrites Errors per TB"),
    unit=unit_count,
    color=Color.PINK,
)

metric_read_correction_algorithm_invocations_per_tb = Metric(
    name="read_correction_algorithm_invocations_per_tb",
    title=Title("Read Algorithm Invocations per TB"),
    unit=unit_count,
    color=Color.LIGHT_PINK,
)

metric_read_total_uncorrected_errors_per_tb = Metric(
    name="read_total_uncorrected_errors_per_tb",
    title=Title("Read Uncorrected Errors per TB"),
    unit=unit_count,
    color=Color.DARK_RED,
)

# Detailed rate metrics for WRITE operations (per TB)
metric_write_errors_corrected_by_eccfast_per_tb = Metric(
    name="write_errors_corrected_by_eccfast_per_tb",
    title=Title("Write ECC Fast Errors per TB"),
    unit=unit_count,
    color=Color.BROWN,
)

metric_write_errors_corrected_by_eccdelayed_per_tb = Metric(
    name="write_errors_corrected_by_eccdelayed_per_tb",
    title=Title("Write ECC Delayed Errors per TB"),
    unit=unit_count,
    color=Color.LIGHT_BROWN,
)

metric_write_errors_corrected_by_rereads_rewrites_per_tb = Metric(
    name="write_errors_corrected_by_rereads_rewrites_per_tb",
    title=Title("Write Rereads/Rewrites Errors per TB"),
    unit=unit_count,
    color=Color.GRAY,
)

metric_write_correction_algorithm_invocations_per_tb = Metric(
    name="write_correction_algorithm_invocations_per_tb",
    title=Title("Write Algorithm Invocations per TB"),
    unit=unit_count,
    color=Color.LIGHT_GRAY,
)

metric_write_total_uncorrected_errors_per_tb = Metric(
    name="write_total_uncorrected_errors_per_tb",
    title=Title("Write Uncorrected Errors per TB"),
    unit=unit_count,
    color=Color.DARK_RED,
)

# Detailed rate metrics for VERIFY operations (per TB)
metric_verify_errors_corrected_by_eccfast_per_tb = Metric(
    name="verify_errors_corrected_by_eccfast_per_tb",
    title=Title("Verify ECC Fast Errors per TB"),
    unit=unit_count,
    color=Color.DARK_CYAN,
)

metric_verify_errors_corrected_by_eccdelayed_per_tb = Metric(
    name="verify_errors_corrected_by_eccdelayed_per_tb",
    title=Title("Verify ECC Delayed Errors per TB"),
    unit=unit_count,
    color=Color.DARK_PINK,
)

metric_verify_errors_corrected_by_rereads_rewrites_per_tb = Metric(
    name="verify_errors_corrected_by_rereads_rewrites_per_tb",
    title=Title("Verify Rereads/Rewrites Errors per TB"),
    unit=unit_count,
    color=Color.DARK_BROWN,
)

metric_verify_correction_algorithm_invocations_per_tb = Metric(
    name="verify_correction_algorithm_invocations_per_tb",
    title=Title("Verify Algorithm Invocations per TB"),
    unit=unit_count,
    color=Color.DARK_GRAY,
)

metric_verify_total_uncorrected_errors_per_tb = Metric(
    name="verify_total_uncorrected_errors_per_tb",
    title=Title("Verify Uncorrected Errors per TB"),
    unit=unit_count,
    color=Color.DARK_RED,
)

metric_total_bytes_processed = Metric(
    name="total_bytes_processed",
    title=Title("Total Bytes Processed"),
    unit=unit_bytes,
    color=Color.WHITE,
)

# Graph definitions - 6 combined graphs with detailed metrics

# 1. Read Operation - Absolute Values (5 lines)
graph_oposs_smart_error_read_absolute = Graph(
    name="oposs_smart_error_read_absolute",
    title=Title("SMART Read Operations - Error Counts"),
    minimal_range=MinimalRange(0, 100),
    simple_lines=[
        "read_errors_corrected_by_eccfast",
        "read_errors_corrected_by_eccdelayed",
        "read_errors_corrected_by_rereads_rewrites",
        "read_correction_algorithm_invocations",
        "read_total_uncorrected_errors",
    ],
)

# 2. Write Operation - Absolute Values (5 lines)
graph_oposs_smart_error_write_absolute = Graph(
    name="oposs_smart_error_write_absolute",
    title=Title("SMART Write Operations - Error Counts"),
    minimal_range=MinimalRange(0, 100),
    simple_lines=[
        "write_errors_corrected_by_eccfast",
        "write_errors_corrected_by_eccdelayed",
        "write_errors_corrected_by_rereads_rewrites",
        "write_correction_algorithm_invocations",
        "write_total_uncorrected_errors",
    ],
)

# 3. Verify Operation - Absolute Values (5 lines)
graph_oposs_smart_error_verify_absolute = Graph(
    name="oposs_smart_error_verify_absolute",
    title=Title("SMART Verify Operations - Error Counts"),
    minimal_range=MinimalRange(0, 100),
    simple_lines=[
        "verify_errors_corrected_by_eccfast",
        "verify_errors_corrected_by_eccdelayed",
        "verify_errors_corrected_by_rereads_rewrites",
        "verify_correction_algorithm_invocations",
        "verify_total_uncorrected_errors",
    ],
)

# 4. Read Operation - Relative Values per TB (4 lines)
graph_oposs_smart_error_read_relative = Graph(
    name="oposs_smart_error_read_relative",
    title=Title("SMART Read Operations - Relative Values (per TB)"),
    minimal_range=MinimalRange(0, 10),
    simple_lines=[
        "read_errors_corrected_by_eccfast_per_tb",
        "read_errors_corrected_by_eccdelayed_per_tb",
        "read_errors_corrected_by_rereads_rewrites_per_tb",
        "read_correction_algorithm_invocations_per_tb",
    ],
)

# 5. Write Operation - Relative Values per TB (4 lines)
graph_oposs_smart_error_write_relative = Graph(
    name="oposs_smart_error_write_relative",
    title=Title("SMART Write Operations - Relative Values (per TB)"),
    minimal_range=MinimalRange(0, 10),
    simple_lines=[
        "write_errors_corrected_by_eccfast_per_tb",
        "write_errors_corrected_by_eccdelayed_per_tb",
        "write_errors_corrected_by_rereads_rewrites_per_tb",
        "write_correction_algorithm_invocations_per_tb",
    ],
)

# 6. Verify Operation - Relative Values per TB (4 lines)
graph_oposs_smart_error_verify_relative = Graph(
    name="oposs_smart_error_verify_relative",
    title=Title("SMART Verify Operations - Relative Values (per TB)"),
    minimal_range=MinimalRange(0, 10),
    simple_lines=[
        "verify_errors_corrected_by_eccfast_per_tb",
        "verify_errors_corrected_by_eccdelayed_per_tb",
        "verify_errors_corrected_by_rereads_rewrites_per_tb",
        "verify_correction_algorithm_invocations_per_tb",
    ],
)

# Bytes processed stacked graph - shows cumulative storage activity
graph_oposs_smart_error_bytes_processed = Graph(
    name="oposs_smart_error_bytes_processed",
    title=Title("SMART Operations - Bytes Processed"),
    minimal_range=MinimalRange(0, 1000000000),
    simple_lines=[
        "read_bytes_processed",
        "write_bytes_processed", 
        "verify_bytes_processed",
    ],
)

# Perfometer for service overview - using individual operation uncorrected errors
perfometer_oposs_smart_error = Perfometer(
    name="oposs_smart_error",
    focus_range=FocusRange(
        lower=Closed(0),
        upper=Closed(100),
    ),
    segments=[
        "read_total_uncorrected_errors",
        "write_total_uncorrected_errors", 
        "verify_total_uncorrected_errors",
    ],
)