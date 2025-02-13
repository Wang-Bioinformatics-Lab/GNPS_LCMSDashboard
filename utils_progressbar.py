import os
import requests
from download import _usi_to_local_filename

def _determine_usi_size(usi):
    try:
        url = "https://datasetcache.gnps2.org/datasette/datasette/database/filename.json?_sort=usi&usi__exact={}&_shape=array".format(usi.rstrip())
        r = requests.get(url)
        r.raise_for_status()

        usi_information = r.json()

        usi_size = usi_information[0]["size"]
    except:
        usi_size = 0

    return usi_size

def determine_usi_progress(usis):
    all_usi = usis.split("\n")

    status_dict = {}

    for usi in all_usi:
        if len(usi) < 5:
            continue
        
        status_dict[usi] = {}

        local_usi_filename = _usi_to_local_filename(usi)
        local_usi_filename = os.path.join("temp", local_usi_filename)        

        full_percent_complete = 0
        
        if os.path.exists(local_usi_filename):
            status_dict[usi]["downloadstatus"] = "done"
            full_percent_complete += 80
        else:
            status_dict[usi]["downloadstatus"] = "pending"
            
            # we should find the temp file
            import download
            remote_link, resource_name = download._resolve_usi_remotelink(usi)
            _, file_extension = os.path.splitext(remote_link)
            temp_download_filename = os.path.join("temp", download._usi_to_temp_download_filename(usi, file_extension))

            print(temp_download_filename)


            if os.path.exists(temp_download_filename):
                usi_size = _determine_usi_size(usi)

                status_dict[usi]["downloadstatus"] = "downloading"

                if usi_size > 0:
                    downloaded_size = os.path.getsize(temp_download_filename)
                    status_dict[usi]["downloadpercent"] = int((downloaded_size / usi_size) * 100)
                    full_percent_complete += int(status_dict[usi]["downloadpercent"] * 0.8)
                else:
                    # we couldnt figure out the full file size
                    status_dict[usi]["downloadpercent"] = 50
                    full_percent_complete += 40
            else:
                status_dict[usi]["downloadstatus"] = "pending"
                status_dict[usi]["downloadpercent"] = 0

        
        # checking the feather file
        local_feather_filename = local_usi_filename + ".ms1.feather"
        if os.path.exists(local_feather_filename):
            status_dict[usi]["readstatus"] = "done"
            full_percent_complete += 20
        else:
            status_dict[usi]["readstatus"] = "pending"

        status_dict[usi]["completionpercent"] = full_percent_complete

    return status_dict

def generate_html_progress(data):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>USI Completion Progress</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; }
            table { width: 80%; margin: 20px auto; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: center; }
            th { background-color: #f4f4f4; }
            .progress-container { position: relative; width: 100%; background: #ddd; height: 25px; border-radius: 5px; }
            .progress-bar { height: 100%; border-radius: 5px; background: green; text-align: center; color: white; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>USI Completion Progress</h2>
        <table>
            <tr>
                <th>USI</th>
                <th>Completion Progress</th>
            </tr>
    """

    for key, statuses in data.items():
        # Use only `completionpercent`
        percent = statuses.get("completionpercent", 100)  # Default to 100% if missing

        # Add table row
        html_content += f"""
        <tr>
            <td>{key}</td>
            <td>
                <div class="progress-container">
                    <div class="progress-bar" style="width:{percent}%;">{percent}%</div>
                </div>
            </td>
        </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """
    return html_content