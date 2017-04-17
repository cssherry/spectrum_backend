web: gunicorn spectrum_backend.wsgi
worker: celery -A spectrum_backend worker -B
flower: flower -A spectrum_backend