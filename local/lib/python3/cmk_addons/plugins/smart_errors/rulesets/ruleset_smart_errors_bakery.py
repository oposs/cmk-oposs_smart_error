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


def _parameter_form_smart_errors():
    """Configuration interface for SMART errors agent plugin"""
    return Dictionary(
        title=Title("SMART Error Monitoring (Linux)"),
        help_text=Help("This plugin monitors SMART error counters on storage devices. "
                       "It requires the smartmontools package to be installed on the target system."),
        elements={
            "enabled": DictElement(
                parameter_form=BooleanChoice(
                    title=Title("Enable SMART error monitoring"),
                    label=Label("Enable monitoring"),
                    prefill=DefaultValue(True),
                )
            ),
            "timeout": DictElement(
                parameter_form=Integer(
                    title=Title("Command timeout (seconds)"),
                    help_text=Help("Timeout for smartctl commands. Increase if you have many drives or slow storage."),
                    prefill=DefaultValue(30),
                    custom_validate=(lambda x: x >= 10 and x <= 300,),
                )
            ),
            "interval": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Execution interval"),
                    label=Label("How often to collect SMART error data"),
                    help_text=Help("0 means every agent run."),
                    displayed_magnitudes=[TimeMagnitude.SECOND, TimeMagnitude.MINUTE],
                    prefill=DefaultValue(0.0),
                )
            ),
            "timeout": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Command execution timeout"),
                    label=Label("Timeout for smartctl commands"),
                    help_text=Help("Set the timeout for each smartctl command execution."),
                    displayed_magnitudes=[TimeMagnitude.SECOND, TimeMagnitude.MINUTE],
                    prefill=DefaultValue(30.0),
                )
            ),
        }
    )


rule_spec_smart_errors_bakery = AgentConfig(
    name="smart_errors",
    title=Title("SMART Error Monitoring (Linux)"),
    topic=Topic.GENERAL,
    parameter_form=_parameter_form_smart_errors,
)