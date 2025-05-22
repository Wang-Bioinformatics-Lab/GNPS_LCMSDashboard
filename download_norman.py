import requests

def _resolve_norman_usi(usi):
    # mzspec:NORMAN-27df0a3e-3578-4a30-b9e4-1505f9da010d:webform/sample/52/uoa_pos_25_lc-esi-qtof_life_apex_16_roach_muscle_from_river_thames_shepperton-sunbury_london_uk_01.01.2016_life_apex_34794.mzml?VersionId=dHajIPC5bwhZM1gzQPvtfR8HNfqkstJL
    usi_splits = usi.split(':')

    # First looking 
    dataset_accession = usi_splits[1].replace("NORMAN-", "")
    filename = usi_splits[2]

    return "https://files.dsfp.norman-data.eu/{}".format(filename)