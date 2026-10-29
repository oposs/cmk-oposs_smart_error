# CheckMK OPOSS SMART Error Monitoring Plugin

A comprehensive CheckMK plugin for monitoring SMART error counters on storage devices. This plugin collects detailed error statistics from drives and provides threshold-based alerting and graphing.

## Features

- **Comprehensive Error Monitoring**: Tracks corrected and uncorrected errors across read, write, and verify operations
- **Detailed Metrics**: Provides both absolute error counts and error rates per TB processed
- **Flexible Thresholds**: Configure warning and critical levels for different error types
- **Graphing**: Error counts and error rates per TB for each operation, and bytes processed
- **Agent Bakery Support**: Automatic deployment and configuration via CheckMK GUI
- **Cross-Platform**: Works on Linux systems with smartmontools

## Requirements

- CheckMK 2.3.0 or later
- `smartmontools` package installed on target hosts
- Optional: `sg3-utils` on target hosts, to show the background scan settings of SAS drives
- Storage devices supporting SCSI error counter logs (most enterprise drives)

## Download

Get the latest version from the [GitHub releases page](https://github.com/oposs/cmk-oposs_smart_error/releases).

Each release includes:
- Pre-built MKP package (recommended)
- Source code
- Release notes with changelog

## Installation

### Recommended: Install from MKP Package

The easiest way to install the plugin is using the pre-built MKP package:

1. **Download the MKP package** from the [releases page](https://github.com/oposs/cmk-oposs_smart_error/releases)
2. **Install via CheckMK GUI**:
   - Navigate to **Setup → Extension packages**
   - Click **Upload package**
   - Select the downloaded `oposs_smart_error-X.Y.Z.mkp` file
   - Click **Install**

3. **Or install via command line**:
   ```bash
   mkp add oposs_smart_error-X.Y.Z.mkp
   ```

### Alternative: Manual Installation

If you prefer to install from source, copy the plugin files to your CheckMK site:

```bash
cp -r local/* ~/local
```

The directory structure should look like:
```
~/local/lib/python3/cmk_addons/plugins/oposs_smart_error/
├── agent_based/
│   └── oposs_smart_error.py
├── checkman/
│   └── oposs_smart_error         # Plugin documentation
├── graphing/
│   ├── oposs_smart_error.py
│   └── translations.py           # Maps metric names of 1.0.5 and older
└── rulesets/
    ├── oposs_smart_error.py      # Check parameter rules
    └── ruleset_oposs_smart_error_bakery.py  # Bakery configuration rules

~/local/lib/python3/cmk/base/cee/plugins/bakery/
└── oposs_smart_error.py          # Bakery plugin logic

~/local/share/check_mk/agents/plugins/
└── oposs_smart_error             # Agent plugin script
```

### Post-Installation Steps

After installing the MKP package or manually copying files:

1. **Restart CheckMK** to load the new plugins:
   ```bash
   omd restart apache
   ```

2. **Agent Plugin Deployment**:
   - **With MKP installation**: The agent plugin is automatically available for bakery deployment
   - **For manual deployment**: Copy the agent plugin to target hosts:
     ```bash
     cp local/share/check_mk/agents/plugins/oposs_smart_error /usr/lib/check_mk_agent/plugins/
     chmod +x /usr/lib/check_mk_agent/plugins/oposs_smart_error
     ```
   - **For Agent Bakery deployment (recommended)**: The bakery will automatically deploy the plugin

## Configuration

### Using Agent Bakery (Recommended)

1. Go to **Setup > Agents > Agent rules**
2. Create a new rule for **OPOSS SMART Error Monitoring (smartctl)**
3. Configure options:
   - **Execution interval**: How often the plugin runs (0 = every agent run, suggested: 30 minutes)
   - **Command execution timeout**: Timeout for each smartctl call (default: 5 seconds)
4. Assign the rule to target hosts
5. Go to **Setup > Agents > Agent bakery** and bake agents

### Manual Deployment

If not using Agent Bakery, manually copy the agent plugin to target hosts:

```bash
scp local/share/check_mk/agents/plugins/oposs_smart_error root@target-host:/usr/lib/check_mk_agent/plugins/
ssh root@target-host chmod +x /usr/lib/check_mk_agent/plugins/oposs_smart_error
```

### Service Discovery

1. Go to **Setup > Hosts**
2. Select target hosts and run **Service discovery**
3. SMART services will be discovered for each drive with error counter logs,
   including disks behind a RAID controller that `smartctl --scan` lists with a
   device type such as `megaraid,0`. A SAS drive that reports its serial
   number but no data also gets a service, which is CRIT.
4. Accept the discovered services

### Threshold Configuration

1. Go to **Setup > Services > Service monitoring rules**
2. Create a new rule for **SMART Error Monitoring**
3. Configure thresholds for specific error counter types. Each field exists
   separately for read, write and verify, for example **Read: Uncorrected
   Errors (Absolute)**:
   - **Uncorrected Errors (Absolute)**
   - **ECC Fast Corrected Errors (Absolute)**
   - **ECC Delayed Corrected Errors (Absolute)**
   - **Rereads/Rewrites Corrected Errors (Absolute)**
   - **Correction Algorithm Invocations (Absolute)**
   - **Grown Defect List Entries (Absolute)**: one field for the drive

Without a rule, any uncorrected error is CRIT. Corrected errors, algorithm
invocations and grown defects are shown and graphed but do not change the
state.

## Service Output

Each monitored drive will show:
- Device model, capacity, and serial number
- Breakdown of specific error correction types (ECC fast, ECC delayed, rereads/rewrites)
- Uncorrected errors count
- Amount of data processed
- Current service state based on configured thresholds

The service name format is "SMART Errors <device_path> (<serial>)", with
the last 8 characters of the serial number, for example
"SMART Errors /dev/sda (2JG5LEHB)". A disk behind a RAID controller also
carries its device type: "SMART Errors /dev/bus/0 megaraid,1 (2JG5LEHB)".

Example service output:
```
WDC WUH721818AL5204 (16.4 TiB) S/N: 2JG5LEHB (sda), Read ECC delayed: 321, Read: 1.42 PiB processed, Write: 148 TiB processed
```

## Background medium scan (SAS drives)

SAS drives read their whole surface on their own while idle and log every
sector they could not read. For each drive with such a log, the plugin adds a
**SMART Background Scan <device>** service:

- Scan status and progress. "No scans active" (scanning off on the drive) is WARN, a halted scan is WARN or CRIT.
- Completed scans, the lifetime average time per scan, and the time since the
  last completed scan (WARN after 90 days, CRIT after 365 days of power-on time).
- Medium errors found by the scan: CRIT for unrecovered and WARN for recovered
  sectors logged in the last 7 days of power-on time, OK for older entries.
- With `sg3-utils` installed: whether scanning is enabled, the scan interval
  and the minimum idle time before a scan starts.

Change the levels and states with the rule **SMART Background Medium Scan**.

The **SMART Errors** service of SAS drives also shows the grown defect list
count. Set levels for it with **Grown Defect List Entries** in the
**SMART Error Monitoring** rule.

## Metrics and Graphing

The plugin provides detailed metrics for each operation type (read, write, verify):

### Absolute Metrics (per operation)
- Errors corrected by ECC fast
- Errors corrected by ECC delayed  
- Errors corrected by rereads/rewrites
- Correction algorithm invocations
- Bytes processed
- Total uncorrected errors

### Relative Metrics (per TB processed)
- Corrected errors and correction algorithm invocations, divided by the TB processed

### Graphs Available
1. **Read Operations - Error Counts**: Absolute read error metrics
2. **Write Operations - Error Counts**: Absolute write error metrics  
3. **Verify Operations - Error Counts**: Absolute verify error metrics
4. **Read Operations - Relative (per TB)**: Read error rates
5. **Write Operations - Relative (per TB)**: Write error rates
6. **Verify Operations - Relative (per TB)**: Verify error rates

## Troubleshooting

### No Services Discovered

Check that:
- `smartctl` is installed on the target host
- Drives support SCSI error counter logs
- Agent plugin is executable and in the correct location
- Plugin produces output: `/usr/lib/check_mk_agent/plugins/oposs_smart_error`

### Error Messages

- **"Failed to get SMART data"**: The rest of the message is smartctl's own
  reason, for example `device Test Unit Ready [medium or hardware error (serious)]`
  for a broken drive. Check the drive, its cabling and the smartctl permissions.
- **"No error counter data available"**: Drive doesn't support SCSI error logging (common with consumer SSDs)
- **"Agent plugin source file not found"**: Bakery can't find the agent plugin file

### Testing Agent Plugin

Test the agent plugin directly on target hosts:

```bash
# Run the plugin manually
/usr/lib/check_mk_agent/plugins/oposs_smart_error

# Check for output
check_mk_agent | grep -A 10 "<<<oposs_smart_error>>>"

# Test the plugin before deployment
python3 local/share/check_mk/agents/plugins/oposs_smart_error
```

### Checking CheckMK Logs

```bash
# Check for plugin errors
tail -f ~/var/log/web.log
tail -f ~/var/log/cmc.log
```

## Supported Devices

The plugin works with storage devices that support SCSI error counter logs:
- Most enterprise SATA/SAS hard drives
- Many enterprise SSDs
- Some consumer drives (varies by manufacturer)

Devices that typically don't work:
- Consumer SSDs without SCSI error logging
- USB-connected drives
- Some NVMe drives (depending on SMART implementation)

## Default Thresholds

If no custom thresholds are configured:
- **Corrected errors**: Warning at any corrected errors
- **Uncorrected errors**: Critical at any uncorrected errors

## License

GNU General Public License v2 - OETIKER+PARTNER AG. See [LICENSE](LICENSE).

## Author

**Tobi Oetiker** <tobi@oetiker.ch>

## Support

- **Issues**: [GitHub Issues](https://github.com/oposs/cmk-oposs_smart_error/issues)
- **Documentation**: See plugin checkman documentation after installation
- **Releases**: [GitHub Releases](https://github.com/oposs/cmk-oposs_smart_error/releases)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
