from celery import Celery
import utils
import os
import uuid

# Setting up celery
celery_instance = Celery('lcms_tasks', backend='redis://redis', broker='redis://redis')

@celery_instance.task(time_limit=120)
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
        if file_extension == ".cdf":
            utils._convert_cdf_to_mzML(local_filename, temp_filename)
        else:
            utils._convert_mzML(local_filename, temp_filename)

        # Renaming the temp
        os.rename(temp_filename, converted_local_filename)

