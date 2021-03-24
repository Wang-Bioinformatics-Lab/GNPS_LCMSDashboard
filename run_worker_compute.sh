#!/bin/bash

celery -A tasks worker -l info -c 16 -Q compute --max-tasks-per-child 10 --loglevel INFO --beat --max-memory-per-child 3000000

