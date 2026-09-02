from unittest.mock import patch

import pytest
import requests

import sys
sys.path.insert(0, "..")

import download_msv


USI = "mzspec:MSV000085852:ccms_peak/QC_raw/QC_0.mzML"
SHORT_USI = "mzspec:MSV000085852:QC_0"
FALLBACK_URL = (
    "https://massiveproxy.gnps2.org/massiveproxy/"
    "MSV000085852/ccms_peak/QC_raw/QC_0.mzML"
)


@pytest.mark.parametrize(
    "lookup_error",
    [requests.ConnectionError("unavailable"), requests.Timeout("timed out")],
)
def test_force_massive_falls_back_on_lookup_transport_errors(lookup_error):
    with patch("download_msv.requests.get", side_effect=lookup_error) as lookup:
        result = download_msv._resolve_msv_usi(USI, force_massive=True)

    assert result == FALLBACK_URL
    lookup.assert_called_once_with(
        "https://massive.ucsd.edu/ProteoSAFe/QuerySpectrum",
        params={"id": f"{USI}:scan:1"},
        verify=False,
        timeout=(3.05, 10),
    )


def test_lookup_transport_error_is_preserved_without_fallback():
    error = requests.ConnectionError("unavailable")

    with patch("download_msv.requests.get", side_effect=error):
        with pytest.raises(requests.ConnectionError) as raised:
            download_msv._resolve_msv_usi(USI)

    assert raised.value is error


def test_short_usi_does_not_return_guessed_fallback_url():
    error = requests.ConnectionError("unavailable")

    with patch("download_msv.requests.get", side_effect=error):
        with pytest.raises(requests.ConnectionError) as raised:
            download_msv._resolve_msv_usi(SHORT_USI, force_massive=True)

    assert raised.value is error
