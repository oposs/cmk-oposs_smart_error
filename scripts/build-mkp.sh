#!/bin/bash

# build-mkp.sh - Build CheckMK MKP package
# This script can be used locally or in CI/CD pipelines

set -e

# Configuration
PACKAGE_NAME="oposs_smart_errors"
PACKAGE_TITLE="SMART Error Monitoring Plugin"
PACKAGE_DESCRIPTION="A comprehensive CheckMK plugin for monitoring SMART error counters on storage devices. This plugin collects detailed error statistics from drives and provides threshold-based alerting and graphing."
AUTHOR="Tobi Oetiker tobi@oetiker.ch"
DOWNLOAD_URL="https://github.com/oposs/cmk-oposs_smart_error"
CMK_VERSION="2.3.0p34"
MIN_CMK_VERSION="2.3.0p1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
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

# Function to validate source files
validate_source_files() {
    print_step "Validating source files..."
    local errors=0
    
    # Check agent plugin
    if [ ! -f "local/share/check_mk/agents/plugins/oposs_smart_error" ]; then
        print_error "Agent plugin not found: local/share/check_mk/agents/plugins/oposs_smart_error"
        errors=$((errors + 1))
    else
        print_info "✓ Agent plugin found"
    fi
    
    # Check check plugins
    local check_files=(
        "local/lib/python3/cmk_addons/plugins/oposs_smart_error/agent_based/oposs_smart_error.py"
        "local/lib/python3/cmk_addons/plugins/oposs_smart_error/checkman/oposs_smart_error"
        "local/lib/python3/cmk_addons/plugins/oposs_smart_error/graphing/oposs_smart_error.py"
        "local/lib/python3/cmk_addons/plugins/oposs_smart_error/rulesets/oposs_smart_error.py"
        "local/lib/python3/cmk_addons/plugins/oposs_smart_error/rulesets/ruleset_oposs_smart_error_bakery.py"
    )
    
    for file in "${check_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Check plugin file not found: $file"
            errors=$((errors + 1))
        fi
    done
    
    if [ $errors -eq 0 ]; then
        print_info "✓ All check plugin files found"
    fi
    
    # Check bakery plugin
    if [ ! -f "local/lib/python3/cmk/base/cee/plugins/bakery/oposs_smart_error.py" ]; then
        print_error "Bakery plugin not found: local/lib/python3/cmk/base/cee/plugins/bakery/oposs_smart_error.py"
        errors=$((errors + 1))
    else
        print_info "✓ Bakery plugin found"
    fi
    
    return $errors
}

# Function to validate Python syntax
validate_python_syntax() {
    print_step "Validating Python syntax..."
    local errors=0
    
    local python_files=(
        "local/lib/python3/cmk_addons/plugins/oposs_smart_error/agent_based/oposs_smart_error.py"
        "local/lib/python3/cmk_addons/plugins/oposs_smart_error/graphing/oposs_smart_error.py"
        "local/lib/python3/cmk_addons/plugins/oposs_smart_error/rulesets/oposs_smart_error.py"
        "local/lib/python3/cmk_addons/plugins/oposs_smart_error/rulesets/ruleset_oposs_smart_error_bakery.py"
        "local/lib/python3/cmk/base/cee/plugins/bakery/oposs_smart_error.py"
        "local/share/check_mk/agents/plugins/oposs_smart_error"
    )
    
    for file in "${python_files[@]}"; do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            print_error "Python syntax error in: $file"
            errors=$((errors + 1))
        else
            print_info "✓ $(basename "$file")"
        fi
    done
    
    return $errors
}

# Function to create info.json
create_info_json() {
    local version=$1
    local build_dir=$2
    
    cat > "$build_dir/info.json" << EOF
{
    "title": "$PACKAGE_TITLE",
    "name": "$PACKAGE_NAME",
    "description": "$PACKAGE_DESCRIPTION",
    "version": "$version",
    "version.packaged": "$CMK_VERSION",
    "version.min_required": "$MIN_CMK_VERSION",
    "version.usable_until": null,
    "author": "$AUTHOR",
    "download_url": "$DOWNLOAD_URL",
    "files": {
        "cmk_addons_plugins": [
            "oposs_smart_error/agent_based/oposs_smart_error.py",
            "oposs_smart_error/checkman/oposs_smart_error",
            "oposs_smart_error/graphing/oposs_smart_error.py",
            "oposs_smart_error/rulesets/oposs_smart_error.py",
            "oposs_smart_error/rulesets/ruleset_oposs_smart_error_bakery.py"
        ],
        "agents": [
            "plugins/oposs_smart_error"
        ],
        "lib": [
            "cmk/base/cee/plugins/bakery/oposs_smart_error.py"
        ]
    }
}
EOF
}

# Function to create info file (Python format)
create_info_file() {
    local version=$1
    local build_dir=$2
    
    cat > "$build_dir/info" << EOF
{'author': '$AUTHOR',
 'description': '$PACKAGE_DESCRIPTION',
 'download_url': '$DOWNLOAD_URL',
 'files': {'agents': ['plugins/oposs_smart_error'],
           'cmk_addons_plugins': ['oposs_smart_error/agent_based/oposs_smart_error.py',
                                  'oposs_smart_error/checkman/oposs_smart_error',
                                  'oposs_smart_error/graphing/oposs_smart_error.py',
                                  'oposs_smart_error/rulesets/oposs_smart_error.py',
                                  'oposs_smart_error/rulesets/ruleset_oposs_smart_error_bakery.py'],
           'lib': ['cmk/base/cee/plugins/bakery/oposs_smart_error.py']},
 'name': '$PACKAGE_NAME',
 'title': '$PACKAGE_TITLE',
 'version': '$version',
 'version.min_required': '$MIN_CMK_VERSION',
 'version.packaged': '$CMK_VERSION',
 'version.usable_until': None}
EOF
}

# Main build function
build_mkp() {
    local version=$1
    local build_dir="/tmp/mkp_build_$$"
    local output_file="${PACKAGE_NAME}-${version}.mkp"
    
    print_info "Building MKP package version $version"
    
    # Create build directory
    mkdir -p "$build_dir"
    
    # Validate source files
    if ! validate_source_files; then
        print_error "Source file validation failed"
        rm -rf "$build_dir"
        exit 1
    fi
    
    # Validate Python syntax
    if ! validate_python_syntax; then
        print_error "Python syntax validation failed"
        rm -rf "$build_dir"
        exit 1
    fi
    
    # Create tar files
    print_step "Creating component tar files..."
    
    # Create agents.tar
    if ! tar -cf "$build_dir/agents.tar" -C "local/share/check_mk/agents" plugins/oposs_smart_error; then
        print_error "Failed to create agents.tar"
        rm -rf "$build_dir"
        exit 1
    fi
    print_info "✓ agents.tar created"
    
    # Create cmk_addons_plugins.tar
    if ! tar -cf "$build_dir/cmk_addons_plugins.tar" -C "local/lib/python3/cmk_addons/plugins" oposs_smart_error/; then
        print_error "Failed to create cmk_addons_plugins.tar"
        rm -rf "$build_dir"
        exit 1
    fi
    print_info "✓ cmk_addons_plugins.tar created"
    
    # Create lib.tar
    if ! tar -cf "$build_dir/lib.tar" -C "local/lib/python3" cmk/base/cee/plugins/bakery/oposs_smart_error.py; then
        print_error "Failed to create lib.tar"
        rm -rf "$build_dir"
        exit 1
    fi
    print_info "✓ lib.tar created"
    
    # Create metadata files
    print_step "Creating metadata files..."
    create_info_json "$version" "$build_dir"
    create_info_file "$version" "$build_dir"
    print_info "✓ Metadata files created"
    
    # Create final MKP package
    print_step "Creating MKP package: $output_file"
    if ! tar -czf "$output_file" -C "$build_dir" agents.tar cmk_addons_plugins.tar lib.tar info info.json; then
        print_error "Failed to create MKP package"
        rm -rf "$build_dir"
        exit 1
    fi
    
    # Cleanup
    rm -rf "$build_dir"
    
    # Show package info
    local size=$(ls -lh "$output_file" | awk '{print $5}')
    print_info "Package created successfully: $output_file ($size)"
    
    # List contents
    print_info "Package contents:"
    tar -tf "$output_file" | sed 's/^/  /'
    
    # Show installation instructions
    echo
    print_info "Installation instructions:"
    echo "  1. Upload via CheckMK GUI: Setup → Extension packages → Upload package"
    echo "  2. Or install via CLI: mkp install $output_file"
    echo
}

# Usage function
usage() {
    cat << EOF
Usage: $0 VERSION

Build CheckMK MKP package from source files.

Arguments:
    VERSION     Version to build (e.g., 1.2.3)

Examples:
    $0 1.2.3    # Build version 1.2.3
    $0 2.0.0    # Build version 2.0.0

Environment Variables:
    BUILD_DIR   Custom build directory (default: /tmp/mkp_build_PID)
EOF
}

# Main script
if [ $# -ne 1 ]; then
    usage
    exit 1
fi

version="$1"

# Validate version format
if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Invalid version format: $version (expected: X.Y.Z)"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "local/share/check_mk/agents/plugins/oposs_smart_error" ]; then
    print_error "Not in the project root directory. Please run from the project root."
    exit 1
fi

# Build the package
build_mkp "$version"