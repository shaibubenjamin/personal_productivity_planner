#!/bin/sh
set -e

# Idempotent: creates tables only if missing, upserts domains/goals from config.
python -m data.seeds.seed_from_config

exec streamlit run app/streamlit/Home.py \
    --server.address=0.0.0.0 \
    --server.port=8501 \
    --server.headless=true
