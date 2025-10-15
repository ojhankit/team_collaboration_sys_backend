# #!/bin/bash
# # entrypoint.sh

# # Apply migrations
python manage.py migrate

# # Collect static files (if needed)
python manage.py collectstatic --noinput

# # Start ASGI server
daphne -b 0.0.0.0 -p 8000 config.asgi:application
