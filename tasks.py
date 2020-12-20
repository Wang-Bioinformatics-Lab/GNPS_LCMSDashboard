from celery import Celery
import download
import os
import uuid

# Setting up celery
celery_instance = Celery('lcms_tasks', backend='redis://redis', broker='redis://redis')


##############################
# Conversion
##############################
@celery_instance.task(time_limit=240)
def _download_convert_file(remote_link, local_filename, converted_local_filename, temp_folder="temp"):
    """
        This function does the serialization of downloading files
    """

    if not os.path.isfile(converted_local_filename):
        filename, file_extension = os.path.splitext(local_filename)

        temp_filename = os.path.join(temp_folder, str(uuid.uuid4()) + file_extension)
        wget_cmd = "wget '{}' -O {} 2> /dev/null".format(remote_link, temp_filename)
        os.system(wget_cmd)
        os.rename(temp_filename, local_filename)

        temp_filename = os.path.join(temp_folder, str(uuid.uuid4()) + ".mzML")
        # Lets do a conversion
        if file_extension.lower() == ".cdf":
            download._convert_cdf_to_mzML(local_filename, temp_filename)
        elif file_extension.lower() == ".raw":
            download._convert_raw_to_mzML(local_filename, temp_filename)
        else:
            download._convert_mzML(local_filename, temp_filename)

        # Renaming the temp
        os.rename(temp_filename, converted_local_filename)

#################################
# Compute Data
#################################
# @celery_instance.task(time_limit=15)
# def task_xic(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2):
#     if get_ms2 is False:
#         try:
#             return _xic_file_fast(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)
#         except:
#             pass

#     return _xic_file_slow(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)


celery_instance.conf.task_routes = {
    'tasks._download_convert_file': {'queue': 'conversion'},
    'tasks.task_xic': {'queue': 'compute'},
}