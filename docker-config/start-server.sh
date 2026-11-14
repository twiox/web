#!/bin/bash

 uv run manage.py migrate
 # copy static files created during build process to volume, so NGINX can reach it.
 cp -r /opt/twio_web/static /opt/.

gunicorn twio_web.wsgi:application --bind 0.0.0.0:8000
