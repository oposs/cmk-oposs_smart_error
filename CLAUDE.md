# CLAUDE.md - Development Notes

## Project Overview
CheckMK OPOSS SMART Error Monitoring Plugin for CheckMK 2.3 - monitors SCSI error counter logs from storage devices.

## Architecture

### Components
- **Agent Plugin**: `local/share/check_mk/agents/plugins/oposs_smart_error` - Python script that runs on monitored hosts
- **Check Plugin**: `local/lib/python3/cmk_addons/plugins/oposs_smart_error/agent_based/oposs_smart_error.py` - Server-side processing using cmk.agent_based.v2
- **Documentation**: `local/lib/python3/cmk_addons/plugins/oposs_smart_error/checkman/oposs_smart_error` - CheckMK plugin documentation
- **Rulesets**: `local/lib/python3/cmk_addons/plugins/oposs_smart_error/rulesets/oposs_smart_error.py` - GUI configuration for thresholds
- **Graphing**: `local/lib/python3/cmk_addons/plugins/oposs_smart_error/graphing/oposs_smart_error.py` - Metrics and graph definitions
- **Bakery**: `local/lib/python3/cmk/base/cee/plugins/bakery/oposs_smart_error.py` - Automatic agent deployment

### Data Flow
1. Agent plugin runs `smartctl` commands to collect SMART data
2. Outputs structured data with section header `<<<oposs_smart_error:sep(124)>>>`
3. Check plugin parses data and generates metrics/service states
4. Graphing component visualizes metrics over time

## CheckMK 2.3 API Usage

### Agent-Based Plugin (v2 API)
```python
from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin, 
    CheckResult,
    DiscoveryResult,
    Metric,
    Result,
    Service,
    State,
    StringTable,
    render,
)
```

### Key Functions
- `parse_oposs_smart_error()`: Parses agent output into structured data
- `discover_oposs_smart_error()`: Creates services for drives with error logs
- `check_oposs_smart_error()`: Evaluates thresholds and generates metrics

### Rulesets (CheckMK 2.3 GUI API)
```python
from cmk.gui.valuespec import Dictionary, Tuple, Integer, Float
from cmk.gui.plugins.wato.utils import CheckParameterRulespecWithoutItem
```

### Graphing (CheckMK 2.3 Metrics API)
```python
from cmk.gui.plugins.metrics import graph_info, metric_info, perfometer_info
```

## Metrics Generated

### Per Operation (read/write/verify) - 6 metrics each:
- `{operation}_errors_corrected_by_eccfast`
- `{operation}_errors_corrected_by_eccdelayed`
- `{operation}_errors_corrected_by_rereads_rewrites`
- `{operation}_correction_algorithm_invocations`
- `{operation}_bytes_processed`
- `{operation}_total_uncorrected_errors`

### Per Operation Rate (per TB) - 5 metrics each:
- Same as above except bytes_processed, divided by TB processed

### Summary Metrics:
- `total_bytes_processed` (only informational metric - error totals are redundant)

## Key Implementation Details

### Agent Plugin
- Uses `smartctl --json --scan` to discover devices
- Uses `smartctl --json=c --info --log=error` to get device data
- Filters devices without SCSI error counter logs
- Outputs JSON data with pipe separator (sep=124)

### Error Handling
- Graceful handling of missing smartctl
- Skips devices without error logs (common for consumer SSDs)
- Validates JSON data structure
- Provides meaningful error messages

### Bakery Integration
- Reads agent plugin source file from same directory (server_side_calls/oposs_smart_error)
- Can modify timeout parameters based on configuration
- Supports interval configuration for scheduled execution
- Falls back to minimal plugin if source not found

## Testing Commands

### Test Agent Plugin
```bash
# Test locally before deployment
python3 local/share/check_mk/agents/plugins/oposs_smart_error

# Test on target host after deployment
/usr/lib/check_mk_agent/plugins/oposs_smart_error
check_mk_agent | grep -A 10 "<<<oposs_smart_error>>>"
```

### Test Check Plugin
```bash
cmk -v --detect-plugins hostname
cmk -v --debug --checks=oposs_smart_error hostname
```

### Validate Plugin Syntax
```bash
python3 -m py_compile local/lib/python3/cmk_addons/plugins/oposs_smart_error/agent_based/oposs_smart_error.py
```

## Configuration Parameters

### Ruleset Parameters
- `uncorrected_errors_abs`: Tuple (warn, crit) for absolute uncorrected errors
- `eccfast_errors_abs`: Tuple (warn, crit) for ECC fast corrected errors
- `eccdelayed_errors_abs`: Tuple (warn, crit) for ECC delayed corrected errors
- `rereads_rewrites_errors_abs`: Tuple (warn, crit) for rereads/rewrites corrected errors
- `algorithm_invocations_abs`: Tuple (warn, crit) for correction algorithm invocations
- `uncorrected_errors_per_tb`: Tuple (warn, crit) for uncorrected error rate per TB

### Bakery Parameters
- `enabled`: Boolean to enable/disable monitoring
- `timeout`: Integer timeout for smartctl commands (default: 30)
- `interval`: Integer execution interval in seconds (default: 0)

## File Locations

### CheckMK Site Structure
```
~/local/lib/python3/cmk_addons/plugins/oposs_smart_error/
├── agent_based/oposs_smart_error.py
├── checkman/oposs_smart_error        # Plugin documentation
├── graphing/oposs_smart_error.py  
└── rulesets/
    ├── oposs_smart_error.py          # Check parameter rules
    └── ruleset_oposs_smart_error_bakery.py  # Bakery configuration rules

~/local/lib/python3/cmk/base/cee/plugins/bakery/
└── oposs_smart_error.py              # Bakery plugin logic

~/local/share/check_mk/agents/plugins/
└── oposs_smart_error                 # Agent plugin script
```

### Agent Plugin Location
```
/usr/lib/check_mk_agent/plugins/oposs_smart_error
```

## Development Notes

### CheckMK 2.3 vs 2.4 Changes
- Removed all CheckMK 2.4 compatibility code (cmk.rulesets.v1, cmk.server_side_calls.v1)
- Using only CheckMK 2.3 APIs throughout
- Bakery uses function-based approach (`agent_config_oposs_smart_error`)

### API Entry Points
CheckMK 2.3 uses discovery-based plugin registration:
- `agent_section_oposs_smart_error`: AgentSection object
- `check_plugin_oposs_smart_error`: CheckPlugin object
- Function names starting with these prefixes are auto-discovered

### Error States Logic
- Default: Any uncorrected errors = CRITICAL, any corrected errors = WARNING
- Configurable via ruleset parameters
- Uses `max(state, new_state)` to escalate severity
- Rate-based thresholds available for normalized comparison

## Troubleshooting

### Common Issues
- Missing smartmontools package
- Drives without SCSI error counter logs
- Permission issues accessing drives
- Plugin not executable

### Debug Information
- Check agent output section format
- Verify JSON parsing
- Test smartctl commands manually
- Check CheckMK logs for import/syntax errors

## Future Enhancements
- Support for NVMe error logs
- Additional SMART attributes monitoring
- Predictive failure analysis
- Integration with other storage monitoring tools