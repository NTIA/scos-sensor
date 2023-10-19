#!/bin/bash

# Usage:
#   - Activate a Python environment with the its_preselector
#   package installed
#   - Run this script with start and stop times for input
#   protection specified as command line arguments.

# Example: Enable input protection from 10:00 to 12:00
# > sudo bash
# > cd /opt/scos-sensor
# > venv/bin/activate
# > pip install git+https://github.com/NTIA/Preselector
# > bash scripts/input_protection.sh 10:00 12:00

# This script sets the preselector state to "noise_diode_off"
# then powers off the preselector, at START_TIME
# Then, at STOP_TIME, the preselector is powered on and set to
# the "antenna" state.


START_TIME=$1
STOP_TIME=$2

SCRIPT_DIR=$(dirname "$0")

echo "python3 $SCRIPT_DIR/_input_protection_enable.py" | at $START_TIME

echo "python3 $SCRIPT_DIR/_input_protection_disable.py" | at $STOP_TIME