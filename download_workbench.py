import requests
from download_msv import _resolve_msv_usi

def _resolve_metabolomicsworkbench_usi(usi):
    usi_splits = usi.split(':')

    # First looking 
    dataset_accession = usi_splits[1]
    filename = usi_splits[2]

    try:
        # Checking if Data is in Metabolomics Workbench
        dataset_list_url = "https://www.metabolomicsworkbench.org/data/show_archive_contents_json.php?STUDY_ID={}".format(dataset_accession)
        mw_file_list = requests.get(dataset_list_url).json()
        for file_obj in mw_file_list:
            if filename in file_obj["FILENAME"]:
                return file_obj["URL"]
    except:
        pass

    # Checking if Data is in MSV
    url = "https://massive.ucsd.edu/ProteoSAFe/QueryDatasets?task=N%2FA&file=&pageSize=30&offset=0&query=%257B%2522full_search_input%2522%253A%2522%2522%252C%2522table_sort_history%2522%253A%2522createdMillis_dsc%2522%252C%2522query%2522%253A%257B%257D%252C%2522title_input%2522%253A%2522{}%2522%257D&target=&_=1606254845533".format(dataset_accession)
    r = requests.get(url)
    data_json = r.json()
    
    msv_accession = data_json["row_data"][0]["dataset"]
    msv_usi = "mzspec:{}:{}:scan:1".format(msv_accession, filename)

    return _resolve_msv_usi(msv_usi)