#!/bin/bash

#celery -A tasks_conversion worker --autoscale=8,1 -Q conversion --max-tasks-per-child 1 --loglevel INFO --max-memory-per-child 3000000
#celery -A tasks_conversion worker --autoscale=8,1 -Q conversion --max-tasks-per-child 1 --loglevel DEBUG --max-memory-per-child 3000000
celery -A tasks_conversion worker --autoscale=1,1 -Q conversion --max-tasks-per-child 1 --loglevel DEBUG --max-memory-per-child 3000000
