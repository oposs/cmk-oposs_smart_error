#!/usr/bin/env python3
"""
CheckMK Web GUI configuration for SMART Error monitoring
Defines rule sets and parameter forms for threshold configuration
Compatible with CheckMK 2.3
"""

from cmk.gui.i18n import _
from cmk.gui.plugins.wato.utils import (
    CheckParameterRulespecWithoutItem,
    rulespec_registry,
)
from cmk.gui.valuespec import (
    Dictionary,
    Float,
    Integer,
    Tuple,
)
from cmk.gui.wato import RulespecGroupCheckParametersStorage


def _parameter_valuespec_smart_errors():
    """Value specification for SMART error thresholds"""
    return Dictionary(
        title=_("SMART Error Counter Thresholds"),
        help=_("Configure thresholds for specific SMART error counter types by operation. "
               "Read, write, and verify operations show different error patterns."),
        elements=[
            # Read operation thresholds
            ("read_uncorrected_errors_abs",
             Tuple(
                 title=_("Read: Uncorrected Errors (Absolute)"),
                 help=_("Thresholds for uncorrected errors during read operations"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=1),
                     Integer(title=_("Critical at"), default_value=5),
                 ],
             )
            ),
            ("read_eccfast_errors_abs",
             Tuple(
                 title=_("Read: ECC Fast Corrected Errors (Absolute)"),
                 help=_("Thresholds for read errors corrected by ECC fast algorithm"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=50000),
                     Integer(title=_("Critical at"), default_value=500000),
                 ],
             )
            ),
            ("read_eccdelayed_errors_abs",
             Tuple(
                 title=_("Read: ECC Delayed Corrected Errors (Absolute)"),
                 help=_("Thresholds for read errors corrected by ECC delayed algorithm"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=5000),
                     Integer(title=_("Critical at"), default_value=50000),
                 ],
             )
            ),
            ("read_rereads_rewrites_errors_abs",
             Tuple(
                 title=_("Read: Rereads/Rewrites Corrected Errors (Absolute)"),
                 help=_("Thresholds for read errors corrected by rereads"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=500),
                     Integer(title=_("Critical at"), default_value=5000),
                 ],
             )
            ),
            ("read_algorithm_invocations_abs",
             Tuple(
                 title=_("Read: Correction Algorithm Invocations (Absolute)"),
                 help=_("Thresholds for read correction algorithm invocations"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=100000),
                     Integer(title=_("Critical at"), default_value=1000000),
                 ],
             )
            ),
            
            # Write operation thresholds
            ("write_uncorrected_errors_abs",
             Tuple(
                 title=_("Write: Uncorrected Errors (Absolute)"),
                 help=_("Thresholds for uncorrected errors during write operations"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=1),
                     Integer(title=_("Critical at"), default_value=3),
                 ],
             )
            ),
            ("write_eccfast_errors_abs",
             Tuple(
                 title=_("Write: ECC Fast Corrected Errors (Absolute)"),
                 help=_("Thresholds for write errors corrected by ECC fast algorithm"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=10000),
                     Integer(title=_("Critical at"), default_value=100000),
                 ],
             )
            ),
            ("write_eccdelayed_errors_abs",
             Tuple(
                 title=_("Write: ECC Delayed Corrected Errors (Absolute)"),
                 help=_("Thresholds for write errors corrected by ECC delayed algorithm"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=1000),
                     Integer(title=_("Critical at"), default_value=10000),
                 ],
             )
            ),
            ("write_rereads_rewrites_errors_abs",
             Tuple(
                 title=_("Write: Rereads/Rewrites Corrected Errors (Absolute)"),
                 help=_("Thresholds for write errors corrected by rewrites"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=50),
                     Integer(title=_("Critical at"), default_value=500),
                 ],
             )
            ),
            ("write_algorithm_invocations_abs",
             Tuple(
                 title=_("Write: Correction Algorithm Invocations (Absolute)"),
                 help=_("Thresholds for write correction algorithm invocations"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=25000),
                     Integer(title=_("Critical at"), default_value=250000),
                 ],
             )
            ),
            
            # Verify operation thresholds
            ("verify_uncorrected_errors_abs",
             Tuple(
                 title=_("Verify: Uncorrected Errors (Absolute)"),
                 help=_("Thresholds for uncorrected errors during verify operations"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=1),
                     Integer(title=_("Critical at"), default_value=5),
                 ],
             )
            ),
            ("verify_eccfast_errors_abs",
             Tuple(
                 title=_("Verify: ECC Fast Corrected Errors (Absolute)"),
                 help=_("Thresholds for verify errors corrected by ECC fast algorithm"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=20000),
                     Integer(title=_("Critical at"), default_value=200000),
                 ],
             )
            ),
            ("verify_eccdelayed_errors_abs",
             Tuple(
                 title=_("Verify: ECC Delayed Corrected Errors (Absolute)"),
                 help=_("Thresholds for verify errors corrected by ECC delayed algorithm"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=2000),
                     Integer(title=_("Critical at"), default_value=20000),
                 ],
             )
            ),
            ("verify_rereads_rewrites_errors_abs",
             Tuple(
                 title=_("Verify: Rereads/Rewrites Corrected Errors (Absolute)"),
                 help=_("Thresholds for verify errors corrected by rereads"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=200),
                     Integer(title=_("Critical at"), default_value=2000),
                 ],
             )
            ),
            ("verify_algorithm_invocations_abs",
             Tuple(
                 title=_("Verify: Correction Algorithm Invocations (Absolute)"),
                 help=_("Thresholds for verify correction algorithm invocations"),
                 elements=[
                     Integer(title=_("Warning at"), default_value=50000),
                     Integer(title=_("Critical at"), default_value=500000),
                 ],
             )
            ),
            
            # Rate-based thresholds
            ("uncorrected_errors_per_tb",
             Tuple(
                 title=_("Any Operation: Uncorrected Errors per TB"),
                 help=_("Thresholds for uncorrected error rate per terabyte processed (any operation)"),
                 elements=[
                     Float(title=_("Warning at"), default_value=0.1),
                     Float(title=_("Critical at"), default_value=1.0),
                 ],
             )
            ),
        ]
    )


rulespec_registry.register(
    CheckParameterRulespecWithoutItem(
        check_group_name="smart_errors",
        group=RulespecGroupCheckParametersStorage,
        match_type="dict",
        parameter_valuespec=_parameter_valuespec_smart_errors,
        title=lambda: _("SMART Error Monitoring"),
    )
)