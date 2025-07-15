#!/bin/bash

# create-release.sh - Create a new release with git tag
# This script helps create releases locally and push them to trigger CI/CD

set -e

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

# Function to get current version from git tags
get_current_version() {
    # Get tags that match version pattern (v1.2.3 or 1.2.3)
    local latest_tag=$(git tag -l | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -n1)
    if [ -z "$latest_tag" ]; then
        echo "0.0.0"
    else
        echo "${latest_tag#v}"  # Remove 'v' prefix if present
    fi
}

# Function to increment version
increment_version() {
    local version=$1
    local increment_type=${2:-patch}
    
    IFS='.' read -r -a version_parts <<< "$version"
    major=${version_parts[0]}
    minor=${version_parts[1]}
    patch=${version_parts[2]}
    
    case $increment_type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            print_error "Invalid increment type: $increment_type"
            exit 1
            ;;
    esac
    
    echo "${major}.${minor}.${patch}"
}

# Function to validate git repository state
validate_git_state() {
    print_step "Validating git repository state..."
    
    # Check if we're in a git repository
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi
    
    # Check if working directory is clean
    if ! git diff --quiet HEAD 2>/dev/null; then
        print_error "Working directory has uncommitted changes"
        print_info "Please commit or stash your changes before creating a release"
        exit 1
    fi
    
    # Check if we're on main branch
    local current_branch=$(git branch --show-current)
    if [ "$current_branch" != "main" ]; then
        print_warn "Not on main branch (currently on: $current_branch)"
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Aborted by user"
            exit 1
        fi
    fi
    
    print_info "✓ Git repository state is valid"
}

# Function to create release
create_release() {
    local version=$1
    local tag_name="v${version}"
    
    print_step "Creating release $version..."
    
    # Validate version format
    if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Invalid version format: $version (expected: X.Y.Z)"
        exit 1
    fi
    
    # Check if tag already exists
    if git tag -l | grep -q "^${tag_name}$"; then
        print_error "Tag $tag_name already exists"
        exit 1
    fi
    
    # Test build the package locally first
    print_step "Testing package build..."
    if [ -f "scripts/build-mkp.sh" ]; then
        chmod +x scripts/build-mkp.sh
        ./scripts/build-mkp.sh "$version"
        
        # Clean up test package
        rm -f "oposs_smart_errors-${version}.mkp"
        print_info "✓ Package build test successful"
    else
        print_warn "Build script not found, skipping build test"
    fi
    
    # Create and push tag
    print_step "Creating git tag: $tag_name"
    git tag -a "$tag_name" -m "Release version $version"
    
    print_step "Pushing tag to origin..."
    git push origin "$tag_name"
    
    print_info "✓ Release $version created successfully"
    print_info "GitHub Actions will now build and publish the release"
    print_info "Check the Actions tab in your GitHub repository for progress"
}

# Function to show current version and tags
show_version_info() {
    local current_version=$(get_current_version)
    print_info "Current version: $current_version"
    
    print_info "Recent version tags:"
    git tag -l | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | sort -V -r | head -5 | sed 's/^/  /'
    
    print_info "All tags:"
    git tag -l | sed 's/^/  /'
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] [VERSION]

Create a new release with git tag that triggers CI/CD pipeline.

OPTIONS:
    -h, --help          Show this help message
    -i, --increment     Increment version (patch, minor, or major)
    -c, --current       Show current version and recent tags
    -n, --dry-run       Show what would be done without creating the release

VERSION:
    Specific version to release (e.g., 1.2.3)
    If not specified, current version + 1 patch level

Examples:
    $0                  # Release with auto-incremented patch version
    $0 1.2.3           # Release specific version
    $0 -i minor        # Increment minor version
    $0 -i major        # Increment major version
    $0 -c              # Show current version
    $0 -n 1.2.3        # Dry run for version 1.2.3
EOF
}

# Parse command line arguments
dry_run=false
increment_type=""
version=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -c|--current)
            show_version_info
            exit 0
            ;;
        -i|--increment)
            increment_type="$2"
            shift 2
            ;;
        -n|--dry-run)
            dry_run=true
            shift
            ;;
        -*)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            version="$1"
            shift
            ;;
    esac
done

# Validate git state
validate_git_state

# Determine version to release
if [ -n "$version" ]; then
    # Use specified version
    release_version="$version"
elif [ -n "$increment_type" ]; then
    # Increment current version
    current_version=$(get_current_version)
    release_version=$(increment_version "$current_version" "$increment_type")
else
    # Default: increment patch version
    current_version=$(get_current_version)
    release_version=$(increment_version "$current_version" "patch")
fi

# Show what will be done
echo
print_info "Release plan:"
print_info "  Current version: $(get_current_version)"
print_info "  New version: $release_version"
print_info "  Git tag: v$release_version"
echo

# Dry run mode
if [ "$dry_run" = true ]; then
    print_info "Dry run mode - no changes will be made"
    print_info "Would create tag: v$release_version"
    exit 0
fi

# Confirm with user
read -p "Do you want to create this release? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Aborted by user"
    exit 1
fi

# Create the release
create_release "$release_version"