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

### Rulesets (CheckMK 2.3 rulesets API)
```python
from cmk.rulesets.v1.form_specs import Dictionary, DictElement, SimpleLevels, TimeSpan
from cmk.rulesets.v1.rule_specs import CheckParameters, AgentConfig, HostAndItemCondition
```

### Graphing (CheckMK 2.3 graphing API)
```python
from cmk.graphing.v1 import metrics, graphs, perfometers, translations
```

## Metrics Generated

All metric names start with `oposs_smart_error_`. The unprefixed names used
up to 1.0.5 are mapped onto them in `graphing/translations.py`, which keeps the
old RRD history in the graphs.

### Per Operation (read/write/verify) - 6 metrics each:
- `oposs_smart_error_{operation}_errors_corrected_by_eccfast`
- `oposs_smart_error_{operation}_errors_corrected_by_eccdelayed`
- `oposs_smart_error_{operation}_errors_corrected_by_rereads_rewrites`
- `oposs_smart_error_{operation}_correction_algorithm_invocations`
- `oposs_smart_error_{operation}_bytes_processed`
- `oposs_smart_error_{operation}_total_uncorrected_errors`

### Per Operation Rate (per TB) - 4 metrics each:
- The first four above with `_per_tb`, divided by TB processed

### Other:
- `oposs_smart_error_grown_defects`
- `oposs_smart_bms_*` for the background scan service

## Key Implementation Details

### Agent Plugin
- Uses `smartctl --json --scan` to discover devices
- Uses one `smartctl --json=c --info --log=error --log=background --attributes -d <type>` call per device
- Sends at most the newest 50 background scan medium error entries per device and counts the rest
- Filters devices without SCSI error counter logs
- With `-n standby,3` smartctl exits with 3 for a sleeping disk and reads nothing,
  not even the serial (bits 0 and 1 never come together otherwise). The agent then
  prints `<dev>|STANDBY|<json>` with the skip count and the identity from the last
  read, kept in `$MK_VARDIR/oposs_smart_error.state.json`, so the check keeps the
  services. A STANDBY line without a serial creates no service
- Outputs JSON data with pipe separator (sep=124)

### Error Handling
- Graceful handling of missing smartctl
- Skips devices without error logs (common for consumer SSDs)
- Validates JSON data structure
- When smartctl gives up (exit bit 0 or 1) it reruns the command without `--json`,
  because smartctl 7.4 prints the reason only as text, and appends the drive
  identity (serial, model, transport) as a 4th field: `<dev>|ERROR|<reason>|<json>`
- The check discovers such a failed drive only with a serial and SAS transport,
  which keeps empty card readers and USB bridges out

### Bakery Integration
- Deploys `local/share/check_mk/agents/plugins/oposs_smart_error` unchanged
- Writes the timeout to `oposs_smart_error.json` in `$MK_CONFDIR`, which the agent reads
- Passes the execution interval to the plugin (asynchronous execution)

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

### Ruleset Parameters (`oposs_smart_error`)
SimpleLevels per operation, `{operation}` is read, write or verify:
- `{operation}_uncorrected_errors_abs`
- `{operation}_eccfast_errors_abs`
- `{operation}_eccdelayed_errors_abs`
- `{operation}_rereads_rewrites_errors_abs`
- `{operation}_algorithm_invocations_abs`
- `grown_defects_abs` (one per drive)

### Bakery Parameters
- `timeout`: timeout for each smartctl call in seconds (default: 5)
- `interval`: execution interval in seconds (default: 1800)
- `standby`: `skip` (default) adds `-n standby,3` to the smartctl call, `wake` does not
- `wake_after`: read a sleeping disk after this many skips in a row (default: 0, never)

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
- Default: any uncorrected error = CRITICAL (levels 1/1); corrected errors,
  algorithm invocations and grown defects are reported OK
- Configurable via ruleset parameters, evaluated with `check_levels()`

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