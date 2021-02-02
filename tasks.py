from celery import Celery
import download
import os
import uuid
import feature_finding
import xic
import lcms_map
import tic
from joblib import Memory

memory = Memory("temp/xic-cache", verbose=0)

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
def task_lcms_aggregate(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None", map_plot_quantization_level="Medium"):
    return lcms_map._aggregate_lcms_map(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter=polarity_filter, map_plot_quantization_level=map_plot_quantization_level)


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


celery_instance.conf.task_routes = {
    'tasks._download_convert_file': {'queue': 'conversion'},
    'tasks.task_lcms_aggregate': {'queue': 'compute'},
    'tasks.task_tic': {'queue': 'compute'},
    'tasks.task_xic': {'queue': 'compute'},
    'tasks.task_featurefinding': {'queue': 'compute'},
    'tasks.task_computeheartbeat': {'queue': 'compute'},
}