from celery import Celery
from celery_once import QueueOnce
import download
import os
import lcms_map

# Setting up celery
celery_instance = Celery('lcms_tasks', backend='redis://gnpslcms-redis', broker='redis://gnpslcms-redis')

# Limiting the once queue for celery tasks, will give an error for idempotent tasks within an hour interval
celery_instance.conf.ONCE = {
  'backend': 'celery_once.backends.Redis',
  'settings': {
    'url': 'redis://gnpslcms-redis:6379/0',
    'default_timeout': 60 * 10,
    'blocking': True,
    'blocking_timeout': 120
  }
}

##############################
# Conversion
##############################
@celery_instance.task(time_limit=480)
def conversion_heartbeat():
    return "Up"


@celery_instance.task(time_limit=480, base=QueueOnce)
def _download_convert_file(usi, temp_folder="temp"):
    """
        This function does the serialization of downloading files
    """

    return_val = download._resolve_usi(usi, temp_folder=temp_folder)
    import sys
    print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

    _convert_file_feather.delay(usi, temp_folder=temp_folder)

    return return_val

@celery_instance.task(time_limit=480, base=QueueOnce)
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



celery_instance.conf.task_routes = {
    'tasks_conversion.conversion_heartbeat': {'queue': 'conversion'},
    'tasks_conversion._download_convert_file': {'queue': 'conversion'},
    'tasks_conversion._convert_file_feather': {'queue': 'conversion'},
}
