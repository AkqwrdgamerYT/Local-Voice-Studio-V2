#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "$(readlink -f -- "$0")")"

PYTHON="${PYTHON:-python3.12}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
	echo "Python 3.12 was not found. Install it, then run this script again."
	exit 1
fi

if ! "$PYTHON" -c 'import tkinter' >/dev/null 2>&1; then
	echo "Tkinter is missing. On Ubuntu, install it with:"
	echo "  sudo apt install python3-tk"
	exit 1
fi

if [ ! -x .venv/bin/python ]; then
	"$PYTHON" -m venv .venv
fi

if ! .venv/bin/python -c 'import numpy, sounddevice' >/dev/null 2>&1; then
	echo "Installing Local Voice Studio's Python dependencies..."
	.venv/bin/python -m pip install -r requirements.txt
fi

exec .venv/bin/python voice_changer_linux.py
