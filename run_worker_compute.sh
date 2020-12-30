#!/bin/bash

celery -A tasks worker -l info -c 4 -Q compute --max-tasks-per-child 10 --loglevel INFO

