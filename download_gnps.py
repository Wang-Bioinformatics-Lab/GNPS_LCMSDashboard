
import os
import requests
import urllib
from bs4 import BeautifulSoup

def _resolve_gnps_usi(usi):
    usi_splits = usi.split(':')

    if "TASK-" in usi_splits[2]:
        # Test: mzspec:GNPS:TASK-de188599f53c43c3aaad95491743c784-spec/spec-00000.mzML:scan:31
        filename = "-".join(usi_splits[2].split("-")[2:])
        task = usi_splits[2].split("-")[1]

        remote_link = "http://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?task={}&block=main&file={}".format(task, urllib.parse.quote(filename))

        try:
            # Now we will try to see if we can resolve the file path back to a mangled name
            xml_url = "https://gnps.ucsd.edu/ProteoSAFe/DownloadResultFile?file=t.{}/params/params.xml".format(task)
            soup = BeautifulSoup(requests.get(xml_url).text)
            print(filename)
            mangled_mapping = {}
            for el_param in soup.find_all('parameter'): 
                el_name = el_param.get("name")
                if el_name == "upload_file_mapping":
                    splits = el_param.contents[0].split("|")
                    mangled_name = splits[0]
                    user_filename = splits[1]

                    mangled_mapping[user_filename] = mangled_name

            if filename[2:] in mangled_mapping:
                mangled_name = mangled_mapping[filename[2:]]
                mangled_folder = mangled_name.split("-")[0]

                task_path = os.path.join(mangled_folder, mangled_name)
                remote_link = "http://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?task={}&block=main&file={}".format(task, urllib.parse.quote(task_path))
        except:
            pass

    elif "QUICKSTART-" in usi_splits[2]:
        filename = "-".join(usi_splits[2].split("-")[2:])
        task = usi_splits[2].split("-")[1]
        remote_link = "http://gnps-quickstart.ucsd.edu/conversion/file?sessionid={}&filename={}".format(task, urllib.parse.quote(filename))
    elif "GNPS" in usi_splits[2] and "accession" in usi_splits[3]:
        print("Library Entry")
        # Lets find the provenance file
        accession = usi_splits[4]
        url = "https://gnps.ucsd.edu/ProteoSAFe/SpectrumCommentServlet?SpectrumID={}".format(accession)
        r = requests.get(url)
        spectrum_dict = r.json()
        task = spectrum_dict["spectruminfo"]["task"]
        source_file = os.path.basename(spectrum_dict["spectruminfo"]["source_file"])
        remote_link = "ftp://ccms-ftp.ucsd.edu/GNPS_Library_Provenance/{}/{}".format(task, source_file)

    return remote_link