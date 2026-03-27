#!/bin/bash
cd /home/zius/Projects/orpaq-ai/backend
source venv/bin/activate
export PYTHONPATH=/home/zius/Projects/orpaq-ai/backend
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
