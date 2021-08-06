#!/bin/bash

#python ./app.py
gunicorn -w 12 --threads=12 --worker-class=gthread -b 0.0.0.0:5000 --timeout 600 --max-requests 500 --max-requests-jitter 100 --graceful-timeout 600 app:server --access-logfile /app/logs/access.log
