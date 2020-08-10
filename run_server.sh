#!/bin/bash


#curlftpfs ftp://massive.ucsd.edu/ /data/massive/

#python ./app.py
gunicorn -w 4 --threads=6 --worker-class=gthread -b 0.0.0.0:5000 --timeout 120 app:server --access-logfile /app/logs/access.log
