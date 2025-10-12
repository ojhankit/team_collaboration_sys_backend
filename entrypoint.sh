#!/bin/sh
set -e

python manage.py collectstatic --noinput || true

python manage.py migrate --noinput

exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
