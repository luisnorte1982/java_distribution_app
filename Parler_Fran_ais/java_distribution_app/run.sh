#!/usr/bin/env bash
# ──────────────────────────────────────────────
#  Java Distribution Reporting — Launch Script
# ──────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Install dependencies if needed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Load .env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Starting Java Distribution Reporting..."
echo "   Open http://localhost:8501 in your browser"
echo ""

streamlit run app.py --server.port 8501 --server.headless true
