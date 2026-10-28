# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### New
- New service "SMART Background Scan <device>" for SAS drives. It shows
  how often the drive's own background surface scan completes, its
  progress, and the unreadable sectors it found. By default it is CRIT
  for unrecovered sectors and WARN for recovered ones found in the last
  7 days, WARN when no scan is active, WARN or CRIT for a halted scan,
  and WARN after 90 days and CRIT after 365 days of power-on time
  without a completed scan; the rule "SMART Background Medium Scan"
  changes these. Of a long scan log the service lists the newest 50
  entries and counts the others as older errors.
- The "SMART Errors" service of SAS drives shows and graphs the number of
  grown defect list entries. The new "Grown Defect List Entries" field in
  the "SMART Error Monitoring" rule sets levels for it.
- With `sg3-utils` installed on the host, the background scan service also
  shows whether scanning is enabled on the drive, its interval and its
  minimum idle time.

### Changed
- The metrics of the "SMART Errors" service now start with
  `oposs_smart_error_`, for example `read_bytes_processed` is now
  `oposs_smart_error_read_bytes_processed`, so the package keeps loading
  on Checkmk 3.0. The service graphs still show the history recorded under
  the old names. Custom graphs, dashboards and metric exports (for example
  InfluxDB) that use the old names must be changed to the new ones.
- The "SMART Errors" service no longer records the metrics
  `read_uncorrected_check`, `read_eccfast_check` and the like, which
  repeated the error counters already graphed. Their stand-alone graphs
  stop getting new data.
- Licence is now GNU General Public License v2, aligning this plugin
  with the rest of the OPOSS Checkmk plugin set. The `LICENSE` file
  previously held the MIT text.

### Fixed
- The README named rules, fields and services that do not exist, such as
  "OPOSS SMART Error Monitoring (Linux)", an "Enable" option, "Uncorrected
  Errors per TB" and the service name "OPOSS SMART Errors /dev/sda", and
  gave threshold defaults the rule does not use. README and the check
  manual page now describe the actual rule fields, the default states and
  the item format "/dev/sda (2JG5LEHB)".
- Disks behind a RAID controller that smartctl reaches only with a device
  type, for example `-d megaraid,0`, got no service. The agent now uses
  the type that `smartctl --scan` reports, and such disks are discovered
  as "SMART Errors /dev/bus/0 megaraid,0 (<serial>)". A disk that also
  appears as a plain device such as /dev/sdb (JBOD) keeps only that
  service, and services of other disks keep their names.
- The "SMART Errors" service of SAS drives showed no drive model, only
  capacity and serial number, for example "(16.4 TiB) S/N: 2JG5LEHB
  (sdc)". It now starts with the model, and the agent also reports the
  firmware revision of SAS drives.
- The "SMART Errors" service went CRIT with "Error: Failed to get SMART
  data" for some drives that smartctl had read without trouble, for
  example when one of its log page reads failed. It now shows the
  counters, and when there really is no data the message says why, for
  example "device open failed (smartctl exit status 2)".
- The "Command execution timeout" set in the agent bakery rule "OPOSS
  SMART Error Monitoring (smartctl)" had no effect: the bakery wrote the
  setting to a file the agent plugin never read, so smartctl always ran with a
  5 second timeout. The setting is now used, values below 1 second are
  refused, and the default stays 5 seconds with or without the rule.

## 1.0.5 - 2025-08-12
### Fixed
- Fixed check_levels parameter handling to work correctly with CheckMK 2.3 SimpleLevels format

## 1.0.4 - 2025-08-08
### Changed
- switch to check_levels

## 1.0.3 - 2025-08-07
### Fixed
- fixed naming regression

## 1.0.2 - 2025-08-07
### Fixed
- improved documentation

## 1.0.1 - 2025-08-07
### New
- initial release


