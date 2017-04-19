web: NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program gunicorn spectrum_backend.wsgi
worker: celery -A spectrum_backend worker -B
flower: flower -A spectrum_backend