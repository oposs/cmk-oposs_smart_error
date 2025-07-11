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
    TimeSpan,
    TimeMagnitude
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