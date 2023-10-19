import os

def download_glycopost(usi, remote_link, output_filename):
    wget_cmd = "wget '{}' --referer '{}' -O {} --no-check-certificate 2> /dev/null".format(remote_link, remote_link, temp_filename)

    os.system(wget_cmd)