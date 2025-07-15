# Changelog

All notable changes to the CheckMK OPOSS SMART Error Monitoring Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### New
### Changed
### Fixed

## 0.9.3 - 2025-07-15
### Fixed
- Fixed version validation to support test versions (X.Y.Z-suffix format)
- Resolved GitHub Actions test workflow failures
- Fixed YAML syntax errors in test workflow configuration
- Improved build script robustness for CI/CD pipeline

## 0.9.1 - 2025-07-15
### Fixed
- Improved README with comprehensive MKP installation instructions
- Added clear download section linking to GitHub releases
- Enhanced installation documentation with GUI and CLI methods
- Added proper support and contributing sections

## 0.9.0 - 2025-07-15
### New
- Initial release of CheckMK OPOSS SMART Error Monitoring Plugin
- Operation-specific threshold configuration for read/write/verify operations
- Comprehensive SMART error counter monitoring with 16 configurable parameters
- Support for CheckMK 2.3+ with cmk.agent_based.v2 API
- Rich graphing with 7 detailed graphs showing error trends and data processing
- Agent Bakery integration for automated deployment
- CheckMK-style documentation (checkman format)
- Monitors SCSI error counter logs on enterprise storage devices
- Tracks corrected and uncorrected errors across operation types
- Provides both absolute error counts and normalized rates per TB
- Configurable thresholds based on real-world error pattern observations
- Automatic service discovery for compatible storage devices
- Detailed device information display (model, capacity, serial number)
- Enhanced release workflow with automatic version management
- Comprehensive validation and testing pipeline
- Professional changelog management following Keep a Changelog format
