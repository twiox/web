#!/bin/bash

CONTAINER_ALREADY_STARTED="/CONTAINER_ALREADY_STARTED_PLACEHOLDER"
if [ ! -e $CONTAINER_ALREADY_STARTED ]; then
    touch $CONTAINER_ALREADY_STARTED
    echo "-- First container startup --"
    # YOUR_JUST_ONCE_LOGIC_HERE
    uv run manage.py migrate
    # copy static files created during build process to volume, so NGINX can reach it.
    cp -r /opt/twio_web/static /opt/.
else
    echo "-- Not first container startup --"
fi

gunicorn twio_web.wsgi:application --bind 0.0.0.0:8000
