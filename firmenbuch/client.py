"""FBW-WebServices (HVD) SOAP client for the Austrian Firmenbuch.

Implements the six operations of the official BMJ interface specification
"FBW-WebServices (HVD) Schnittstellenbeschreibung" v1.3 (22.05.2025):
Auszug V2, Urkunden, Veraenderungen (Firma/Urkunde), Suche (Firma/Urkunde).

Pure stdlib HTTP + xml.etree parsing; no external SOAP library.
"""

from __future__ import annotations

import base64
import os
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from typing import Any

ENDPOINT = "https://justizonline.gv.at/jop/api/at.gv.justiz.fbw/ws"
WSDL_URL = ENDPOINT + "/fbw.wsdl"
NS = "ns://firmenbuch.justiz.gv.at/Abfrage"
SOAP_ENV = "http://www.w3.org/2003/05/soap-envelope"

UMFANG_VALUES = ("Kurzinformation", "Vollinformation")


class FirmenbuchError(RuntimeError):
    """A SOAP fault or transport error from the FBW service."""


class FirmenbuchAuthError(FirmenbuchError):
    """Missing/invalid API token (HTTP 401/403)."""


class FirmenbuchRateLimitError(FirmenbuchError):
    """Server-side load limit hit (HTTP 429)."""


def normalize_fnr(fnr: str) -> str:
    """Normalize a Firmenbuchnummer: strip spaces, keep digits + check letter."""
    return re.sub(r"\s+", "", str(fnr or "")).strip()


def build_envelope(body_xml: str) -> str:
    """Wrap a request body in a SOAP 1.2 envelope."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<soap:Envelope xmlns:soap="{SOAP_ENV}">'
        "<soap:Header/>"
        f"<soap:Body>{body_xml}</soap:Body>"
        "</soap:Envelope>"
    )


def _esc(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ---------------------------------------------------------------- payloads --

def auszug_v2_request(
    fnr: str,
    stichtag: str | None = None,
    umfang: str = "Kurzinformation",
) -> str:
    if umfang not in UMFANG_VALUES:
        raise ValueError(f"umfang must be one of {UMFANG_VALUES}")
    if not stichtag:
        stichtag = date.today().isoformat()
    parts = [f"<aus:FNR>{_esc(normalize_fnr(fnr))}</aus:FNR>"]
    parts.append(f"<aus:STICHTAG>{_esc(stichtag)}</aus:STICHTAG>")
    parts.append(f"<aus:UMFANG>{_esc(umfang)}</aus:UMFANG>")
    return (
        f'<aus:AUSZUG_V2_REQUEST xmlns:aus="{NS}/v2/AuszugRequest">'
        + "".join(parts)
        + "</aus:AUSZUG_V2_REQUEST>"
    )


def urkunde_request(key: str) -> str:
    return (
        f'<urk:URKUNDEREQUEST xmlns:urk="{NS}/UrkundeRequest">'
        f"<urk:KEY>{_esc(key)}</urk:KEY>"
        "</urk:URKUNDEREQUEST>"
    )


def _validate_zeitraum(von: str, bis: str) -> None:
    """The FBW service rejects veraenderungen ranges longer than 7 days
    (SOAP fault 'Der Zeitraum darf 7 Tage nicht überschreiten')."""
    try:
        d_von, d_bis = date.fromisoformat(von), date.fromisoformat(bis)
    except ValueError as exc:
        raise ValueError("von/bis must be YYYY-MM-DD") from exc
    if d_bis < d_von:
        raise ValueError("bis must not be before von")
    if (d_bis - d_von).days > 7:
        raise ValueError(
            "the FBW API allows a maximum range of 7 days for "
            "veraenderungen queries; split the period into <=7-day chunks"
        )


def veraenderungen_firma_request(
    von: str,
    bis: str,
    gericht: str | None = None,
    rechtsform: str | None = None,
) -> str:
    _validate_zeitraum(von, bis)
    parts = [
        f"<ver:VON>{_esc(von)}</ver:VON>",
        f"<ver:BIS>{_esc(bis)}</ver:BIS>",
    ]
    if gericht:
        parts.append(f"<ver:GERICHT>{_esc(gericht)}</ver:GERICHT>")
    if rechtsform:
        parts.append(f"<ver:RECHTSFORM>{_esc(rechtsform)}</ver:RECHTSFORM>")
    return (
        f'<ver:VERAENDERUNGENFIRMAREQUEST xmlns:ver="{NS}/VeraenderungenFirmaRequest">'
        + "".join(parts)
        + "</ver:VERAENDERUNGENFIRMAREQUEST>"
    )


def veraenderungen_urkunde_request(von: str, bis: str) -> str:
    _validate_zeitraum(von, bis)
    return (
        f'<ver:VERAENDERUNGENURKUNDEREQUEST xmlns:ver="{NS}/VeraenderungenUrkundeRequest">'
        f"<ver:VON>{_esc(von)}</ver:VON>"
        f"<ver:BIS>{_esc(bis)}</ver:BIS>"
        "</ver:VERAENDERUNGENURKUNDEREQUEST>"
    )


def wertetabellen_request(tabelle: str = "ALL", stichtag: str | None = None) -> str:
    """WERTETABELLEN_V2_REQUEST: fetch FB code/value tables (undocumented in
    spec v1.3 but part of the live WSDL)."""
    parts = [f"<wta:TABELLE>{_esc(tabelle)}</wta:TABELLE>"]
    if stichtag:
        parts.append(f"<wta:STICHTAG>{_esc(stichtag)}</wta:STICHTAG>")
    return (
        f'<wta:WERTETABELLEN_V2_REQUEST xmlns:wta="{NS}/v2/FBWertetabellenRequest">'
        + "".join(parts)
        + "</wta:WERTETABELLEN_V2_REQUEST>"
    )


def suche_firma_request(
    firmenwortlaut: str,
    exakte_suche: bool = False,
    suchbereich: str = "1",
    gericht: str | None = None,
    rechtsform: str | None = None,
    rechtseigenschaft: str | None = None,
    ortnr: str | None = None,
) -> str:
    def opt(tag: str, value: str | None) -> str:
        return f"<suc:{tag}>{_esc(value)}</suc:{tag}>" if value else f"<suc:{tag}/>"

    return (
        f'<suc:SUCHEFIRMAREQUEST xmlns:suc="{NS}/SucheFirmaRequest">'
        f"<suc:FIRMENWORTLAUT>{_esc(firmenwortlaut)}</suc:FIRMENWORTLAUT>"
        f"<suc:EXAKTESUCHE>{'true' if exakte_suche else 'false'}</suc:EXAKTESUCHE>"
        f"<suc:SUCHBEREICH>{_esc(suchbereich)}</suc:SUCHBEREICH>"
        + opt("GERICHT", gericht)
        + opt("RECHTSFORM", rechtsform)
        + opt("RECHTSEIGENSCHAFT", rechtseigenschaft)
        + opt("ORTNR", ortnr)
        + "</suc:SUCHEFIRMAREQUEST>"
    )


def suche_urkunde_request(fnrs: str | list[str] | None = None, az: str | None = None) -> str:
    """Build a SUCHEURKUNDEREQUEST.

    Per WSDL (xs:choice) the request carries EITHER one Firmenbuchnummer
    OR one Aktenzeichen — multiple FNRs in one request are rejected with
    HTTP 400. For a list of FNRs, call this once per FNR.
    """
    if (fnrs is None) == (az is None):
        raise ValueError("suche_urkunde: pass exactly one of fnrs (single FNR) or az")
    if az is not None:
        item = f"<suc:AZ>{_esc(az)}</suc:AZ>"
    else:
        if isinstance(fnrs, list) and len(fnrs) != 1:
            raise ValueError(
                "suche_urkunde: the FBW API accepts only ONE Firmenbuchnummer "
                "per request (WSDL xs:choice); issue one call per FNR"
            )
        item = f"<suc:FNR>{_esc(normalize_fnr(fnrs[0] if isinstance(fnrs, list) else fnrs))}</suc:FNR>"
    return (
        f'<suc:SUCHEURKUNDEREQUEST xmlns:suc="{NS}/SucheUrkundeRequest">'
        + item
        + "</suc:SUCHEURKUNDEREQUEST>"
    )


# ------------------------------------------------------------------ client --

class FirmenbuchClient:
    def __init__(self, api_key: str | None = None, timeout: float = 60.0):
        self.api_key = os.environ.get("FIRMENBUCH_API_KEY", "") if api_key is None else api_key
        self.timeout = timeout

    def call(self, body_xml: str, action: str) -> str:
        """POST a SOAP 1.2 request; return the raw response XML string."""
        if not self.api_key:
            raise FirmenbuchAuthError(
                "FIRMENBUCH_API_KEY is not set. The Firmenbuch API requires a free "
                "token: log in with ID Austria at https://justizonline.gv.at/jop/web/iwg "
                "and file the 'Application for information reuse' (tile 'Antrag auf "
                "Informationsweiterverwendung'). After approval the token appears "
                "under your profile, tab 'Informationsweiterverwendung'."
            )
        envelope = build_envelope(body_xml).encode("utf-8")
        req = urllib.request.Request(
            ENDPOINT,
            data=envelope,
            headers={
                "Content-Type": "application/soap+xml;charset=UTF-8",
                "X-API-KEY": self.api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise FirmenbuchAuthError(
                    f"HTTP {exc.code}: API token rejected. Check FIRMENBUCH_API_KEY "
                    "(token from JustizOnline, profile tab 'Informationsweiterverwendung')."
                ) from exc
            if exc.code == 429:
                raise FirmenbuchRateLimitError(
                    "HTTP 429 Too Many Requests: server-side load limit reached; "
                    "retry later."
                ) from exc
            detail = self._http_error_detail(exc)
            msg = f"HTTP {exc.code} from FBW endpoint"
            if detail:
                msg += f": {detail}"
            if exc.code == 500 and "Zugriff nicht erlaubt" in detail:
                msg += " (token not authorized for this operation/range; " \
                       "e.g. wertetabellen needs a wider HVD scope, " \
                       "veraenderungen is only served for very recent dates)"
            raise FirmenbuchError(msg) from exc
        except urllib.error.URLError as exc:
            raise FirmenbuchError(f"Connection to FBW endpoint failed: {exc.reason}") from exc

    @staticmethod
    def _http_error_detail(exc: urllib.error.HTTPError) -> str:
        """Extract a human-readable reason from an error-response body, if any."""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            return ""
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return ""
        for tag in ("Text", "faultstring"):
            el = root.find(f".//{tag}")
            if el is None:
                # namespace-agnostic fallback (SOAP 1.2 fault Text lives in the envelope ns)
                el = root.find(f".//{{*}}{tag}")
            if el is not None and el.text:
                return el.text.strip()
        return ""

    def parse(self, response_xml: str) -> dict[str, Any]:
        """Parse a SOAP response; raise on a SOAP 1.1/1.2 fault; flatten the body."""
        root = ET.fromstring(response_xml)
        soap12_env = "http://www.w3.org/2003/05/soap-envelope"
        soap11_env = "http://schemas.xmlsoap.org/soap/envelope/"

        fault = root.find(f".//{{{soap12_env}}}Fault")
        if fault is not None:
            reason_el = fault.find(f".//{{{soap12_env}}}Text")
            reason = reason_el.text if reason_el is not None else "unknown SOAP fault"
            value_el = fault.find(f".//{{{soap12_env}}}Value")
            code = value_el.text if value_el is not None else ""
            raise FirmenbuchError(f"Firmenbuch SOAP fault [{code}]: {reason}")

        fault = root.find(f".//{{{soap11_env}}}Fault")
        if fault is not None:
            faultstring_el = fault.find("faultstring")
            reason = faultstring_el.text if faultstring_el is not None else "unknown SOAP fault"
            faultcode_el = fault.find("faultcode")
            code = faultcode_el.text if faultcode_el is not None else ""
            raise FirmenbuchError(f"Firmenbuch SOAP fault [{code}]: {reason}")

        body = root.find(f"{{{soap12_env}}}Body")
        if body is None:
            body = root.find(f"{{{soap11_env}}}Body")
        if body is None:
            raise FirmenbuchError("SOAP response has no Body")
        children = list(body)
        if not children:
            raise FirmenbuchError("SOAP Body is empty")
        return _flatten(children[0])


# -------------------------------------------------------------- xml -> dict --

def _tag(el: ET.Element) -> str:
    return el.tag.rsplit("}", 1)[-1]


def _attrs(el: ET.Element) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, value in el.attrib.items():
        name = name.rsplit("}", 1)[-1]
        out[name] = _coerce(value)
    return out


def _coerce(text: str | None) -> Any:
    if text is None:
        return None
    t = text.strip()
    if t.lower() == "true":
        return True
    if t.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", t):
        try:
            return int(t)
        except ValueError:
            return t
    return t


def _flatten(el: ET.Element) -> Any:
    """Recursively flatten XML to dicts/lists, collapsing single-element lists."""
    node: dict[str, Any] = {}
    node.update(_attrs(el))
    if el.text and el.text.strip():
        text_val = _coerce(el.text)
        if not node and not list(el):
            return text_val
        node["#text"] = text_val
    for child in el:
        key = _tag(child)
        val = _flatten(child)
        if key in node:
            if not isinstance(node[key], list):
                node[key] = [node[key]]
            node[key].append(val)
        else:
            node[key] = val
    return node


def collapse_single(value: Any) -> Any:
    """Collapse one-element lists to scalars/dicts (FBW repeats elements for lists)."""
    if isinstance(value, list):
        return [collapse_single(v) for v in value]
    if isinstance(value, dict):
        return {k: collapse_single(v) for k, v in value.items()}
    return value


# ------------------------------------------------------------ base64 docs --

def decode_document(content_b64: str) -> bytes:
    """Decode a URKUNDERESPONSE CONTENT (base64) into raw bytes."""
    return base64.b64decode(content_b64)
