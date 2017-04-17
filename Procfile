web: gunicorn spectrum_backend.wsgi
worker: celery worker --beat --loglevel=info --app=spectrum_backend
flower: flower -A spectrum_backend