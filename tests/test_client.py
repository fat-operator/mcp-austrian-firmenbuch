"""Tests for the FBW SOAP client: envelope building, parsing, fault handling."""

import base64
import urllib.error
from datetime import date

import pytest

from firmenbuch.client import (
    FirmenbuchAuthError,
    FirmenbuchClient,
    FirmenbuchError,
    auszug_v2_request,
    build_envelope,
    decode_document,
    normalize_fnr,
    suche_firma_request,
    suche_urkunde_request,
    urkunde_request,
    veraenderungen_firma_request,
    veraenderungen_urkunde_request,
)

from tests.fixtures import (
    AUSZUG_RESPONSE,
    AUSZUG_V2,
    FAULT_SOAP11,
    FAULT_SOAP12,
    SUCHE_FIRMA,
    SUCHE_FIRMA_RESPONSE,
    SUCHE_URKUNDE,
    SUCHE_URKUNDE_RESPONSE,
    URKUNDE,
    URKUNDE_RESPONSE,
    VERAENDERUNGEN_FIRMA,
    VERAENDERUNGEN_FIRMA_RESPONSE,
    VERAENDERUNGEN_URKUNDE,
)


def test_normalize_fnr():
    assert normalize_fnr("58468 h") == "58468h"
    assert normalize_fnr("419999x") == "419999x"


def test_build_envelope_structure():
    env = build_envelope(AUSZUG_V2)
    assert env.startswith('<?xml version="1.0"')
    assert 'xmlns:soap="http://www.w3.org/2003/05/soap-envelope"' in env
    assert AUSZUG_V2 in env


def test_auszug_request_matches_spec():
    req = auszug_v2_request("5h", stichtag="2015-12-22")
    assert req == AUSZUG_V2


def test_auszug_request_defaults_to_today_when_omitted():
    req = auszug_v2_request("5h", stichtag=None)
    today = date.today().isoformat()
    expected = (
        '<aus:AUSZUG_V2_REQUEST xmlns:aus="ns://firmenbuch.justiz.gv.at/Abfrage/v2/AuszugRequest">'
        "<aus:FNR>5h</aus:FNR>"
        f"<aus:STICHTAG>{today}</aus:STICHTAG>"
        "<aus:UMFANG>Kurzinformation</aus:UMFANG>"
        "</aus:AUSZUG_V2_REQUEST>"
    )
    assert req == expected


def test_auszug_request_rejects_bad_umfang():
    with pytest.raises(ValueError):
        auszug_v2_request("5h", umfang="Alles")


def test_urkunde_request_matches_spec():
    assert urkunde_request("304188_0070711322495_000___000_30_7730290_XML") == URKUNDE


def test_veraenderungen_firma_request_matches_spec():
    req = veraenderungen_firma_request("2014-11-25", "2014-11-25", "007", "AG")
    assert req == VERAENDERUNGEN_FIRMA


def test_veraenderungen_urkunde_request_matches_spec():
    assert veraenderungen_urkunde_request("2014-11-25", "2014-11-25") == VERAENDERUNGEN_URKUNDE


def test_suche_firma_request_matches_spec():
    req = suche_firma_request("mayer")
    assert req == SUCHE_FIRMA


def test_suche_urkunde_request_normalizes_fnr():
    req = suche_urkunde_request(["629 a"])
    assert req == SUCHE_URKUNDE


def test_parse_auszug_response():
    client = FirmenbuchClient(api_key="k")
    data = client.parse(AUSZUG_RESPONSE)
    firma = data["FIRMA"]  # single body child is unwrapped into its own fields
    assert data["FNR"] == "58468 h"
    # repeated BEZEICHNUNG elements collapse into a list
    bez = firma["FI_DKZ02"]["BEZEICHNUNG"]
    assert bez == ["EDV-Technik Dipl.-Ing. Went", "Gesellschaft m.b.H."]
    assert firma["FI_DKZ03"]["ZUSTELLBAR"] is True
    assert firma["FI_DKZ03"]["PLZ"] == 8054


def test_parse_suche_firma_response_lists():
    client = FirmenbuchClient(api_key="k")
    data = client.parse(SUCHE_FIRMA_RESPONSE)
    results = data["ERGEBNIS"]
    assert isinstance(results, list) and len(results) == 2
    assert results[0]["FNR"] == "145733p"
    assert results[0]["RECHTSFORM"]["CODE"] == "OG"
    # single result still parses
    single = client.parse(SUCHE_URKUNDE_RESPONSE)
    assert single["ERGEBNIS"]["KEY"].startswith("000629_")


def test_parse_urkunde_response_and_decode():
    client = FirmenbuchClient(api_key="k")
    data = client.parse(URKUNDE_RESPONSE)
    doc = data["DOKUMENT"]
    assert doc["CONTENTTYPE"] == "application/xml"
    assert decode_document(doc["CONTENT"]) == b'<?xml version="1.0"?>'
    assert base64.b64encode(decode_document(doc["CONTENT"])).decode() == doc["CONTENT"]


def test_parse_veraenderungen_response():
    client = FirmenbuchClient(api_key="k")
    data = client.parse(VERAENDERUNGEN_FIRMA_RESPONSE)
    chg = data["VERAENDERUNG"]
    assert isinstance(chg, list) and len(chg) == 2
    assert chg[0]["FNR"] == "73589 w"


@pytest.mark.parametrize("xml,needle", [(FAULT_SOAP12, "Stichtag"), (FAULT_SOAP11, "BIS-Datum")])
def test_parse_raises_on_faults(xml, needle):
    client = FirmenbuchClient(api_key="k")
    with pytest.raises(FirmenbuchError, match=needle):
        client.parse(xml)


def test_call_without_key_raises_auth_error():
    client = FirmenbuchClient(api_key="")
    with pytest.raises(FirmenbuchAuthError, match="ID Austria"):
        client.call(AUSZUG_V2, action="auszug")


def test_suche_urkunde_request_accepts_az():
    out = suche_urkunde_request(az="007 61 Fr 2164/15 w")
    assert "AZ>007 61 Fr 2164/15 w<" in out
    assert "FNR" not in out


def test_suche_urkunde_request_requires_exactly_one():
    with pytest.raises(ValueError):
        suche_urkunde_request()
    with pytest.raises(ValueError):
        suche_urkunde_request(fnrs="435836k", az="007 61 Fr 2164/15 w")


def test_veraenderungen_zeitraum_limits():
    with pytest.raises(ValueError, match="7 days"):
        veraenderungen_firma_request("2026-01-01", "2026-01-31")
    with pytest.raises(ValueError, match="7 days"):
        veraenderungen_urkunde_request("2026-01-01", "2026-01-31")
    with pytest.raises(ValueError, match="bis"):
        veraenderungen_firma_request("2026-01-10", "2026-01-01")
    # 7 days exactly is fine
    assert "VON>2026-01-01<" in veraenderungen_firma_request("2026-01-01", "2026-01-08")


def test_http_error_detail_extraction(tmp_path):
    soap_fault = (
        '<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">'
        "<env:Header/><env:Body><env:Fault><env:Code><env:Value>env:Receiver</env:Value>"
        '</env:Code><env:Reason><env:Text xml:lang="de-AT">Zugriff nicht erlaubt!'
        "</env:Text></env:Reason></env:Fault></env:Body></env:Envelope>"
    )
    client = FirmenbuchClient(api_key="k")
    import io

    err = urllib.error.HTTPError(
        "url", 500, "Internal Server Error", {},
        io.BytesIO(soap_fault.encode()),
    )
    assert "Zugriff nicht erlaubt" in client._http_error_detail(err)
