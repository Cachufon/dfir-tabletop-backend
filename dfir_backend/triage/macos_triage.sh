#!/bin/bash
# Skeleton script for macOS triage collection.
# This script is intentionally minimal and documents the artifacts we plan to gather
# during initial triage. Implement collection logic in future iterations.

set -euo pipefail

# TODO: set TARGET_DIR to the destination for collected artifacts
TARGET_DIR="/tmp/macos_triage"
mkdir -p "$TARGET_DIR"

# Unified logs (requires log CLI)
# TODO: collect recent unified logs for relevant subsystems and save to TARGET_DIR
# Example placeholder:
# log show --info --debug --predicate 'subsystem BEGINSWITH "com.apple"' --last 1d > "$TARGET_DIR/unified_logs.log"

# TCC database entries
# TODO: copy or query TCC.db to capture application permission decisions
# Example placeholder:
# cp /Library/Application\ Support/com.apple.TCC/TCC.db "$TARGET_DIR/TCC.db" 2>/dev/null || true

# Persistence mechanisms (launch agents/daemons, profiles, login items)
# TODO: enumerate ~/Library/LaunchAgents, /Library/LaunchAgents, /Library/LaunchDaemons
# TODO: gather configuration profiles and login items for persistence review

# Running processes
# TODO: capture process list with command line details
# Example placeholder:
# ps auxww > "$TARGET_DIR/process_list.txt"

# Network connections
# TODO: capture active network connections and listeners
# Example placeholder:
# lsof -i -n -P > "$TARGET_DIR/network_connections.txt"

# Browser artifacts
# TODO: collect key browser data (history, downloads, extensions) for major browsers
# NOTE: ensure collection respects privacy and legal constraints

# Bundle summary for analysts
# TODO: generate a manifest of collected files for quick review
# ls -lR "$TARGET_DIR" > "$TARGET_DIR/manifest.txt"

echo "macOS triage collection placeholder complete. Artifacts staged in $TARGET_DIR (if collected)."
