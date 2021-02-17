from celery import Celery
import download
import os
import uuid
import feature_finding
import xic
import lcms_map
import tic
import glob
from joblib import Memory

memory = Memory("temp/memory-cache", verbose=0)

# Setting up celery
celery_instance = Celery('lcms_tasks', backend='redis://redis', broker='redis://redis')

##############################
# Conversion
##############################
@celery_instance.task(time_limit=240)
def _download_convert_file(usi, temp_folder="temp"):
    """
        This function does the serialization of downloading files
    """

    return download._resolve_usi(usi, temp_folder=temp_folder)

#################################
# Compute Data
#################################
@celery_instance.task(time_limit=120)
def task_lcms_aggregate(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None", map_plot_quantization_level="Medium", cache=True):
    if cache:
        _aggregate_lcms_map = memory.cache(lcms_map._aggregate_lcms_map)
    else:
        _aggregate_lcms_map = lcms_map._aggregate_lcms_map

    return _aggregate_lcms_map(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter=polarity_filter, map_plot_quantization_level=map_plot_quantization_level)


@celery_instance.task(time_limit=90)
def task_tic(input_filename, tic_option="TIC", polarity_filter="None"):
    tic_df = tic.tic_file(input_filename, tic_option=tic_option, polarity_filter=polarity_filter)
    return tic_df.to_dict(orient="records")

@celery_instance.task(time_limit=60)
def task_xic(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2=False):
    # Caching
    xic_file = memory.cache(xic.xic_file)

    xic_df, ms2_data = xic_file(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2=get_ms2)
    return xic_df.to_dict(orient="records"), ms2_data

@celery_instance.task(time_limit=90)
def task_featurefinding(filename, params):
    feature_df = feature_finding.perform_feature_finding(filename, params, timeout=80)
    return feature_df.to_dict(orient="records")


@celery_instance.task(time_limit=60)
def task_computeheartbeat():
    return "Up"

import datetime
import sys
@celery_instance.task(time_limit=480)
def _task_cleanup():
    all_temp_files = glob.glob("/app/temp/*")

    MAX_TIME_SECONDS = 604800 # This is one week
    #MAX_TIME_SECONDS = 60 # This is one minute

    for filename in all_temp_files:
        # Skipping local file uploads
        if "mzspecLOCAL" in filename:
            continue
        
        if os.path.isfile(filename):
            file_stats = os.stat(filename)
            access_time = file_stats.st_atime
            access_datetime = datetime.datetime.fromtimestamp(access_time)
            time_delta = datetime.datetime.now() - access_datetime

            if time_delta.total_seconds() > MAX_TIME_SECONDS:
                # Lets remove
                print("REMOVING", filename)
                os.remove(filename)

    return "Cleanup"


celery_instance.conf.beat_schedule = {
    "cleanup": {
        "task": "tasks._task_cleanup",
        "schedule": 60
    }
}


celery_instance.conf.task_routes = {
    'tasks._download_convert_file': {'queue': 'conversion'},
    
    'tasks._task_cleanup': {'queue': 'compute'},

    'tasks.task_lcms_aggregate': {'queue': 'compute'},
    'tasks.task_tic': {'queue': 'compute'},
    'tasks.task_xic': {'queue': 'compute'},
    'tasks.task_featurefinding': {'queue': 'compute'},
    'tasks.task_computeheartbeat': {'queue': 'compute'},
}