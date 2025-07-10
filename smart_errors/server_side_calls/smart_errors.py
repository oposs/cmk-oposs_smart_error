#!/usr/bin/env python3
"""
CheckMK Bakery Plugin for SMART Error Monitoring
Automatically distributes the agent plugin to monitored hosts
Compatible with CheckMK 2.3
"""

from pathlib import Path
from typing import Any, Dict

from cmk.utils.rulesets.definition import RuleGroup

from cmk.gui.i18n import _
from cmk.gui.valuespec import (
    Dictionary,
    DropdownChoice,
    Integer,
)
from cmk.gui.plugins.wato.utils import (
    HostRulespec,
    rulespec_registry,
)

# Plugin files to distribute
PLUGIN_FILES = {
    "smart_errors": {
        "source": Path(__file__).parent.parent.parent / "agents" / "plugins" / "smart_errors",
        "target": "plugins/smart_errors",
        "permissions": 0o755,
    }
}


def _valuespec_agent_config_smart_errors():
    """Configuration interface for SMART errors agent plugin"""
    return Dictionary(
        title=_("SMART Error Monitoring (Linux)"),
        help=_("This plugin monitors SMART error counters on storage devices. "
               "It requires the smartmontools package to be installed on the target system."),
        elements=[
            ("enabled", 
             DropdownChoice(
                 title=_("Enable SMART error monitoring"),
                 choices=[
                     (True, _("Enable")),
                     (False, _("Disable")),
                 ],
                 default_value=True,
             )
            ),
            ("timeout",
             Integer(
                 title=_("Command timeout (seconds)"),
                 help=_("Timeout for smartctl commands. Increase if you have many drives or slow storage."),
                 default_value=30,
                 minvalue=10,
                 maxvalue=300,
             )
            ),
            ("interval",
             Integer(
                 title=_("Execution interval (seconds)"),
                 help=_("How often to collect SMART error data. 0 means every agent run."),
                 default_value=0,
                 minvalue=0,
                 maxvalue=3600,
             )
            ),
        ],
        optional_keys=["timeout", "interval"],
    )


# Register the rule specification
rulespec_registry.register(
    HostRulespec(
        group=RuleGroup.AgentConfig,
        name="agent_config:smart_errors",
        valuespec=_valuespec_agent_config_smart_errors,
        title=lambda: _("SMART Error Monitoring (Linux)"),
        is_deprecated=False,
    )
)


def agent_config_smart_errors(params: Dict[str, Any], hostname: str, ipaddress: str) -> Dict[str, Any]:
    """Generate agent configuration for CheckMK 2.3"""
    if not params.get("enabled", True):
        return {}
    
    # Create the agent plugin content
    plugin_content = _get_agent_plugin_content(params)
    
    return {
        "files": {
            "plugins/smart_errors": {
                "content": plugin_content,
                "permissions": 0o755,
            }
        }
    }


def _get_agent_plugin_content(params: Dict[str, Any]) -> str:
    """Generate the agent plugin content with configuration"""
    timeout = params.get("timeout", 30)
    interval = params.get("interval", 0)
    
    # Read the base plugin file (located in same directory)
    plugin_source = Path(__file__).parent / "smart_errors"
    
    try:
        with open(plugin_source, 'r') as f:
            base_content = f.read()
    except FileNotFoundError:
        # Fallback embedded content
        base_content = _get_embedded_agent_plugin()
    
    # Modify timeout in the content
    if timeout != 30:
        base_content = base_content.replace("timeout=30", f"timeout={timeout}")
    
    # Add interval handling if specified
    if interval > 0:
        interval_header = f"""#!/usr/bin/env python3
# Interval: {interval}
"""
        # Insert interval header after shebang
        lines = base_content.split('\n')
        lines.insert(1, f"# Interval: {interval}")
        base_content = '\n'.join(lines)
    
    return base_content


def _get_embedded_agent_plugin() -> str:
    """Minimal fallback agent plugin if source file not found"""
    return '''#!/usr/bin/env python3
# Fallback SMART errors agent plugin
# This is a minimal version - the full plugin should be distributed via the source file
print("<<<smart_errors:sep(124)>>>")
print("ERROR|Agent plugin source file not found in bakery")
'''


# CheckMK 2.3 registration - function name is used for discovery
# The function agent_config_smart_errors is automatically discovered