#!/bin/bash
# K2Pro Timelapse launcher — Linux / macOS
# Usage:  ./k2pro-timelapse.sh [PRINTER-IP]
# Runs in auto mode: monitors the printer and captures one timelapse per print,
# then waits for the next print automatically.

set -euo pipefail
cd "$(dirname "$0")"
source venv/bin/activate
exec python3 k2pro_timelapse.py --auto "$@"
