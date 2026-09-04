import csv
import os
import sys

import pytest

sys.path.insert(0, "..")

import download


def _usi_list():
    with open(os.path.join(os.path.dirname(__file__), "usi_list.tsv")) as f:
        return [row["usi"] for row in csv.DictReader(f, delimiter="\t")]


# Hits live upstream repositories, so it is the slow test in this suite.
@pytest.mark.parametrize("usi", _usi_list())
def test_resolve_remote_url(usi):
    remote_link, resource_name = download._resolve_usi_remotelink(usi)
    print("RESOLVED URL", remote_link, resource_name)
    assert len(remote_link) > 0
