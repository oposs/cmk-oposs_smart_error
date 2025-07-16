#!/bin/bash

# create-github-release.sh - Create GitHub release with MKP file upload
# This script creates a GitHub release and uploads the corresponding MKP file

set -e

# Configuration
REPO_OWNER="oposs"
REPO_NAME="cmk-oposs_smart_error"
PACKAGE_NAME="oposs_smart_errors"

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

# Function to show usage
show_usage() {
    echo "Usage: $0 VERSION"
    echo
    echo "Create a GitHub release with MKP file upload"
    echo
    echo "Arguments:"
    echo "  VERSION     Version to release (e.g., 1.0.1)"
    echo
    echo "Examples:"
    echo "  $0 1.0.1    # Create release v1.0.1"
    echo "  $0 1.2.0    # Create release v1.2.0"
    echo
    echo "Requirements:"
    echo "  - GitHub CLI (gh) must be installed and authenticated"
    echo "  - Tag v\$VERSION must exist in repository"
    echo "  - MKP file mkp/\${PACKAGE_NAME}-\$VERSION.mkp must exist"
}

# Check arguments
if [ $# -ne 1 ]; then
    show_usage
    exit 1
fi

VERSION="$1"
TAG_NAME="v$VERSION"
MKP_FILE="mkp/${PACKAGE_NAME}-${VERSION}.mkp"

# Validate version format
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Invalid version format '$VERSION'. Expected format: X.Y.Z"
    exit 1
fi

# Check if gh CLI is available and authenticated
print_step "Checking GitHub CLI..."
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) is not installed. Please install it first:"
    print_error "  https://cli.github.com/"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    print_error "GitHub CLI is not authenticated. Please run:"
    print_error "  gh auth login"
    exit 1
fi

print_info "✓ GitHub CLI is installed and authenticated"

# Check if tag exists
print_step "Checking if tag $TAG_NAME exists..."
if ! git tag -l | grep -q "^$TAG_NAME$"; then
    print_error "Tag '$TAG_NAME' does not exist. Please create it first:"
    print_error "  git tag $TAG_NAME"
    print_error "  git push origin $TAG_NAME"
    exit 1
fi

print_info "✓ Tag $TAG_NAME exists"

# Check if MKP file exists
print_step "Checking if MKP file exists..."
if [ ! -f "$MKP_FILE" ]; then
    print_error "MKP file '$MKP_FILE' not found"
    print_error "Please ensure the MKP file exists in the mkp/ directory"
    exit 1
fi

# Get file size
FILE_SIZE=$(ls -lh "$MKP_FILE" | awk '{print $5}')
print_info "✓ MKP file found: $MKP_FILE ($FILE_SIZE)"

# Extract changelog for this version
print_step "Extracting changelog..."
CHANGELOG_FILE="CHANGES.md"
RELEASE_NOTES=""

if [ -f "$CHANGELOG_FILE" ]; then
    # Extract changelog entries for this version
    RELEASE_NOTES=$(awk "
        /^## $VERSION / { flag=1; next }
        /^## [0-9]/ && flag { exit }
        flag && /^### |^- / { print }
    " "$CHANGELOG_FILE")
    
    if [ -z "$RELEASE_NOTES" ]; then
        print_warn "No changelog entries found for version $VERSION"
        RELEASE_NOTES="No changelog entries found for this release."
    fi
else
    print_warn "No CHANGES.md file found"
    RELEASE_NOTES="No changelog file found."
fi

# Create release notes
RELEASE_BODY=$(cat <<EOF
## What's Changed

$RELEASE_NOTES

## Installation

Download the MKP file and install it:

**GUI Installation:**
1. Go to Setup → Extension packages
2. Click "Upload package"
3. Select the downloaded \`${PACKAGE_NAME}-${VERSION}.mkp\` file
4. Click "Upload & install"

**CLI Installation:**
\`\`\`bash
mkp add ${PACKAGE_NAME}-${VERSION}.mkp
\`\`\`

## Requirements
- CheckMK 2.3.0p1 or later
- smartmontools package installed on monitored hosts
- Enterprise storage devices with SCSI error counter logs

## Package Information
- **File**: \`${PACKAGE_NAME}-${VERSION}.mkp\`
- **Size**: $FILE_SIZE
- **Author**: Tobi Oetiker <tobi@oetiker.ch>
- **Repository**: https://github.com/$REPO_OWNER/$REPO_NAME
EOF
)

# Check if release already exists
print_step "Checking if release already exists..."
if gh release view "$TAG_NAME" &> /dev/null; then
    print_warn "Release $TAG_NAME already exists"
    read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deleting existing release..."
        gh release delete "$TAG_NAME" --yes
    else
        print_info "Exiting without changes"
        exit 0
    fi
fi

# Create the release
print_step "Creating GitHub release $TAG_NAME..."
gh release create "$TAG_NAME" \
    --title "Release v$VERSION" \
    --notes "$RELEASE_BODY" \
    --verify-tag

print_info "✓ Release created successfully"

# Upload MKP file
print_step "Uploading MKP file..."
gh release upload "$TAG_NAME" "$MKP_FILE"

print_info "✓ MKP file uploaded successfully"

# Show final information
print_step "Release Summary"
echo "🎉 Release $TAG_NAME created successfully!"
echo "📦 MKP file: $MKP_FILE ($FILE_SIZE)"
echo "🔗 Release URL: https://github.com/$REPO_OWNER/$REPO_NAME/releases/tag/$TAG_NAME"
echo
echo "Users can now install the plugin with:"
echo "  mkp add ${PACKAGE_NAME}-${VERSION}.mkp"