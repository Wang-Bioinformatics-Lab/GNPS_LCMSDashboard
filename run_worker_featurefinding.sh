#!/bin/bash

celery -A tasks worker -l info --autoscale=8,1 -Q featurefinding --max-tasks-per-child 10 --loglevel INFO --beat --max-memory-per-child 3000000

