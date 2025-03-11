#!/bin/bash
set -e

# ---------------------------
# Cleanup Code (Unchanged)
# ---------------------------
echo "Starting build process..."
rm -rf build/ dist/ */**/*.egg-info OpenVPCal.spec
echo "Cleanup complete."

# ---------------------------
# Remove existing uv environment directory (if applicable)
# ---------------------------
echo "Removing existing uv environment..."
rm -rf .uv .venv  # or the specific directory uv uses

# ---------------------------
# Build Environment with uv
# ---------------------------
echo "Building environment with uv..."
uv build

# ---------------------------
# Run the compile.py script using uv
# ---------------------------
echo "Running compile.py using uv..."
uv run python compile.py

echo "Build process finished successfully."

# ---------------------------
# Cleanup Code (Unchanged)
# ---------------------------
echo "Post build cleanup"
rm -rf build/ */**/*.egg-info OpenVPCal.spec
echo "Post Cleanup complete."