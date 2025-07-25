# CheckMK Agent-Based Check Plugin Development Guide
## CheckMK 2.3.0

This guide provides comprehensive instructions for developing agent-based check plugins for CheckMK 2.3.0, including Agent Bakery support, based on the official CheckMK Plugin APIs.

## Overview

CheckMK agent-based check plugins consist of two main components:
1. **Agent Plugin** - Collects raw monitoring data on the target host
2. **Check Plugin** - Processes the data and determines service states on the CheckMK server

## Prerequisites

- CheckMK 2.3.0 installation
- Python 3 knowledge
- Understanding of the monitoring system being implemented
- Access to CheckMK development environment

## Development Environment Setup

### Directory Structure
```
~/local/lib/python3/cmk_addons/plugins/MY_PLUGIN
├── agent_based/           # Check plugins (using cmk.agent_based.v2)
├── graphing/             # Graphing definitions (using cmk.graphing.v1)
├── rulesets/             # Rule specifications (using cmk.rulesets.v1)
└── server_side_calls/    # Special agents (using cmk.server_side_calls.v1)

~/local/lib/python3/cmk/base/cee/plugins/bakery/
└──                       # Agent bakery plugins (using cmk.base.plugins.bakery.bakery_api.v1)

~/local/share/check_mk/agents/plugins/
└──                       # Agent plugin source files
```

### Agent Plugin Location
```
/usr/lib/check_mk_agent/plugins/
```

## Plugin Discovery and Entry Points

CheckMK 2.3.0 uses a discovery-based approach for plugin registration. Plugins are discovered using entry point prefixes:

- `agent_section_` - For agent sections
- `snmp_section_` - For SNMP sections
- `check_plugin_` - For check plugins
- `inventory_plugin_` - For inventory plugins

**Important**: Use `cmk.agent_based.v2.entry_point_prefixes()` to get the current prefixes programmatically.

## Agent Plugin Development

### Basic Structure
Agent plugins are executable scripts that output monitoring data in CheckMK format.

```bash
#!/bin/bash
# Agent plugin example
echo "<<<my_service>>>"
# Output monitoring data here
```

### Key Requirements
- Must be executable
- Output section header: `<<<section_name>>>`
- Provide structured data for the check plugin to parse
- Should handle errors gracefully
- Use consistent field separators (space or tab)

### Example Agent Plugin
```python
#!/usr/bin/env python3
import json
import os
import subprocess
import sys

# Determine the config file path using the MK_CONFDIR environment variable
CONFIG_FILE = os.path.join(os.environ.get("MK_CONFDIR", "/etc/check_mk"), "my_service.json")

def get_config() -> dict:
    """Read and parse the JSON configuration file."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def get_service_data(timeout: int):
    """Collect service-specific data"""
    try:
        # Your data collection logic here
        result = subprocess.run(['your_command'], capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out"
    except Exception as e:
        return f"ERROR: {e}"

def main():
    # Read configuration
    config = get_config()
    timeout = config.get("timeout", 30)

    # Always start with section header
    print("<<<my_custom_service>>>")
    
    # Output structured data
    data = get_service_data(timeout)
    if data.startswith("ERROR:"):
        print(data, file=sys.stderr)
        sys.exit(1)
    
    # Output data in structured format
    lines = data.split('\n')
    for line in lines:
        if line.strip():
            print(line)

if __name__ == "__main__":
    main()
```

### Advanced Agent Plugin Features
```python
#!/usr/bin/env python3
# Advanced agent plugin with multiple sections

import json
import time
import sys

def collect_metrics():
    """Collect various metrics"""
    return {
        'cpu_usage': 85.2,
        'memory_usage': 67.8,
        'disk_usage': 45.3,
        'timestamp': int(time.time())
    }

def collect_status():
    """Collect service status information"""
    return {
        'service_name': 'my_service',
        'status': 'running',
        'uptime': 3600,
        'version': '2.1.0'
    }

def main():
    try:
        # Multiple sections can be output
        print("<<<my_service_metrics>>>")
        metrics = collect_metrics()
        for key, value in metrics.items():
            print(f"{key} {value}")
        
        print("<<<my_service_status>>>")
        status = collect_status()
        for key, value in status.items():
            print(f"{key} {value}")
            
    except Exception as e:
        print(f"<<<my_service_error>>>", file=sys.stderr)
        print(f"error {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Advanced Agent Plugin Patterns

#### JSON-Encoded Data with Custom Separators

For complex data structures, you can use JSON encoding with custom field separators. This is particularly useful when monitoring systems that produce rich, nested data.

```python
#!/usr/bin/env python3
import json
import subprocess
import sys

def get_complex_device_data(device_name):
    """Collect complex device information"""
    try:
        # Example: Get detailed device information
        result = subprocess.run(['smartctl', '--json=c', '--info', device_name], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except Exception:
        return None

def main():
    # Use custom separator (pipe character, ASCII 124)
    print("<<<smart_devices:sep(124)>>>")
    
    devices = ['/dev/sda', '/dev/sdb', '/dev/nvme0n1']
    
    for device_name in devices:
        device_data = get_complex_device_data(device_name)
        if device_data:
            # Create structured output data
            output_data = {
                'device': device_data.get('device', {}).get('name', device_name),
                'model': device_data.get('model_name', ''),
                'serial': device_data.get('serial_number', ''),
                'capacity_bytes': device_data.get('user_capacity', {}).get('bytes', 0),
                'smart_status': device_data.get('smart_status', {}).get('passed', False),
                'temperature': device_data.get('temperature', {}).get('current', 0),
                'power_on_hours': device_data.get('power_on_time', {}).get('hours', 0),
            }
            
            # Output: device_name|json_data
            print(f"{device_name}|{json.dumps(output_data, separators=(',', ':'))}")
        else:
            # Handle errors gracefully
            print(f"{device_name}|ERROR|Failed to get device data")

if __name__ == "__main__":
    main()
```

**Key advantages of this pattern:**
- **Rich Data Structures**: Handle complex nested data
- **Efficient Parsing**: Single JSON decode operation on server
- **Consistent Format**: Structured data easier to process
- **Error Handling**: Clear error states for failed devices

#### Multi-Section Output with Different Data Types

```python
#!/usr/bin/env python3
import json
import time
import subprocess

def collect_system_metrics():
    """Collect various system metrics"""
    return {
        'cpu_usage': 85.2,
        'memory_usage': 67.8,
        'load_average': [1.2, 1.5, 1.8],
        'timestamp': int(time.time())
    }

def collect_service_status():
    """Collect service status information"""
    services = []
    try:
        result = subprocess.run(['systemctl', 'list-units', '--type=service', '--state=running'],
                              capture_output=True, text=True, timeout=10)
        for line in result.stdout.split('\n')[1:]:  # Skip header
            if line.strip() and not line.startswith('●'):
                parts = line.split()
                if len(parts) >= 4:
                    services.append({
                        'name': parts[0],
                        'load': parts[1],
                        'active': parts[2],
                        'sub': parts[3]
                    })
    except Exception:
        pass
    return services

def main():
    try:
        # Section 1: Simple key-value metrics
        print("<<<system_metrics>>>")
        metrics = collect_system_metrics()
        for key, value in metrics.items():
            if isinstance(value, list):
                print(f"{key} {' '.join(map(str, value))}")
            else:
                print(f"{key} {value}")
        
        # Section 2: JSON-encoded complex data with custom separator
        print("<<<service_status:sep(124)>>>")
        services = collect_service_status()
        for service in services:
            service_name = service['name']
            service_data = json.dumps(service, separators=(',', ':'))
            print(f"{service_name}|{service_data}")
        
        # Section 3: Mixed format for compatibility
        print("<<<system_info>>>")
        print(f"hostname {subprocess.getoutput('hostname')}")
        print(f"uptime {subprocess.getoutput('uptime -p')}")
        print(f"kernel {subprocess.getoutput('uname -r')}")
            
    except Exception as e:
        print(f"<<<monitoring_error>>>", file=sys.stderr)
        print(f"error {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### Real-World Example: SMART Error Monitoring

Here's a complete real-world example that demonstrates advanced agent plugin patterns:

```python
#!/usr/bin/env python3
"""
Advanced SMART Error Monitoring Agent Plugin
Demonstrates JSON encoding, custom separators, and error handling
"""

import json
import subprocess
import sys
from typing import Dict, List, Optional

def get_smart_devices() -> List[Dict]:
    """Get list of SMART-capable devices"""
    try:
        result = subprocess.run(
            ['smartctl', '--json', '--scan'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return []
        
        data = json.loads(result.stdout)
        return data.get('devices', [])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []

def get_smart_info_and_errors(device_name: str) -> Optional[Dict]:
    """Get comprehensive SMART data for a device"""
    try:
        result = subprocess.run(
            ['smartctl', '--json=c', '--info', '--log=error', device_name],
            capture_output=True, text=True, timeout=30
        )
        # Allow various return codes that still provide useful data
        if result.returncode not in [0, 1, 2, 4]:
            return None
        
        data = json.loads(result.stdout)
        return data
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None

def main():
    """Main function demonstrating advanced agent plugin patterns"""
    devices = get_smart_devices()
    
    if not devices:
        # Exit silently if no devices - don't create empty sections
        return
    
    # Use custom separator for complex JSON data
    print("<<<smart_errors:sep(124)>>>")
    
    for device in devices:
        device_name = device.get('name', '')
        if not device_name:
            continue
            
        smart_data = get_smart_info_and_errors(device_name)
        if smart_data is None:
            # Structured error reporting
            print(f"{device_name}|ERROR|Failed to get SMART data")
            continue
        
        # Extract and structure relevant data
        device_info = smart_data.get('device', {})
        error_log = smart_data.get('scsi_error_counter_log', {})
        
        # Skip devices without the data we need
        if not error_log:
            continue
        
        # Validate data quality before processing
        valid_operations = ['read', 'write', 'verify']
        if not any(op in error_log for op in valid_operations):
            continue
        
        # Create comprehensive output structure
        output_data = {
            'device': device_info.get('name', device_name),
            'protocol': device_info.get('protocol', 'unknown'),
            'model': smart_data.get('model_name', ''),
            'serial': smart_data.get('serial_number', ''),
            'firmware': smart_data.get('firmware_version', ''),
            'capacity_bytes': smart_data.get('user_capacity', {}).get('bytes', 0),
            'error_counters': error_log
        }
        
        # Output structured data: device_name|json_payload
        print(f"{device_name}|{json.dumps(output_data, separators=(',', ':'))}")

if __name__ == "__main__":
    main()
```

**Corresponding check plugin parser:**

```python
def parse_smart_errors(string_table: StringTable) -> Section:
    """Parse JSON-encoded SMART error data"""
    section = {}
    
    for line in string_table:
        if len(line) < 2:
            continue
            
        device_name = line[0]
        
        if line[1] == "ERROR":
            # Handle structured error reporting
            error_msg = line[2] if len(line) > 2 else "Unknown error"
            section[device_name] = {"error": error_msg}
            continue
        
        try:
            # Parse JSON payload
            data = json.loads(line[1])
            section[device_name] = data
        except json.JSONDecodeError:
            section[device_name] = {"error": "Invalid JSON data"}
    
    return section
```

#### Best Practices for JSON-Encoded Agent Plugins

When using JSON encoding in agent plugins, follow these best practices:

**1. Use Custom Separators for Complex Data**
```python
# Good: Custom separator for JSON data
print("<<<my_service:sep(124)>>>")  # Uses pipe (|) separator
print(f"{item_name}|{json.dumps(data, separators=(',', ':'))}")

# Avoid: Default whitespace with JSON (parsing issues)
print("<<<my_service>>>")
print(f"{item_name} {json.dumps(data)}")  # Spaces in JSON break parsing
```

**2. Compact JSON Encoding**
```python
# Good: Compact encoding saves bandwidth
json.dumps(data, separators=(',', ':'))

# Avoid: Pretty-printed JSON wastes space
json.dumps(data, indent=2)
```

**3. Structured Error Handling**
```python
# Good: Consistent error format
if error_condition:
    print(f"{device_name}|ERROR|Specific error message")
    continue

# Avoid: Inconsistent error reporting
if error_condition:
    print(f"Error with {device_name}")  # No structure
```

**4. Data Validation Before Output**
```python
# Good: Validate data quality
def validate_data(data):
    required_fields = ['status', 'metrics']
    return all(field in data for field in required_fields)

for item in items:
    data = collect_data(item)
    if data and validate_data(data):
        print(f"{item}|{json.dumps(data, separators=(',', ':'))}")
    else:
        print(f"{item}|ERROR|Invalid or missing data")
```

**5. Performance Considerations**
```python
# Good: Batch processing and efficient data structures
def main():
    all_data = collect_all_data()  # Single collection call
    
    print("<<<my_service:sep(124)>>>")
    
    for item_name, item_data in all_data.items():
        if item_data:
            # Pre-structure data for JSON encoding
            output_data = {
                'name': item_data['name'],
                'metrics': item_data.get('metrics', {}),
                'timestamp': int(time.time())
            }
            print(f"{item_name}|{json.dumps(output_data, separators=(',', ':'))}")

# Avoid: Individual calls in loop
def main():
    print("<<<my_service:sep(124)>>>")
    
    for item_name in get_item_names():
        item_data = collect_data(item_name)  # Slow: N separate calls
        print(f"{item_name}|{json.dumps(item_data, separators=(',', ':'))}")
```

**6. Unicode and Special Character Handling**
```python
# Good: Ensure ASCII output for compatibility
json.dumps(data, separators=(',', ':'), ensure_ascii=True)

# Handle special characters in keys
safe_key = device_name.replace('|', '_').replace('\n', '_')
print(f"{safe_key}|{json.dumps(data, separators=(',', ':'))}")
```

**7. Section Headers and Data Organization**
```python
# Good: Clear section organization
def main():
    # Static configuration data
    print("<<<service_config>>>")
    print(f"version {get_version()}")
    print(f"config_path {get_config_path()}")
    
    # Dynamic metrics with JSON
    print("<<<service_metrics:sep(124)>>>")
    for metric_name, metric_data in get_metrics().items():
        print(f"{metric_name}|{json.dumps(metric_data, separators=(',', ':'))}")
    
    # Status information
    print("<<<service_status:sep(124)>>>")
    status_data = get_status()
    print(f"overall|{json.dumps(status_data, separators=(',', ':'))}")
```

#### When to Use JSON vs Simple Formats

**Use JSON encoding when:**
- Data has nested structures (dictionaries, lists)
- Multiple related metrics per item
- Complex error information needed
- Data types vary (strings, numbers, booleans)

**Use simple key-value format when:**
- Data is flat (single level)
- Performance is critical
- Backward compatibility required
- Simple numeric metrics only

**Example comparison:**

```python
# Simple format - good for basic metrics
print("<<<cpu_usage>>>")
print("cpu0 85.2")
print("cpu1 67.8")
print("load_avg 1.25")

# JSON format - good for complex data
print("<<<cpu_detailed:sep(124)>>>")
cpu_data = {
    'usage_percent': 85.2,
    'frequency_mhz': 2400,
    'temperature_celsius': 65,
    'processes': ['python', 'nginx', 'mysql'],
    'load_average': [1.25, 1.50, 1.80]
}
print(f"cpu0|{json.dumps(cpu_data, separators=(',', ':'))}")
```

## Check Plugin Development

### API Version 2 Overview
CheckMK 2.3.0 uses the `cmk.agent_based.v2` API, which replaces the registration-based approach with a discovery-based system using classes.

### Essential Components
Every check plugin requires:

1. **Agent Section** - Defines how raw data is parsed
2. **Check Plugin** - Defines service discovery and checking logic
3. **Entry Point Prefixes** - For plugin discovery

### Basic Check Plugin Structure
```python
#!/usr/bin/env python3
# File: ~/local/lib/python3/cmk_addons/plugins/agent_based/my_service.py

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
    Metric,
    render,
)
from typing import Any, Dict, Mapping

# Define the section
def parse_my_service(string_table: list[list[str]]) -> Dict[str, Any]:
    """Parse raw agent data into structured format"""
    parsed_data = {}
    for line in string_table:
        if len(line) >= 2:
            key, value = line[0], line[1]
            # Try to convert to appropriate type
            try:
                parsed_data[key] = float(value) if '.' in value else int(value)
            except ValueError:
                parsed_data[key] = value
    return parsed_data

# Create the agent section
agent_section_my_service = AgentSection(
    name="my_service",
    parse_function=parse_my_service,
)

# Discovery function
def discover_my_service(section: Dict[str, Any]) -> DiscoveryResult:
    """Determine which services to create"""
    if section:
        yield Service(item="my_service")

# Check function
def check_my_service(item: str, section: Dict[str, Any]) -> CheckResult:
    """Evaluate data and determine service state"""
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data available")
        return
    
    # Your check logic here
    value = section.get("metric_value", 0)
    
    # Yield metrics
    yield Metric("my_metric", value)
    
    # Determine state
    if value > 100:
        yield Result(state=State.CRIT, summary=f"Critical: Value is {value}")
    elif value > 50:
        yield Result(state=State.WARN, summary=f"Warning: Value is {value}")
    else:
        yield Result(state=State.OK, summary=f"OK: Value is {value}")

# Create the check plugin
check_plugin_my_service = CheckPlugin(
    name="my_service",
    service_name="My Service",
    discovery_function=discover_my_service,
    check_function=check_my_service,
    sections=["my_service"],
)
```

### AgentSection Class Details
```python
# Complete AgentSection signature
class AgentSection:
    name: str
    parse_function: Callable[[list[list[str]]], Any]
    parsed_section_name: str | None = None
    host_label_function: Callable[[Any], HostLabelGenerator] | None = None
    supersedes: list[str] | None = None
```

### CheckPlugin Class Details
```python
# Complete CheckPlugin signature
class CheckPlugin:
    name: str
    sections: list[str]
    service_name: str
    discovery_function: Callable[..., DiscoveryResult]
    check_function: Callable[..., CheckResult]
    check_default_parameters: Mapping[str, Any] | None = None
    check_ruleset_name: str | None = None
    cluster_check_function: Callable[..., CheckResult] | None = None
```

### Advanced Features

#### Metrics and Performance Data
```python
from cmk.agent_based.v2 import Metric, render

def check_my_service_with_metrics(item: str, section: Dict[str, Any]) -> CheckResult:
    value = section.get("metric_value", 0)
    
    # Multiple metrics can be yielded
    yield Metric("my_metric", value, boundaries=(0, 200))
    yield Metric("secondary_metric", section.get("secondary_value", 0))
    
    # Use render functions for consistent formatting
    yield Result(
        state=State.OK, 
        summary=f"Current value: {render.percent(value)}"
    )
```

#### Configuration Parameters
```python
from typing import Mapping

def check_my_service_with_params(
    item: str, 
    params: Mapping[str, Any], 
    section: Dict[str, Any]
) -> CheckResult:
    warn_level = params.get("warn_level", 50)
    crit_level = params.get("crit_level", 100)
    
    value = section.get("metric_value", 0)
    
    if value >= crit_level:
        state = State.CRIT
    elif value >= warn_level:
        state = State.WARN
    else:
        state = State.OK
    
    yield Result(state=state, summary=f"Value: {value}")
    yield Metric("my_metric", value, levels=(warn_level, crit_level))

# Check plugin with parameters
check_plugin_my_service_params = CheckPlugin(
    name="my_service_params",
    service_name="My Service %s",
    sections=["my_service"],
    discovery_function=discover_my_service,
    check_function=check_my_service_with_params,
    check_ruleset_name="my_service_levels",
    check_default_parameters={"warn_level": 50, "crit_level": 100},
)
```

#### Multi-Item Services
```python
def discover_my_service_multi(section: Dict[str, Any]) -> DiscoveryResult:
    """Discover multiple service items"""
    for item_name in section.keys():
        if item_name.startswith("item_"):
            yield Service(item=item_name)

def check_my_service_multi(item: str, section: Dict[str, Any]) -> CheckResult:
    """Check specific item"""
    if item not in section:
        yield Result(state=State.UNKNOWN, summary=f"Item {item} not found")
        return
    
    value = section[item]
    yield Result(state=State.OK, summary=f"Item {item}: {value}")
    yield Metric(f"metric_{item}", value)

check_plugin_my_service_multi = CheckPlugin(
    name="my_service_multi",
    service_name="My Service %s",
    sections=["my_service"],
    discovery_function=discover_my_service_multi,
    check_function=check_my_service_multi,
)
```

#### Using check_levels Helper
```python
from cmk.agent_based.v2 import check_levels

def check_my_service_levels(item: str, params: Mapping[str, Any], section: Dict[str, Any]) -> CheckResult:
    value = section.get("metric_value", 0)
    
    # Use check_levels for automatic level checking
    yield from check_levels(
        value=value,
        metric_name="my_metric",
        levels_upper=params.get("levels"),
        label="My metric",
        render_func=render.percent,
    )
```

## Agent Bakery Integration

The Agent Bakery allows centralized configuration and deployment of agent plugins across multiple hosts using the `cmk.base.plugins.bakery.bakery_api.v1` API.

**Important**: CheckMK 2.3 bakery integration requires **two separate files**:
1. **Bakery Plugin** - Technical logic for plugin generation and deployment
2. **Bakery Ruleset** - GUI configuration interface for administrators

### Bakery Plugin Structure
```python
# File: ~/local/lib/check_mk/base/cee/plugins/bakery/my_service.py

import json
from cmk.base.plugins.bakery.bakery_api.v1 import (
    register,
    Plugin,
    PluginConfig,
    OS,
    WindowsConfigEntry,
    FileGenerator,
    ScriptletGenerator,
)
from pathlib import Path
from typing import Any, Dict

def get_my_service_files(conf: Dict[str, Any]):
    """Files function for my_service bakery plugin"""
    if conf is None or not conf.get("enabled", True):
        return

    # Get configuration values
    interval = int(conf.get("interval", 60))
    timeout = conf.get("timeout", 30)

    # Generate configuration file for the agent in JSON format
    config_content = json.dumps({"timeout": int(timeout)})
    yield PluginConfig(
        base_os=OS.LINUX,
        target=Path("my_service.json"),
        lines=config_content.splitlines(),
    )

    # Generate plugin using source reference
    # This will automatically find the agent plugin in local/share/check_mk/agents/plugins/
    yield Plugin(
        base_os=OS.LINUX,
        source=Path('my_service'),  # References local/share/check_mk/agents/plugins/my_service
        target=Path('my_service'),  # Deploys to /usr/lib/check_mk_agent/plugins/my_service
        interval=interval,
    )

# Register the bakery plugin using the official API
register.bakery_plugin(
    name="my_service",
    files_function=get_my_service_files,
)
```

### Bakery Ruleset Structure (CheckMK 2.3 - Modern API)
```python
# File: ~/local/lib/python3/cmk_addons/plugins/<family>/rulesets/ruleset_<name>_bakery.py

from cmk.rulesets.v1 import Label, Title, Help
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DefaultValue,
    DictElement,
    Dictionary,
    TimeSpan,
    TimeMagnitude
)
from cmk.rulesets.v1.rule_specs import AgentConfig, Topic

def _parameter_form_my_service():
    """Configuration interface for bakery plugin"""
    return Dictionary(
        title=Title("My Service Agent Plugin"),
        help_text=Help("Configure the My Service monitoring agent plugin."),
        elements={
            "enabled": DictElement(
                parameter_form=BooleanChoice(
                    title=Title("Enable monitoring"),
                    label=Label("Enable monitoring"),
                    prefill=DefaultValue(True),
                )
            ),
            "interval": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Execution interval"),
                    label=Label("How often to collect data"),
                    help_text=Help("0 means every agent run."),
                    displayed_magnitudes=[TimeMagnitude.SECOND, TimeMagnitude.MINUTE],
                    prefill=DefaultValue(60.0),
                )
            ),
            "timeout": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Command execution timeout"),
                    label=Label("Timeout for external commands"),
                    help_text=Help("Set the timeout for commands run by the agent plugin."),
                    displayed_magnitudes=[TimeMagnitude.SECOND],
                    prefill=DefaultValue(30.0),
                )
            ),
        }
    )

# Register the bakery rule specification
rule_spec_my_service_bakery = AgentConfig(
    name="my_service",
    title=Title("My Service Agent Deployment"),
    topic=Topic.GENERAL,
    parameter_form=_parameter_form_my_service,
)
```

### Key Points About the Bakery API

**Separation of Concerns:**
- **Bakery Plugin**: Technical logic only (`local/lib/check_mk/base/cee/plugins/bakery/`)
- **Bakery Ruleset**: GUI configuration only (`local/lib/python3/cmk_addons/plugins/<family>/rulesets/`)
- Never mix both concerns in the same file

**Agent Plugin Source Location:**
- Agent plugins should be stored in `local/share/check_mk/agents/plugins/`
- The bakery automatically finds them when using `source=Path('plugin_name')`
- No need to manually read file content or specify complex paths

**Registration:**
- Use `register.bakery_plugin()` for proper registration
- Use `files_function` parameter with a generator function
- The function should yield `Plugin` objects

**Configuration:**
- Configuration comes from ruleset parameters
- Use the `conf` parameter to access user settings
- Return early if plugin is disabled

### Advanced Bakery Features
```python
# File: ~/local/lib/check_mk/base/cee/plugins/bakery/my_service_advanced.py

from cmk.base.plugins.bakery.bakery_api.v1 import (
    register,
    Plugin,
    PluginConfig,
    OS,
    WindowsConfigEntry,
    ScriptletGenerator,
    FileGenerator,
)
from pathlib import Path
from typing import Any, Dict

def get_my_service_advanced_files(conf: Dict[str, Any]):
    """Advanced files function with multiple plugin variants"""

    # Get configuration values
    interval = conf.get('interval', 60)
    timeout = conf.get('timeout', 30)
    
    # Generate Linux plugin
    yield Plugin(
        base_os=OS.LINUX,
        source=Path('my_service_advanced'),  # References source file
        target=Path('my_service_advanced'),  # Target deployment path
        interval=interval,
    )
    
    # Generate Windows plugin if enabled
    if conf.get('windows_enabled', False):
        yield Plugin(
            base_os=OS.WINDOWS,
            source=Path('my_service_advanced.bat'),  # Windows batch script
            target=Path('my_service_advanced.bat'),
            interval=interval,
        )
    
    # Generate configuration file
    config_content = f'''# My Service Advanced Configuration
interval = {interval}
timeout = {timeout}
enabled = {conf.get('enabled', True)}
'''
    
    yield PluginConfig(
        target_path="cfg/my_service_advanced.conf",
        content=config_content,
    )

def get_my_service_advanced_scriptlets(conf: Dict[str, Any]):
    """Scriptlets function for package management"""
    if conf is None or not conf.get("enabled", True):
        return
    
    # Installation scriptlet
    install_script = f'''#!/bin/bash
# Install scriptlet for my_service_advanced
mkdir -p /etc/my_service
echo "interval={conf.get('interval', 60)}" > /etc/my_service/config
chmod 644 /etc/my_service/config
'''
    
    # Uninstall scriptlet
    uninstall_script = '''#!/bin/bash
# Uninstall scriptlet for my_service_advanced
rm -rf /etc/my_service
'''
    
    yield ScriptletGenerator(
        install=install_script,
        uninstall=uninstall_script,
    )

def get_my_service_advanced_windows_config(conf: Dict[str, Any]):
    """Windows configuration function"""
    if conf is None or not conf.get("enabled", True) or not conf.get('windows_enabled', False):
        return
    
    yield WindowsConfigEntry(
        path="my_service_advanced",
        content={
            "interval": conf.get('interval', 60),
            "timeout": conf.get('timeout', 30),
        },
    )

# Register the advanced bakery plugin with all functions
register.bakery_plugin(
    name="my_service_advanced",
    files_function=get_my_service_advanced_files,
    scriptlets_function=get_my_service_advanced_scriptlets,
    windows_config_function=get_my_service_advanced_windows_config,
)
```

## Ruleset Integration

Rulesets allow users to configure plugin parameters through the CheckMK GUI using the `cmk.rulesets.v1` API.

### Basic Ruleset Definition
```python
# File: ~/local/lib/python3/cmk_addons/plugins/rulesets/my_service.py

from cmk.rulesets.v1 import Title, Help, Label
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    Integer,
    String,
    BooleanChoice,
    SimpleLevels,
    LevelDirection,
    DefaultValue,
    InputHint,
)
from cmk.rulesets.v1.rule_specs import (
    CheckParameters,
    HostAndServiceCondition,
    HostAndItemCondition,
    Topic,
)

def _form_spec_my_service():
    return Dictionary(
        title=Title("My Service Check Configuration"),
        elements={
            "levels": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Levels for my metric"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Integer(unit_symbol="%"),
                    prefill_fixed_levels=DefaultValue((80, 90)),
                ),
                required=True,
            ),
            "interval": DictElement(
                parameter_form=Integer(
                    title=Title("Check Interval"),
                    help_text=Help("Interval in seconds between checks"),
                    prefill=DefaultValue(60),
                    custom_validate=[
                        validators.NumberInRange(min_value=1, max_value=3600)
                    ],
                ),
                required=False,
            ),
        },
    )

# For check plugins WITHOUT items (single service per host)
rule_spec_my_service_no_items = CheckParameters(
    title=Title("My Service Ruleset"),
    topic=Topic.APPLICATIONS,
    name="my_service",
    parameter_form=_form_spec_my_service,
    condition=HostAndServiceCondition(service_name="My Service"),
)

# For check plugins WITH items (multiple services per host)
rule_spec_my_service_with_items = CheckParameters(
    title=Title("My Service Ruleset"),
    topic=Topic.APPLICATIONS,
    name="my_service_items",
    parameter_form=_form_spec_my_service,
    condition=HostAndItemCondition(item_title=Title("Service Instance")),
)
```

### Ruleset Conditions: HostAndServiceCondition vs HostAndItemCondition

**Critical Decision Point**: Choose the correct condition type based on your check plugin structure.

#### HostAndServiceCondition
Use for check plugins that create **single services per host** (no items):

```python
from cmk.rulesets.v1.rule_specs import HostAndServiceCondition

# For check plugins like system CPU, memory, uptime
condition=HostAndServiceCondition(service_name="CPU utilization")
```

**Examples of non-item services:**
- System CPU monitoring
- Overall memory usage
- System uptime
- Single application monitoring

#### HostAndItemCondition  
Use for check plugins that create **multiple services per host** (with items):

```python
from cmk.rulesets.v1.rule_specs import HostAndItemCondition

# For check plugins like filesystems, network interfaces, database tables
condition=HostAndItemCondition(item_title=Title("ZPool name"))
```

**Examples of item-based services:**
- Filesystem monitoring (item = mount point)
- Network interface monitoring (item = interface name)
- Database monitoring (item = database name)
- **ZFS pool monitoring (item = pool name)** ← Our OPOSS zpool iostat case

#### Real-World Example: OPOSS zpool iostat

```python
# File: ~/local/lib/python3/cmk_addons/plugins/rulesets/oposs_zpool_iostat.py

rule_spec_oposs_zpool_iostat = CheckParameters(
    title=Title("OPOSS zpool iostat monitoring"),
    topic=Topic.STORAGE,
    name="oposs_zpool_iostat", # Must match check_ruleset_name in CheckPlugin
    parameter_form=_parameter_form_oposs_zpool_iostat,
    condition=HostAndItemCondition(item_title=Title("ZPool name")), # Correct for multi-pool monitoring
)
```

#### Common Mistake: Using the Wrong Condition Type

**❌ WRONG** - Using HostAndServiceCondition for item-based checks:
```python
# This causes TypeError: HostAndServiceCondition.__init__() got an unexpected keyword argument 'service_name'
condition=HostAndServiceCondition(service_name="ZPool I/O")
```

**✅ CORRECT** - Using HostAndItemCondition for item-based checks:
```python
condition=HostAndItemCondition(item_title=Title("ZPool name"))
```

### Advanced Form Specifications
```python
from cmk.rulesets.v1.form_specs import (
    CascadingSingleChoice,
    CascadingSingleChoiceElement,
    List,
    MultipleChoice,
    MultipleChoiceElement,
    RegularExpression,
    TimeSpan,
    DataSize,
    validators,
)

def _advanced_form_spec():
    return Dictionary(
        title=Title("Advanced Service Configuration"),
        elements={
            "monitoring_mode": DictElement(
                parameter_form=CascadingSingleChoice(
                    title=Title("Monitoring Mode"),
                    elements=[
                        CascadingSingleChoiceElement(
                            name="simple",
                            title=Title("Simple monitoring"),
                            parameter_form=Dictionary(
                                elements={
                                    "threshold": DictElement(
                                        parameter_form=Integer(
                                            title=Title("Threshold"),
                                            prefill=DefaultValue(100),
                                        ),
                                        required=True,
                                    ),
                                },
                            ),
                        ),
                        CascadingSingleChoiceElement(
                            name="advanced",
                            title=Title("Advanced monitoring"),
                            parameter_form=Dictionary(
                                elements={
                                    "thresholds": DictElement(
                                        parameter_form=List(
                                            title=Title("Multiple thresholds"),
                                            element_template=Integer(),
                                            add_element_label=Label("Add threshold"),
                                        ),
                                        required=True,
                                    ),
                                    "regex_filter": DictElement(
                                        parameter_form=RegularExpression(
                                            title=Title("Filter regex"),
                                            prefill=DefaultValue(r".*"),
                                        ),
                                        required=False,
                                    ),
                                },
                            ),
                        ),
                    ],
                    prefill=DefaultValue("simple"),
                ),
                required=True,
            ),
            "timeouts": DictElement(
                parameter_form=Dictionary(
                    title=Title("Timeout Configuration"),
                    elements={
                        "connection_timeout": DictElement(
                            parameter_form=TimeSpan(
                                title=Title("Connection timeout"),
                                prefill=DefaultValue(30.0),
                            ),
                            required=True,
                        ),
                        "read_timeout": DictElement(
                                parameter_form=TimeSpan(
                                title=Title("Read timeout"),
                                prefill=DefaultValue(60.0),
                            ),
                            required=True,
                        ),
                    },
                ),
                required=False,
            ),
            "data_limits": DictElement(
                parameter_form=DataSize(
                    title=Title("Maximum data size"),
                    prefill=DefaultValue(1024 * 1024),  # 1MB
                ),
                required=False,
            ),
        },
    )
```

## Graphing Integration

Create visual representations of your metrics using the `cmk.graphing.v1` API.

### Metric Definitions
```python
# File: ~/local/lib/python3/cmk_addons/plugins/graphing/my_service.py

from cmk.graphing.v1 import Title
from cmk.graphing.v1.metrics import (
    Color,
    DecimalNotation,
    IECNotation,
    Metric,
    StrictPrecision,
    Unit,
)

# Define units
unit_percentage = Unit(DecimalNotation("%"))
unit_bytes = Unit(IECNotation("B"))
unit_seconds = Unit(DecimalNotation("s"))

# Define metrics
metric_my_service_cpu = Metric(
    name="my_service_cpu",
    title=Title("My Service CPU Usage"),
    unit=unit_percentage,
    color=Color.BLUE,
)

metric_my_service_memory = Metric(
    name="my_service_memory",
    title=Title("My Service Memory Usage"),
    unit=unit_bytes,
    color=Color.GREEN,
)

metric_my_service_response_time = Metric(
    name="my_service_response_time",
    title=Title("My Service Response Time"),
    unit=unit_seconds,
    color=Color.ORANGE,
)
```

### Graph Definitions
```python
from cmk.graphing.v1.graphs import (
    Graph,
    MinimalRange,
    Bidirectional,
)

# Simple graph
graph_my_service_performance = Graph(
    name="my_service_performance",
    title=Title("My Service Performance"),
    compound_lines=[
        "my_service_cpu",
        "my_service_memory",
    ],
    simple_lines=[
        "my_service_response_time",
    ],
    # mandatory! None is not allowed!
    minimal_range=MinimalRange(
        lower=0,
        upper=100,
    ),
)

# Bidirectional graph (for network traffic, etc.)
graph_my_service_network = Bidirectional(
    name="my_service_network",
    title=Title("My Service Network Traffic"),
    lower=Graph(
        name="my_service_network_lower",
        title=Title("Inbound Traffic"),
        compound_lines=["my_service_bytes_in"],
    ),
    upper=Graph(
        name="my_service_network_upper",
        title=Title("Outbound Traffic"), 
        compound_lines=["my_service_bytes_out"],
    ),
)
```

### Perfometer Definitions
```python
from cmk.graphing.v1.perfometers import (
    Perfometer,
    FocusRange,
    Closed,
    Stacked,
)

# Simple perfometer
perfometer_my_service_cpu = Perfometer(
    name="my_service_cpu",
    focus_range=FocusRange(
        lower=Closed(0),
        upper=Closed(100),
    ),
    segments=[
        "my_service_cpu",
    ],
)

# Stacked perfometer
perfometer_my_service_stacked = Stacked(
    name="my_service_stacked",
    lower=Perfometer(
        name="my_service_cpu_lower",
        focus_range=FocusRange(
            lower=Closed(0),
            upper=Closed(100),
        ),
        segments=["my_service_cpu"],
    ),
    upper=Perfometer(
        name="my_service_memory_upper",
        focus_range=FocusRange(
            lower=Closed(0),
            upper=Closed(100),
        ),
        segments=["my_service_memory"],
    ),
)
```

## Best Practices

### Error Handling
```python
from cmk.agent_based.v2 import Result, State

def parse_my_service(string_table: list[list[str]]) -> Dict[str, Any]:
    """Robust parsing with error handling"""
    parsed_data = {}
    
    try:
        for line_num, line in enumerate(string_table, 1):
            if len(line) < 2:
                continue  # Skip malformed lines
            
            key, value = line[0], line[1]
            
            # Type conversion with error handling
            try:
                if value.replace('.', '', 1).isdigit():
                    parsed_data[key] = float(value) if '.' in value else int(value)
                elif value.lower() in ('true', 'false'):
                    parsed_data[key] = value.lower() == 'true'
                else:
                    parsed_data[key] = value
            except (ValueError, AttributeError):
                parsed_data[key] = value  # Keep as string if conversion fails
                
    except Exception as e:
        # Log parsing errors but don't fail completely
        parsed_data['_parse_error'] = str(e)
    
    return parsed_data

def check_my_service_robust(item: str, section: Dict[str, Any]) -> CheckResult:
    """Check function with comprehensive error handling"""
    # Handle parsing errors
    if '_parse_error' in section:
        yield Result(
            state=State.UNKNOWN,
            summary=f"Parse error: {section['_parse_error']}"
        )
        return
    
    # Handle missing data
    if not section:
        yield Result(
            state=State.UNKNOWN,
            summary="No data available"
        )
        return
    
    # Handle missing specific metrics
    if 'metric_value' not in section:
        yield Result(
            state=State.UNKNOWN,
            summary="Required metric not found"
        )
        return
    
    try:
        value = section['metric_value']
        
        # Validate data types
        if not isinstance(value, (int, float)):
            yield Result(
                state=State.UNKNOWN,
                summary=f"Invalid data type: {type(value).__name__}"
            )
            return
        
        # Perform checks
        if value < 0:
            yield Result(
                state=State.WARN,
                summary=f"Negative value detected: {value}"
            )
        else:
            yield Result(
                state=State.OK,
                summary=f"Value: {value}"
            )
        
        yield Metric("my_metric", value)
        
    except Exception as e:
        yield Result(
            state=State.UNKNOWN,
            summary=f"Check failed: {e}"
        )
```

### Performance Considerations
- Keep agent plugins lightweight and fast
- Use appropriate data structures for large datasets
- Implement timeouts for external calls
- Cache expensive operations when possible
- Avoid blocking operations in check functions

### Testing
```python
import pytest
from typing import List

def test_parse_function():
    """Test parsing function with various inputs"""
    # Test normal data
    test_data = [["key1", "value1"], ["key2", "123"], ["key3", "45.67"]]
    result = parse_my_service(test_data)
    
    assert result == {
        "key1": "value1",
        "key2": 123,
        "key3": 45.67,
    }
    
    # Test malformed data
    malformed_data = [["key1"], ["key2", "value2", "extra"], []]
    result = parse_my_service(malformed_data)
    
    assert "key1" not in result  # Should skip incomplete lines
    assert result.get("key2") == "value2"  # Should handle extra fields
    
    # Test empty data
    empty_result = parse_my_service([])
    assert empty_result == {}

def test_check_function():
    """Test check function logic"""
    # Test normal operation
    section = {"metric_value": 50}
    results = list(check_my_service("test_item", section))
    
    assert len(results) >= 1
    assert any(r.state == State.OK for r in results if isinstance(r, Result))
    
    # Test missing data
    empty_section = {}
    results = list(check_my_service("test_item", empty_section))
    
    assert any(r.state == State.UNKNOWN for r in results if isinstance(r, Result))
```

### Documentation

CheckMK plugins should include proper documentation in the checkman format for user reference.

#### Creating Checkman Documentation
Create documentation files in the `checkman/` directory:

```
~/local/lib/python3/cmk_addons/plugins/
├── agent_based/
├── checkman/              # Plugin documentation  
│   └── my_service         # Documentation file (no extension)
├── graphing/
└── rulesets/
```

#### Checkman Format
CheckMK uses a simple text-based format for plugin documentation:

```
# File: ~/local/lib/python3/cmk_addons/plugins/checkman/my_service

title: My Service: Performance Monitoring
agents: linux
catalog: os/services
license: GPL
distribution: check_mk
description:
 This check monitors the performance and status of My Service running on
 Linux systems. It tracks key metrics including CPU usage, memory consumption,
 and response times.

 The check uses data collected by the {my_service} agent plugin, which
 queries the service's status API and performance counters.

 The plugin automatically discovers running instances of My Service and
 creates individual services for monitoring. Each service provides detailed
 performance metrics and configurable threshold levels.

 This check requires My Service version 2.0 or later and the service API
 to be enabled in the configuration.

item:
 The service instance name (e.g. {main}, {worker-1})

discovery:
 One service is created for each running My Service instance that responds
 to status queries. Services are named "My Service <instance_name>".

cluster:
 In cluster environments, the check aggregates metrics from all cluster
 nodes and reports the combined status and performance data.
```

#### Checkman Elements

**Required Fields:**
- `title:` - Short descriptive title for the check
- `agents:` - Supported agent types (linux, windows, snmp, etc.)
- `catalog:` - Category path for organization (os/storage, app/databases, etc.)
- `description:` - Detailed description of functionality

**Optional Fields:**
- `license:` - License information (GPL, MIT, etc.)
- `distribution:` - Distribution method (check_mk, exchange, etc.)
- `item:` - Description of service items if check uses items
- `discovery:` - How services are discovered and created
- `cluster:` - Behavior in cluster environments
- `perfdata:` - Description of performance metrics
- `parameters:` - Configuration parameters available

#### Example: Complete Checkman Documentation

```
title: SMART: Error Counter Monitoring
agents: linux
catalog: os/storage
license: GPL
distribution: check_mk
description:
 This check monitors SMART error counters on storage devices that support
 SCSI error counter logs. It tracks detailed error statistics including
 corrected and uncorrected errors across read, write, and verify operations.

 The check provides both absolute error counts and normalized error rates
 per terabyte of data processed, allowing for comprehensive storage health
 monitoring and trend analysis.

 This check requires the {smartmontools} package to be installed on the
 monitored host. The agent plugin uses {smartctl} to collect error counter
 data from storage devices.

 The plugin automatically discovers devices that support SCSI error counter
 logs (typically enterprise SATA/SAS drives and many enterprise SSDs).
 Consumer SSDs and USB drives often do not support this feature and will
 not be monitored.

 Each operation type (read, write, verify) generates detailed metrics:
 errors corrected by ECC fast/delayed, errors corrected by rereads/rewrites,
 total corrected errors, correction algorithm invocations, bytes processed,
 and total uncorrected errors.

item:
 The device path (e.g. {/dev/sda})

discovery:
 One service is created for each storage device that supports SCSI error
 counter logs and has meaningful error counter data available. Services
 are named "SMART Errors <device_path>" (e.g. "SMART Errors /dev/sda").

perfdata:
 The check provides detailed metrics for each operation type:
 - Absolute error counts (corrected/uncorrected by type)
 - Correction algorithm invocations
 - Bytes processed per operation
 - Relative error rates per TB processed

parameters:
 Operation-specific thresholds can be configured for each error type:
 - Uncorrected errors (absolute counts)
 - ECC fast/delayed corrected errors (absolute counts)  
 - Rereads/rewrites corrected errors (absolute counts)
 - Correction algorithm invocations (absolute counts)
 - Overall uncorrected error rate per TB processed
```

#### Documentation Best Practices
- Use clear, concise language
- Include specific technical requirements
- Explain discovery behavior
- Document all configuration options
- Provide examples where helpful
- Reference related tools and dependencies
- Use CheckMK markup conventions ({tool_name} for tools, etc.)

## Deployment

### Manual Installation
1. Copy agent plugin to `/usr/lib/check_mk_agent/plugins/`
2. Make executable: `chmod +x plugin_name`
3. Copy check plugin to `~/local/lib/python3/cmk_addons/plugins/agent_based/`
4. Copy ruleset definitions to `~/local/lib/python3/cmk_addons/plugins/rulesets/`
5. Copy graphing definitions to `~/local/lib/python3/cmk_addons/plugins/graphing/`
6. Restart CheckMK: `cmk -R` or `omd restart`

### Using Agent Bakery
1. Create bakery plugin in `~/local/lib/check_mk/base/cee/plugins/bakery/`
2. Create rule set in `~/local/lib/python3/cmk_addons/plugins/rulesets/`
3. Configure via CheckMK GUI under "Agents > Agent rules"
4. Bake and deploy agents via "Agents > Agent bakery"

### Package Distribution
```bash
# Create MKP package
cd ~/local/lib/python3/cmk_addons/plugins/
tar -czf my_service_plugin.tar.gz agent_based/ bakery/ rulesets/ graphing/

# Install on other CheckMK instances
mkp install my_service_plugin.tar.gz
```

## Debugging

### Common Issues
- **Plugin not discovered**: Check file permissions, syntax, and entry point prefixes
- **No data**: Verify agent plugin output format and section headers
- **Parse errors**: Add debug logging to parse function
- **Service not created**: Check discovery function logic and section data
- **Import errors**: Verify API imports and module structure

### Debugging Tools
```bash
# Test agent plugin directly
/usr/lib/check_mk_agent/plugins/my_service

# Test agent output
check_mk_agent | grep -A 10 "<<<my_service>>>"

# Test check plugin discovery
cmk -v --detect-plugins hostname

# Test check plugin execution
cmk -v --debug hostname

# View parsed agent data
cmk -d hostname

# Test specific service
cmk -v --debug --checks=my_service hostname

# Validate plugin syntax
python3 -m py_compile ~/local/lib/python3/cmk_addons/plugins/agent_based/my_service.py
```

### Logging and Debugging
```python
import logging

# Set up logging
logger = logging.getLogger("cmk.base.plugins.agent_based.my_service")

def parse_my_service(string_table: list[list[str]]) -> Dict[str, Any]:
    """Parse with debugging"""
    logger.debug("Parsing data: %s", string_table)
    
    try:
        parsed_data = {}
        for i, line in enumerate(string_table):
            logger.debug("Processing line %d: %s", i, line)
            # Your parsing logic here
            
        logger.debug("Parsed data: %s", parsed_data)
        return parsed_data
        
    except Exception as e:
        logger.error("Parse error: %s", e, exc_info=True)
        return {"_error": str(e)}

def check_my_service(item: str, section: Dict[str, Any]) -> CheckResult:
    """Check with debugging"""
    logger.debug("Checking item %s with section: %s", item, section)
    
    if "_error" in section:
        logger.error("Section has parse error: %s", section["_error"])
        yield Result(state=State.UNKNOWN, summary=f"Parse error: {section['_error']}")
        return
    
    # Your check logic here
    logger.debug("Check completed for item %s", item)
```

### Testing in Development
```python
# File: test_my_service.py

import pytest
from typing import List
from cmk.agent_based.v2 import Result, State, Service

# Import your plugin functions
from cmk_addons.plugins.agent_based.my_service import (
    parse_my_service,
    discover_my_service,
    check_my_service,
)

class TestMyService:
    def test_parse_normal_data(self):
        """Test parsing with normal data"""
        test_data = [
            ["metric_value", "50"],
            ["status", "running"],
            ["version", "1.0.0"],
        ]
        
        result = parse_my_service(test_data)
        
        assert result["metric_value"] == 50
        assert result["status"] == "running"
        assert result["version"] == "1.0.0"
    
    def test_parse_malformed_data(self):
        """Test parsing with malformed data"""
        test_data = [
            ["incomplete_line"],
            ["valid_key", "valid_value"],
            [],  # Empty line
        ]
        
        result = parse_my_service(test_data)
        
        assert "valid_key" in result
        assert "incomplete_line" not in result
    
    def test_discovery(self):
        """Test service discovery"""
        section = {"metric_value": 50, "status": "running"}
        
        services = list(discover_my_service(section))
        
        assert len(services) == 1
        assert isinstance(services[0], Service)
    
    def test_check_ok_state(self):
        """Test check function with OK state"""
        section = {"metric_value": 30}
        
        results = list(check_my_service("test_item", section))
        
        assert len(results) > 0
        assert any(r.state == State.OK for r in results if isinstance(r, Result))
    
    def test_check_missing_data(self):
        """Test check function with missing data"""
        section = {}
        
        results = list(check_my_service("test_item", section))
        
        assert len(results) > 0
        assert any(r.state == State.UNKNOWN for r in results if isinstance(r, Result))

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### Plugin Validation
```python
# File: validate_plugin.py

import sys
import importlib.util
from pathlib import Path

def validate_plugin(plugin_path: str) -> bool:
    """Validate plugin structure and imports"""
    try:
        # Check if file exists
        if not Path(plugin_path).exists():
            print(f"ERROR: Plugin file not found: {plugin_path}")
            return False
        
        # Try to import the module
        spec = importlib.util.spec_from_file_location("plugin", plugin_path)
        if spec is None:
            print(f"ERROR: Cannot load plugin spec: {plugin_path}")
            return False
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check for required components
        required_components = [
            "agent_section_",  # Should have agent section
            "check_plugin_",   # Should have check plugin
        ]
        
        found_components = []
        for attr_name in dir(module):
            for component in required_components:
                if attr_name.startswith(component):
                    found_components.append(component)
        
        if len(found_components) == len(required_components):
            print(f"SUCCESS: Plugin validation passed: {plugin_path}")
            return True
        else:
            missing = set(required_components) - set(found_components)
            print(f"ERROR: Missing components: {missing}")
            return False
            
    except Exception as e:
        print(f"ERROR: Plugin validation failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_plugin.py <plugin_path>")
        sys.exit(1)
    
    plugin_path = sys.argv[1]
    if validate_plugin(plugin_path):
        sys.exit(0)
    else:
        sys.exit(1)
```

## Advanced Topics

### Inventory Integration
```python
from cmk.agent_based.v2 import InventoryPlugin, InventoryResult, TableRow, Attributes

def inventory_my_service(section: Dict[str, Any]) -> InventoryResult:
    """Create inventory entries for the HW/SW inventory"""
    if not section:
        return
    
    # Add attributes to inventory
    yield Attributes(
        path=["software", "applications", "my_service"],
        inventory_attributes={
            "version": section.get("version", "unknown"),
            "status": section.get("status", "unknown"),
            "install_date": section.get("install_date", "unknown"),
        },
    )
    
    # Add table rows for detailed information
    if "components" in section:
        for component in section["components"]:
            yield TableRow(
                path=["software", "applications", "my_service", "components"],
                key_columns={
                    "name": component.get("name", "unknown"),
                },
                inventory_columns={
                    "version": component.get("version", "unknown"),
                    "status": component.get("status", "unknown"),
                    "size": component.get("size", 0),
                },
            )

# Create inventory plugin
inventory_plugin_my_service = InventoryPlugin(
    name="my_service",
    inventory_function=inventory_my_service,
    sections=["my_service"],
)
```

### Cluster Support
```python
from cmk.agent_based.v2 import clusterize
from typing import Mapping

def cluster_check_my_service(
    item: str, 
    section: Mapping[str, Dict[str, Any]]
) -> CheckResult:
    """Check function for cluster services"""
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data from cluster nodes")
        return
    
    # Aggregate data from all cluster nodes
    total_value = 0
    node_states = []
    
    for node_name, node_data in section.items():
        if node_data and "metric_value" in node_data:
            total_value += node_data["metric_value"]
            node_states.append((node_name, node_data.get("status", "unknown")))
    
    # Determine overall cluster state
    if not node_states:
        yield Result(state=State.UNKNOWN, summary="No valid data from cluster nodes")
        return
    
    # Report cluster summary
    yield Result(
        state=State.OK,
        summary=f"Cluster total: {total_value} (from {len(node_states)} nodes)"
    )
    
    # Report individual node states
    for node_name, status in node_states:
        yield Result(
            state=State.OK,
            notice=f"Node {node_name}: {status}"
        )
    
    # Add cluster metric
    yield Metric("cluster_total", total_value)

# Create check plugin with cluster support
check_plugin_my_service_cluster = CheckPlugin(
    name="my_service_cluster",
    service_name="My Service Cluster",
    sections=["my_service"],
    discovery_function=discover_my_service,
    check_function=check_my_service,
    cluster_check_function=cluster_check_my_service,
)
```

### SNMP-based Plugins
```python
from cmk.agent_based.v2 import (
    SNMPSection,
    SimpleSNMPSection,
    SNMPTree,
    SNMPDetectSpecification,
    all_of,
    exists,
    startswith,
    OIDEnd,
)

# Simple SNMP section
snmp_section_my_device = SimpleSNMPSection(
    name="my_device",
    parse_function=parse_my_device,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.12345.1.1",
        oids=[
            "1.0",  # Device name
            "2.0",  # Device status
            "3.0",  # Device temperature
        ],
    ),
    detect=SNMPDetectSpecification(
        all_of(
            exists(".1.3.6.1.4.1.12345.1.1.1.0"),
            startswith(".1.3.6.1.2.1.1.1.0", "My Device"),
        ),
    ),
)

# Advanced SNMP section with table
snmp_section_my_device_table = SNMPSection(
    name="my_device_table",
    parse_function=parse_my_device_table,
    fetch=[
        SNMPTree(
            base=".1.3.6.1.4.1.12345.1.2.1",
            oids=[
                OIDEnd(),
                "2",  # Interface name
                "3",  # Interface status
                "4",  # Interface speed
            ],
        ),
    ],
    detect=SNMPDetectSpecification(
        all_of(
            exists(".1.3.6.1.4.1.12345.1.1.1.0"),
            startswith(".1.3.6.1.2.1.1.1.0", "My Device"),
        ),
    ),
)

def parse_my_device_table(string_table: list[list[str]]) -> Dict[str, Any]:
    """Parse SNMP table data"""
    interfaces = {}
    
    for line in string_table:
        if len(line) >= 4:
            index, name, status, speed = line
            interfaces[index] = {
                "name": name,
                "status": status,
                "speed": int(speed) if speed.isdigit() else 0,
            }
    
    return interfaces
```

### Host Labels
```python
from cmk.agent_based.v2 import HostLabel

def host_label_my_service(section: Dict[str, Any]) -> HostLabelGenerator:
    """Generate host labels based on service data"""
    if not section:
        return
    
    # Add labels based on service characteristics
    if "version" in section:
        yield HostLabel("my_service_version", section["version"])
    
    if "type" in section:
        yield HostLabel("my_service_type", section["type"])
    
    if section.get("cluster_mode", False):
        yield HostLabel("my_service_cluster", "yes")
    
    # Conditional labels
    if section.get("metric_value", 0) > 1000:
        yield HostLabel("my_service_high_load", "yes")

# Add host label function to agent section
agent_section_my_service_with_labels = AgentSection(
    name="my_service_labels",
    parse_function=parse_my_service,
    host_label_function=host_label_my_service,
)
```

## Complete Example: Temperature Monitoring Plugin

Here's a complete example that demonstrates all the concepts covered in this guide:

### Agent Plugin
```bash
#!/bin/bash
# File: /usr/lib/check_mk_agent/plugins/temperature_monitor

echo "<<<temperature_monitor>>>"

# Simulate temperature readings
echo "sensor_1 25.5 OK"
echo "sensor_2 67.8 WARN"
echo "sensor_3 89.2 CRIT"
echo "ambient 22.1 OK"
echo "system_info Temperature Monitor v1.2.0"
```

### Complete Check Plugin
```python
# File: ~/local/lib/python3/cmk_addons/plugins/agent_based/temperature_monitor.py

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
    Metric,
    render,
    check_levels,
    HostLabel,
)
from typing import Any, Dict, Mapping

def parse_temperature_monitor(string_table: list[list[str]]) -> Dict[str, Any]:
    """Parse temperature monitor data"""
    sensors = {}
    system_info = {}
    
    for line in string_table:
        if len(line) >= 3:
            if line[0] == "system_info":
                system_info["version"] = " ".join(line[1:])
            else:
                sensor_name, temp_str, status = line[0], line[1], line[2]
                try:
                    temperature = float(temp_str)
                    sensors[sensor_name] = {
                        "temperature": temperature,
                        "status": status,
                    }
                except ValueError:
                    continue
    
    return {"sensors": sensors, "system_info": system_info}

def host_label_temperature_monitor(section: Dict[str, Any]) -> HostLabelGenerator:
    """Generate host labels"""
    if section.get("system_info", {}).get("version"):
        yield HostLabel("temperature_monitor", "yes")
        version = section["system_info"]["version"]
        if "v1.2" in version:
            yield HostLabel("temperature_monitor_version", "v1.2")

# Create agent section
agent_section_temperature_monitor = AgentSection(
    name="temperature_monitor",
    parse_function=parse_temperature_monitor,
    host_label_function=host_label_temperature_monitor,
)

def discover_temperature_monitor(section: Dict[str, Any]) -> DiscoveryResult:
    """Discover temperature sensors"""
    for sensor_name in section.get("sensors", {}):
        yield Service(item=sensor_name)

def check_temperature_monitor(
    item: str, 
    params: Mapping[str, Any], 
    section: Dict[str, Any]
) -> CheckResult:
    """Check temperature sensor"""
    sensors = section.get("sensors", {})
    
    if item not in sensors:
        yield Result(state=State.UNKNOWN, summary=f"Sensor {item} not found")
        return
    
    sensor_data = sensors[item]
    temperature = sensor_data["temperature"]
    
    # Use check_levels for automatic threshold checking
    yield from check_levels(
        value=temperature,
        metric_name="temperature",
        levels_upper=params.get("temperature_levels"),
        levels_lower=params.get("temperature_levels_lower"),
        render_func=lambda x: f"{x:.1f}°C",
        label="Temperature",
    )
    
    # Additional status information
    sensor_status = sensor_data.get("status", "UNKNOWN")
    if sensor_status in ["WARN", "CRIT"]:
        yield Result(
            state=State.WARN if sensor_status == "WARN" else State.CRIT,
            notice=f"Sensor reports status: {sensor_status}"
        )

# Create check plugin
check_plugin_temperature_monitor = CheckPlugin(
    name="temperature_monitor",
    service_name="Temperature %s",
    sections=["temperature_monitor"],
    discovery_function=discover_temperature_monitor,
    check_function=check_temperature_monitor,
    check_default_parameters={
        "temperature_levels": (80.0, 90.0),
        "temperature_levels_lower": (10.0, 5.0),
    },
    check_ruleset_name="temperature_monitor",
)
```

### Ruleset Configuration
```python
# File: ~/local/lib/python3/cmk_addons/plugins/rulesets/temperature_monitor.py

from cmk.rulesets.v1 import Title, Help
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    Float,
    SimpleLevels,
    LevelDirection,
    DefaultValue,
)
from cmk.rulesets.v1.rule_specs import (
    CheckParameters,
    HostAndServiceCondition,
    Topic,
)

def _temperature_monitor_form_spec():
    return Dictionary(
        title=Title("Temperature Monitor Configuration"),
        elements={
            "temperature_levels": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Upper temperature levels"),
                    help_text=Help("Temperature levels for warning and critical states"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Float(unit_symbol="°C"),
                    prefill_fixed_levels=DefaultValue((80.0, 90.0)),
                ),
                required=True,
            ),
            "temperature_levels_lower": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Lower temperature levels"),
                    help_text=Help("Temperature levels for low temperature warnings"),
                    level_direction=LevelDirection.LOWER,
                    form_spec_template=Float(unit_symbol="°C"),
                    prefill_fixed_levels=DefaultValue((10.0, 5.0)),
                ),
                required=False,
            ),
        },
    )

rule_spec_temperature_monitor = CheckParameters(
    title=Title("Temperature Monitor"),
    topic=Topic.ENVIRONMENT,
    name="temperature_monitor",
    parameter_form=_temperature_monitor_form_spec,
    condition=HostAndServiceCondition(service_name="Temperature"),
)
```

### Graphing Configuration
```python
# File: ~/local/lib/python3/cmk_addons/plugins/graphing/temperature_monitor.py

from cmk.graphing.v1 import Title
from cmk.graphing.v1.metrics import (
    Color,
    DecimalNotation,
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

# Define unit
unit_celsius = Unit(DecimalNotation("°C"))

# Define metric
metric_temperature = Metric(
    name="temperature",
    title=Title("Temperature"),
    unit=unit_celsius,
    color=Color.BLUE,
)

# Define graph
graph_temperature = Graph(
    name="temperature",
    title=Title("Temperature"),
    simple_lines=[
        "temperature",
    ],
    minimal_range=MinimalRange(
        lower=0,
        upper=100,
    ),
)

# Define perfometer
perfometer_temperature = Perfometer(
    name="temperature",
    focus_range=FocusRange(
        lower=Closed(0),
        upper=Closed(100),
    ),
    segments=[
        "temperature",
    ],
)
```

### Bakery Integration

#### Bakery Plugin
```python
# File: ~/local/lib/check_mk/base/cee/plugins/bakery/temperature_monitor.py

from cmk.base.plugins.bakery.bakery_api.v1 import (
    register,
    Plugin,
    OS,
)
from pathlib import Path
from typing import Any, Dict

def get_temperature_monitor_files(conf: Dict[str, Any]):
    """Files function for temperature monitor bakery plugin"""
    if conf is None or not conf.get("enabled", True):
        return
    
    # Get configuration values
    interval = conf.get("interval", 60)
    
    # Generate plugin using source reference
    # This will automatically find the agent plugin in local/share/check_mk/agents/plugins/
    yield Plugin(
        base_os=OS.LINUX,
        source=Path('temperature_monitor'),  # References local/share/check_mk/agents/plugins/temperature_monitor
        target=Path('temperature_monitor'),  # Deploys to /usr/lib/check_mk_agent/plugins/temperature_monitor
        interval=interval,
    )

# Register the bakery plugin using the official API
register.bakery_plugin(
    name="temperature_monitor",
    files_function=get_temperature_monitor_files,
)
```

#### Bakery Ruleset (CheckMK 2.3 - Modern API)
```python
# File: ~/local/lib/python3/cmk_addons/plugins/temperature_monitor/rulesets/ruleset_temperature_monitor_bakery.py

from cmk.rulesets.v1 import Label, Title, Help
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DefaultValue,
    DictElement,
    Dictionary,
    TimeSpan,
    TimeMagnitude
)
from cmk.rulesets.v1.rule_specs import AgentConfig, Topic

def _parameter_form_temperature_monitor():
    """Configuration interface for temperature monitor agent plugin"""
    return Dictionary(
        title=Title("Temperature Monitor Agent Plugin"),
        help_text=Help("Configure the temperature monitoring agent plugin."),
        elements={
            "enabled": DictElement(
                parameter_form=BooleanChoice(
                    title=Title("Enable temperature monitoring"),
                    label=Label("Enable monitoring"),
                    prefill=DefaultValue(True),
                )
            ),
            "interval": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Execution interval"),
                    label=Label("How often to collect temperature data"),
                    help_text=Help("0 means every agent run."),
                    displayed_magnitudes=[TimeMagnitude.SECOND, TimeMagnitude.MINUTE],
                    prefill=DefaultValue(60.0),
                )
            ),
        }
    )

# Register the bakery rule specification
rule_spec_temperature_monitor_bakery = AgentConfig(
    name="temperature_monitor",
    title=Title("Temperature Monitor Agent Plugin"),
    topic=Topic.GENERAL,
    parameter_form=_parameter_form_temperature_monitor,
)
```

## Conclusion

This comprehensive guide provides everything needed to develop robust agent-based check plugins for CheckMK 2.3.0. The key points to remember:

1. **Use the v2 API** - CheckMK 2.3.0 uses the discovery-based `cmk.agent_based.v2` API
2. **Proper error handling** - Always handle missing data and parsing errors gracefully
3. **Comprehensive testing** - Test with various data scenarios and edge cases
4. **Follow conventions** - Use proper naming, structure, and documentation
5. **Leverage all APIs** - Combine agent-based, rulesets, graphing, and bakery APIs for complete solutions

For additional resources:
- CheckMK Exchange for sharing plugins
- CheckMK GitHub repository for contributing
- CheckMK documentation for API references
- Community forums for support and discussion
- Local API documentation in `check_mk/plugin-api/html/`

## CheckMK Color Class Constants

The `cmk.graphing.v1.Color` class provides predefined color constants for use in graphing definitions. These constants ensure consistent color usage across CheckMK visualizations.

### Available Color Constants

The following color constants are available in the Color class:

#### Red Colors
- `Color.LIGHT_RED` - Light red shade
- `Color.RED` - Standard red
- `Color.DARK_RED` - Dark red shade

#### Orange Colors  
- `Color.LIGHT_ORANGE` - Light orange shade
- `Color.ORANGE` - Standard orange
- `Color.DARK_ORANGE` - Dark orange shade

#### Yellow Colors
- `Color.LIGHT_YELLOW` - Light yellow shade
- `Color.YELLOW` - Standard yellow
- `Color.DARK_YELLOW` - Dark yellow shade

#### Green Colors
- `Color.LIGHT_GREEN` - Light green shade
- `Color.GREEN` - Standard green
- `Color.DARK_GREEN` - Dark green shade

#### Blue Colors
- `Color.LIGHT_BLUE` - Light blue shade
- `Color.BLUE` - Standard blue
- `Color.DARK_BLUE` - Dark blue shade

#### Cyan Colors
- `Color.LIGHT_CYAN` - Light cyan shade
- `Color.CYAN` - Standard cyan
- `Color.DARK_CYAN` - Dark cyan shade

#### Purple Colors
- `Color.LIGHT_PURPLE` - Light purple shade
- `Color.PURPLE` - Standard purple
- `Color.DARK_PURPLE` - Dark purple shade

#### Pink Colors
- `Color.LIGHT_PINK` - Light pink shade
- `Color.PINK` - Standard pink
- `Color.DARK_PINK` - Dark pink shade

#### Brown Colors
- `Color.LIGHT_BROWN` - Light brown shade
- `Color.BROWN` - Standard brown
- `Color.DARK_BROWN` - Dark brown shade

#### Gray Colors
- `Color.LIGHT_GRAY` - Light gray shade
- `Color.GRAY` - Standard gray
- `Color.DARK_GRAY` - Dark gray shade

#### Monochrome Colors
- `Color.BLACK` - Black
- `Color.WHITE` - White

### Usage Example

```python
from cmk.graphing.v1 import Color
from cmk.graphing.v1.metrics import Metric

# Define a metric with a specific color
metric_example = Metric(
    name="example_metric",
    title=Title("Example Metric"),
    unit=unit_count,
    color=Color.BLUE,  # Use predefined color constant
)
```

### Important Notes

- Always use the predefined Color constants rather than creating custom color values
- Color constants like `Color.MAGENTA` and `Color.NAVY` do not exist and will cause errors
- The Color class ensures consistent theming across CheckMK's graphing system
- Colors are automatically adapted for different themes (light/dark mode)