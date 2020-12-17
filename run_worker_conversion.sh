#!/bin/bash

celery -A tasks worker -l info -c 1 -Q conversion
