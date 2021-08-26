#!/bin/bash

celery -A tasks worker -l info --autoscale=16,4 -Q compute --max-tasks-per-child 10 --loglevel INFO --beat --max-memory-per-child 3000000

