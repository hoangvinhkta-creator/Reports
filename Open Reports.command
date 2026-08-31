#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")"
exec python3 app/owner_launcher.py
