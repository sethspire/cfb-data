#!/bin/bash
set -euo pipefail

# Install system dependencies
sudo dnf install -y git

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.cargo/env" 2>/dev/null || true

# Clone the repo
git clone https://github.com/<your-org>/cfb-data.git /home/ec2-user/cfb-data
cd /home/ec2-user/cfb-data

# Install Python dependencies
uv sync

# Run backfill
uv run python scripts/backfill.py \
  --bucket "<your-bucket>" \
  --start-year 2025 \
  --delay 0.5
