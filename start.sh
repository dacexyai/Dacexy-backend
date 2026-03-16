#!/bin/bash
set -e

echo "=== Working directory ==="
pwd

echo "=== Running setup ==="
python setup.py

echo "=== Verifying src/main.py exists ==="
ls -la src/
ls -la src/main.py

echo "=== Starting server ==="
python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
