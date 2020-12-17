#!/bin/bash

celery -A tasks worker -l info -c 4 -Q compute
