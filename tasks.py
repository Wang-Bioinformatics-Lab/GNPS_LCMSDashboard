from celery import Celery
from celery_once import QueueOnce
import download
import os
import uuid
import feature_finding
import xic
import lcms_map
import tic
import glob
import redis
from joblib import Memory

from sync import _sychronize_save_state, _sychronize_load_state

memory = Memory("temp/memory-cache", verbose=0)

# Setting up celery
celery_instance = Celery('lcms_tasks', backend='redis://redis', broker='redis://redis')

# Limiting the once queue for celery tasks, will give an error for idempotent tasks within an hour interval
celery_instance.conf.ONCE = {
  'backend': 'celery_once.backends.Redis',
  'settings': {
    'url': 'redis://redis:6379/0',
    'default_timeout': 60 * 60,
    'blocking': True,
    'blocking_timeout': 120
  }
}

redis_client = redis.Redis(host='redis', port=6379, db=0)

##############################
# Conversion
##############################
@celery_instance.task(time_limit=480, base=QueueOnce)
def _download_convert_file(usi, temp_folder="temp"):
    """
        This function does the serialization of downloading files
    """

    return_val = download._resolve_usi(usi, temp_folder=temp_folder)
    _convert_file_feather.delay(usi, temp_folder=temp_folder)

    return return_val

@celery_instance.task(time_limit=480)
def _convert_file_feather(usi, temp_folder="temp"):
    """
        This function does the serialization of conversion to feather format
    """

    if download._resolve_exists_local(usi, temp_folder=temp_folder):
        local_filename = os.path.join(temp_folder, download._usi_to_local_filename(usi))
        ms1_filename, msn_filename = lcms_map._get_feather_filenames(local_filename)

        if os.path.exists(ms1_filename):
            return

        # Let's do stuff here
        lcms_map._save_lcms_data_feather(local_filename)


    

#################################
# Compute Data
#################################
@celery_instance.task(time_limit=120)
def task_lcms_aggregate(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None", map_plot_quantization_level="Medium", cache=True):
    if cache:
        print("Caching Disabled, because with memory, it takes almost as long to cache the result as it takes to run")

    _aggregate_lcms_map = lcms_map._aggregate_lcms_map
    aggregation, msn_df = _aggregate_lcms_map(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter=polarity_filter, map_plot_quantization_level=map_plot_quantization_level)
    return aggregation, msn_df.to_dict(orient="records")

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

@celery_instance.task(time_limit=60)
def task_chromatogram_options(local_filename):
    # Caching
    chromatograms_list = memory.cache(xic.chromatograms_list)

    options = chromatograms_list(local_filename)
    return options

@celery_instance.task(time_limit=90)
def task_featurefinding(filename, params):
    feature_df = feature_finding.perform_feature_finding(filename, params, timeout=80)
    return feature_df.to_dict(orient="records")

@celery_instance.task(time_limit=1)
def task_collabsync(session_id, triggered_fields, full_params, synchronization_token=None):
    existing_params = _sychronize_load_state(session_id, redis_client)

    print("TRIGGERED FIELDS", triggered_fields)

    # Here we only update if we see a single update field, to make sure to avoid initial loads the wipe out everything
    if len(triggered_fields) <= 2:
        for field in triggered_fields:
            try:
                field_value = field.split(".")[0]
                #print(field_value)
                existing_params[field_value] = full_params[field_value]
            except:
                pass

    #import json
    #print(json.dumps(existing_params, indent=4))
    _sychronize_save_state(session_id, existing_params, redis_client, synchronization_token=synchronization_token)

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
        "schedule": 3600
    }
}


celery_instance.conf.task_routes = {
    'tasks._download_convert_file': {'queue': 'conversion'},
    'tasks._convert_file_feather': {'queue': 'conversion'},
    
    'tasks._task_cleanup': {'queue': 'compute'},

    'tasks.task_lcms_aggregate': {'queue': 'compute'},

    'tasks.task_tic': {'queue': 'compute'},
    'tasks.task_xic': {'queue': 'compute'},
    'tasks.task_featurefinding': {'queue': 'compute'},
    'tasks.task_computeheartbeat': {'queue': 'compute'},

    'tasks.task_collabsync': {'queue': 'sync'},
}