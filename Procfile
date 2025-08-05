web: uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}
worker: celery -A tasks worker --loglevel=INFO -E -n smol_podcaster@%h