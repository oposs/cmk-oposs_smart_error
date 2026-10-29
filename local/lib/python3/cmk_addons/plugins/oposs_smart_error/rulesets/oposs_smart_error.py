#!/usr/bin/env python3
"""
CheckMK Web GUI configuration for SMART Error monitoring
Defines rule sets and parameter forms for threshold configuration
Compatible with CheckMK 2.3
"""

from cmk.rulesets.v1 import Title, Help, Label
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    Integer,
    SimpleLevels,
    LevelDirection,
    DefaultValue,
    ServiceState,
    TimeSpan,
    TimeMagnitude,
)
from cmk.rulesets.v1.rule_specs import (
    CheckParameters,
    HostAndItemCondition,
    Topic,
)


def _parameter_form_oposs_smart_error():
    """Form specification for SMART error thresholds"""
    return Dictionary(
        title=Title("SMART Error Counter Thresholds"),
        help_text=Help("Configure thresholds for specific SMART error counter types by operation. "
               "Read, write, and verify operations show different error patterns."),
        elements={
            # Read operation thresholds
            "read_uncorrected_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Read: Uncorrected Errors (Absolute)"),
                    help_text=Help("Thresholds for uncorrected errors during read operations"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((1, 5)),
                ),
                required=False,
            ),
            "read_eccfast_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Read: ECC Fast Corrected Errors (Absolute)"),
                    help_text=Help("Thresholds for read errors corrected by ECC fast algorithm"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((50000, 500000)),
                ),
                required=False,
            ),
            "read_eccdelayed_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Read: ECC Delayed Corrected Errors (Absolute)"),
                    help_text=Help("Thresholds for read errors corrected by ECC delayed algorithm"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((5000, 50000)),
                ),
                required=False,
            ),
            "read_rereads_rewrites_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Read: Rereads/Rewrites Corrected Errors (Absolute)"),
                    help_text=Help("Thresholds for read errors corrected by rereads"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((500, 5000)),
                ),
                required=False,
            ),
            "read_algorithm_invocations_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Read: Correction Algorithm Invocations (Absolute)"),
                    help_text=Help("Thresholds for read correction algorithm invocations"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((100000, 1000000)),
                ),
                required=False,
            ),
            
            # Write operation thresholds
            "write_uncorrected_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Write: Uncorrected Errors (Absolute)"),
                    help_text=Help("Thresholds for uncorrected errors during write operations"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((1, 3)),
                ),
                required=False,
            ),
            "write_eccfast_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Write: ECC Fast Corrected Errors (Absolute)"),
                    help_text=Help("Thresholds for write errors corrected by ECC fast algorithm"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((10000, 100000)),
                ),
                required=False,
            ),
            "write_eccdelayed_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Write: ECC Delayed Corrected Errors (Absolute)"),
                    help_text=Help("Thresholds for write errors corrected by ECC delayed algorithm"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((1000, 10000)),
                ),
                required=False,
            ),
            "write_rereads_rewrites_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Write: Rereads/Rewrites Corrected Errors (Absolute)"),
                    help_text=Help("Thresholds for write errors corrected by rewrites"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((50, 500)),
                ),
                required=False,
            ),
            "write_algorithm_invocations_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Write: Correction Algorithm Invocations (Absolute)"),
                    help_text=Help("Thresholds for write correction algorithm invocations"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((25000, 250000)),
                ),
                required=False,
            ),
            
            # Verify operation thresholds
            "verify_uncorrected_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Verify: Uncorrected Errors (Absolute)"),
                    help_text=Help("Thresholds for uncorrected errors during verify operations"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((1, 5)),
                ),
                required=False,
            ),
            "verify_eccfast_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Verify: ECC Fast Corrected Errors (Absolute)"),
                    help_text=Help("Thresholds for verify errors corrected by ECC fast algorithm"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((20000, 200000)),
                ),
                required=False,
            ),
            "verify_eccdelayed_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Verify: ECC Delayed Corrected Errors (Absolute)"),
                    help_text=Help("Thresholds for verify errors corrected by ECC delayed algorithm"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((2000, 20000)),
                ),
                required=False,
            ),
            "verify_rereads_rewrites_errors_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Verify: Rereads/Rewrites Corrected Errors (Absolute)"),
                    help_text=Help("Thresholds for verify errors corrected by rereads"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((200, 2000)),
                ),
                required=False,
            ),
            "verify_algorithm_invocations_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Verify: Correction Algorithm Invocations (Absolute)"),
                    help_text=Help("Thresholds for verify correction algorithm invocations"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((50000, 500000)),
                ),
                required=False,
            ),

            # Grown defect list (SAS drives)
            "grown_defects_abs": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Grown Defect List Entries (Absolute)"),
                    help_text=Help("Thresholds for the number of sectors the drive has remapped "
                                   "since it left the factory. Without a rule the count is only "
                                   "shown and graphed."),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(),
                    prefill_fixed_levels=DefaultValue((10, 100)),
                ),
                required=False,
            ),
        }
    )


rule_spec_oposs_smart_error = CheckParameters(
    title=Title("SMART Error Monitoring"),
    topic=Topic.STORAGE,
    name="oposs_smart_error",
    parameter_form=_parameter_form_oposs_smart_error,
    condition=HostAndItemCondition(item_title=Title("Device")),
)


_DAYS = [TimeMagnitude.DAY, TimeMagnitude.HOUR]


def _parameter_form_oposs_smart_bms():
    """Form specification for background medium scan monitoring"""
    return Dictionary(
        title=Title("SMART Background Medium Scan"),
        help_text=Help("SAS drives read their whole surface on their own while idle "
                       "(background medium scan, BMS) and log the sectors they could not "
                       "read. All times are counted in drive power-on time."),
        elements={
            "last_scan_age": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Time since last completed scan"),
                    help_text=Help("The drive does not log when a scan finished. The check "
                                   "notes the power-on time at which the scan counter went up. "
                                   "Until it has seen that once, the time shown is a lower bound."),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=TimeSpan(displayed_magnitudes=_DAYS),
                    prefill_fixed_levels=DefaultValue((90 * 86400.0, 365 * 86400.0)),
                ),
                required=False,
            ),
            "recent_window": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Medium errors count as recent for"),
                    help_text=Help("A medium error logged within this power-on time is recent. "
                                   "Older entries stay in the drive log and get their own state."),
                    displayed_magnitudes=_DAYS,
                    prefill=DefaultValue(7 * 86400.0),
                ),
                required=False,
            ),
            "state_no_scan": DictElement(
                parameter_form=ServiceState(
                    title=Title("State when no scan is active"),
                    help_text=Help("Status 0 means background scanning is switched off on the drive."),
                    prefill=DefaultValue(ServiceState.WARN),
                ),
                required=False,
            ),
            "state_recent_unrecovered": DictElement(
                parameter_form=ServiceState(
                    title=Title("State for recent unrecovered medium errors"),
                    help_text=Help("The sector could not be read and its data was not restored. "
                                   "Storage with redundancy (Ceph, ZFS, RAID) should be told to "
                                   "rewrite it, for example with a deep scrub."),
                    prefill=DefaultValue(ServiceState.CRIT),
                ),
                required=False,
            ),
            "state_recent_recovered": DictElement(
                parameter_form=ServiceState(
                    title=Title("State for recent recovered medium errors"),
                    help_text=Help("The drive reassigned or rewrote the sector with its data intact."),
                    prefill=DefaultValue(ServiceState.WARN),
                ),
                required=False,
            ),
            "state_old_errors": DictElement(
                parameter_form=ServiceState(
                    title=Title("State for older medium errors"),
                    prefill=DefaultValue(ServiceState.OK),
                ),
                required=False,
            ),
        }
    )


rule_spec_oposs_smart_bms = CheckParameters(
    title=Title("SMART Background Medium Scan"),
    topic=Topic.STORAGE,
    name="oposs_smart_bms",
    parameter_form=_parameter_form_oposs_smart_bms,
    condition=HostAndItemCondition(item_title=Title("Device")),
)
