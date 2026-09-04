#!/bin/bash

# Resolution is I/O bound against upstream repositories; threads, not processes.
# 60s timeout is generous for a lookup - the old 600s existed for file conversion,
# which no longer happens here.
exec gunicorn -w 2 --threads=8 --worker-class=gthread \
    -b 0.0.0.0:5000 \
    --timeout 60 \
    --max-requests 1000 --max-requests-jitter 100 \
    --access-logfile - --error-logfile - \
    app:server
