#!/bin/bash
set -e

echo "=== Teable CLI Installation ==="

# Check Node.js
if ! command -v node &> /dev/null; then
  echo "ERROR: Node.js is not installed. Please install Node.js >= 18 first."
  echo "  https://nodejs.org/"
  exit 1
fi

NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
  echo "ERROR: Node.js >= 18 required, found v$(node -v)"
  exit 1
fi
echo "✓ Node.js $(node -v)"

# Install CLI
if command -v teable &> /dev/null; then
  echo "✓ teable CLI already installed ($(teable --version 2>/dev/null || echo 'unknown version'))"
  echo "  Upgrading to latest..."
fi

npm install -g @teable/cli
echo "✓ teable CLI installed ($(teable --version))"

# Auth
echo ""
echo "=== Authentication ==="
if teable auth status &> /dev/null; then
  echo "✓ Already authenticated"
  teable auth status
else
  echo "Starting browser login..."
  # Honor TEABLE_ENDPOINT for non-Cloud instances; otherwise the CLI defaults to Cloud
  teable auth login ${TEABLE_ENDPOINT:+--endpoint "$TEABLE_ENDPOINT"}
  echo "✓ Authentication complete"
fi

# Verify
echo ""
echo "=== Verification ==="
teable --version
teable auth status
echo ""
echo "=== Done! Teable CLI is ready to use. ==="
