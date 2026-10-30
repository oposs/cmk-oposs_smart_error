#!/usr/bin/env python3
"""
CheckMK Bakery Ruleset for SMART Error Monitoring
Provides GUI configuration for the agent bakery plugin
Compatible with CheckMK 2.3
"""

from cmk.rulesets.v1 import Label, Title, Help
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DefaultValue,
    DictElement,
    Dictionary,
    Integer,
    SingleChoice,
    SingleChoiceElement,
    TimeSpan,
    TimeMagnitude,
    validators,
)
from cmk.rulesets.v1.rule_specs import AgentConfig, Topic


def _parameter_form_oposs_smart_error():
    """Configuration interface for SMART errors agent plugin"""
    return Dictionary(
        title=Title("OPOSS SMART Error Monitoring (smartctl)"),
        help_text=Help("This plugin monitors SMART error counters on storage devices. "
                       "It requires the smartmontools package to be installed on the target system."),
        elements={
            "interval": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Execution interval"),
                    label=Label("How often to collect SMART error data"),
                    help_text=Help("0 means every agent run."),
                    displayed_magnitudes=[TimeMagnitude.SECOND, TimeMagnitude.MINUTE],
                    prefill=DefaultValue(1800.0),
                )
            ),
            "timeout": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Command execution timeout"),
                    label=Label("Timeout for smartctl commands"),
                    help_text=Help("Set the timeout for each smartctl command execution."),
                    displayed_magnitudes=[TimeMagnitude.SECOND, TimeMagnitude.MINUTE],
                    prefill=DefaultValue(5.0),
                    custom_validate=(validators.NumberInRange(min_value=1.0),),
                )
            ),
            "standby": DictElement(
                parameter_form=SingleChoice(
                    title=Title("Disks in standby"),
                    help_text=Help("Reading a disk in STANDBY or SLEEP mode spins it up. When the "
                                   "disk is skipped, its services stay OK with \"Disk in standby, "
                                   "not checked\" until it is awake at an agent run."),
                    elements=[
                        SingleChoiceElement(name="skip", title=Title("Skip them, do not spin them up")),
                        SingleChoiceElement(name="wake", title=Title("Spin them up and check them")),
                    ],
                    prefill=DefaultValue("skip"),
                )
            ),
            "wake_after": DictElement(
                parameter_form=Integer(
                    title=Title("Check a disk in standby anyway after"),
                    unit_symbol="skipped runs",
                    help_text=Help("Spins up a disk that was skipped this many agent runs in a row, "
                                   "so a disk that sleeps all the time still gets checked. "
                                   "With an execution interval of 30 minutes, 48 means once a day. "
                                   "0 never spins a disk up."),
                    prefill=DefaultValue(0),
                    custom_validate=(validators.NumberInRange(min_value=0),),
                )
            ),
        }
    )


rule_spec_oposs_smart_error_bakery = AgentConfig(
    name="oposs_smart_error",
    title=Title("OPOSS SMART Error Monitoring (smartctl)"),
    topic=Topic.GENERAL,
    parameter_form=_parameter_form_oposs_smart_error,
)