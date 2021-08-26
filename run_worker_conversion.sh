#!/bin/bash

celery -A tasks worker -l info --autoscale=8,1 -Q conversion --max-tasks-per-child 1 --loglevel INFO --max-memory-per-child 3000000
