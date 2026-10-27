# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### New
- New service "SMART Background Scan <device>" for SAS drives. It shows
  how often the drive's own background surface scan completes, its
  progress, and the unreadable sectors it found: CRIT for unrecovered
  ones and WARN for recovered ones in the last 7 days, configurable in
  the rule "SMART Background Medium Scan".
- The "SMART Errors" service of SAS drives shows and graphs the number of
  grown defect list entries. The new "Grown Defect List Entries" field in
  the "SMART Error Monitoring" rule sets levels for it.
- With `sg3-utils` installed on the host, the background scan service also
  shows whether scanning is enabled on the drive, its interval and its
  minimum idle time.

### Changed
- Licence is now GNU General Public License v2, aligning this plugin
  with the rest of the OPOSS Checkmk plugin set. The `LICENSE` file
  previously held the MIT text.

### Fixed

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


