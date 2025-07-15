#!/bin/bash

# test-release.sh - Test the enhanced release workflow locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to get current version
get_current_version() {
    local latest_tag=$(git tag -l | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -n1)
    if [ -z "$latest_tag" ]; then
        echo "0.0.0"
    else
        echo "${latest_tag#v}"
    fi
}

# Function to increment version
increment_version() {
    local version=$1
    local release_type=$2
    
    IFS='.' read -r -a version_parts <<< "$version"
    major=${version_parts[0]}
    minor=${version_parts[1]}
    patch=${version_parts[2]}
    
    case $release_type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        feature)
            minor=$((minor + 1))
            patch=0
            ;;
        bugfix)
            patch=$((patch + 1))
            ;;
        *)
            print_error "Invalid release type: $release_type"
            exit 1
            ;;
    esac
    
    echo "${major}.${minor}.${patch}"
}

# Function to update CHANGES.md
update_changelog() {
    local version=$1
    local date=$(date +%Y-%m-%d)
    
    print_step "Updating CHANGES.md for version $version"
    
    # Create backup
    cp CHANGES.md CHANGES.md.backup
    
    # Extract unreleased section
    local unreleased=$(sed -n '/## \[Unreleased\]/,/## [0-9]/p' CHANGES.md | head -n -1)
    
    # Create new changelog entry
    cat > CHANGES.md.new << EOF
# Changelog

All notable changes to the CheckMK OPOSS SMART Error Monitoring Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### New
### Changed
### Fixed

## ${version} - ${date}
EOF
    
    # Add unreleased content to new version
    echo "$unreleased" | sed '/## \[Unreleased\]/d' | sed '/^$/d' >> CHANGES.md.new
    
    # Add previous versions
    sed -n '/## [0-9]/,$p' CHANGES.md >> CHANGES.md.new
    
    # Replace original
    mv CHANGES.md.new CHANGES.md
    
    print_info "✅ CHANGES.md updated successfully"
}

# Function to test build
test_build() {
    local version=$1
    
    print_step "Testing MKP build for version $version"
    
    if [ -f "scripts/build-mkp.sh" ]; then
        chmod +x scripts/build-mkp.sh
        ./scripts/build-mkp.sh "$version"
        
        local package_file="oposs_smart_errors-${version}.mkp"
        if [ -f "$package_file" ]; then
            print_info "✅ Build test successful: $package_file"
            rm -f "$package_file"
        else
            print_error "❌ Build test failed: package not created"
            exit 1
        fi
    else
        print_error "❌ Build script not found"
        exit 1
    fi
}

# Main function
main() {
    local release_type=${1:-bugfix}
    local dry_run=${2:-false}
    
    print_info "Testing enhanced release workflow"
    print_info "Release type: $release_type"
    
    # Get current version
    local current_version=$(get_current_version)
    print_info "Current version: $current_version"
    
    # Generate new version
    local new_version=$(increment_version "$current_version" "$release_type")
    print_info "New version: $new_version"
    
    # Test build
    test_build "$new_version"
    
    if [ "$dry_run" = "true" ]; then
        print_info "✅ Dry run completed successfully"
        print_info "Would create version: $new_version"
    else
        # Update changelog
        update_changelog "$new_version"
        
        print_info "✅ Release test completed successfully"
        print_info "CHANGES.md updated for version $new_version"
        print_info "To restore original: mv CHANGES.md.backup CHANGES.md"
    fi
}

# Usage
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    cat << EOF
Usage: $0 [RELEASE_TYPE] [DRY_RUN]

Test the enhanced release workflow locally.

Arguments:
    RELEASE_TYPE    Release type (bugfix, feature, major) [default: bugfix]
    DRY_RUN        Set to 'true' for dry run [default: false]

Examples:
    $0                    # Test bugfix release
    $0 feature            # Test feature release
    $0 major true         # Dry run major release
EOF
    exit 0
fi

main "$@"