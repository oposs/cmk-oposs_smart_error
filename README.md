# CheckMK OPOSS SMART Error Monitoring Plugin

A comprehensive CheckMK plugin for monitoring SMART error counters on storage devices. This plugin collects detailed error statistics from drives and provides threshold-based alerting and graphing.

## Features

- **Comprehensive Error Monitoring**: Tracks corrected and uncorrected errors across read, write, and verify operations
- **Detailed Metrics**: Provides both absolute error counts and error rates per TB processed
- **Flexible Thresholds**: Configure warning and critical levels for different error types
- **Rich Graphing**: Six detailed graphs showing error trends and statistics
- **Agent Bakery Support**: Automatic deployment and configuration via CheckMK GUI
- **Cross-Platform**: Works on Linux systems with smartmontools

## Requirements

- CheckMK 2.3.0 or later
- `smartmontools` package installed on target hosts
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
   - Select the downloaded `oposs_smart_errors-X.Y.Z.mkp` file
   - Click **Install**

3. **Or install via command line**:
   ```bash
   mkp add oposs_smart_errors-X.Y.Z.mkp
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
│   └── oposs_smart_error.py
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
2. Create a new rule for **OPOSS SMART Error Monitoring (Linux)**
3. Configure options:
   - **Enable**: Enable/disable monitoring
   - **Timeout**: Command timeout in seconds (default: 30)
   - **Interval**: Execution interval in seconds (0 = every agent run)
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
3. SMART services will be discovered for each drive with error counter logs
4. Accept the discovered services

### Threshold Configuration

1. Go to **Setup > Services > Service monitoring rules**
2. Create a new rule for **OPOSS SMART Error Monitoring**
3. Configure thresholds for specific error counter types:
   - **Uncorrected Errors (Absolute)**: Warning/Critical for uncorrected errors (default: 1, 10)
   - **ECC Fast Corrected Errors (Absolute)**: Warning/Critical for fast ECC corrections (default: 10000, 100000)
   - **ECC Delayed Corrected Errors (Absolute)**: Warning/Critical for delayed ECC corrections (default: 1000, 10000)
   - **Rereads/Rewrites Corrected Errors (Absolute)**: Warning/Critical for reread/rewrite corrections (default: 100, 1000)
   - **Correction Algorithm Invocations (Absolute)**: Warning/Critical for algorithm invocations (default: 50000, 500000)
   - **Uncorrected Errors per TB**: Warning/Critical for uncorrected error rate per TB (default: 0.1, 1.0)

## Service Output

Each monitored drive will show:
- Device model, capacity, and serial number
- Breakdown of specific error correction types (ECC fast, ECC delayed, rereads/rewrites)
- Uncorrected errors count
- Amount of data processed
- Current service state based on configured thresholds

The service name format is "OPOSS SMART Errors <device_path>", for example "OPOSS SMART Errors /dev/sda".

Example service output:
```
WDC WD4003FZEX-00Z4SA0 (4.00 TB) S/N: WD-WMC130: Corrected: 125 ECC fast, 31 ECC delayed, 12.3 TB processed
```

## Metrics and Graphing

The plugin provides detailed metrics for each operation type (read, write, verify):

### Absolute Metrics (per operation)
- Errors corrected by ECC fast
- Errors corrected by ECC delayed  
- Errors corrected by rereads/rewrites
- Total errors corrected
- Correction algorithm invocations
- Bytes processed
- Total uncorrected errors

### Relative Metrics (per TB processed)
- All above metrics calculated per TB of data processed

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

- **"Failed to get SMART data"**: Check drive accessibility and smartctl permissions
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

This project is licensed under the GNU General Public License v2.0 - see the [LICENSE](LICENSE) file for details.

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