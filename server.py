"""MCP server exposing the Austrian Firmenbuch FBW-WebServices (HVD) API.

Six tools, one per operation of the official BMJ interface spec v1.3:
suche_firma, auszug (v2), suche_urkunde, urkunde,
veraenderungen_firma, veraenderungen_urkunde.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from typing import Any

from mcp.server.fastmcp import FastMCP

from firmenbuch.client import (
    FirmenbuchAuthError,
    FirmenbuchClient,
    FirmenbuchError,
    FirmenbuchRateLimitError,
    auszug_v2_request,
    normalize_fnr,
    suche_firma_request,
    suche_urkunde_request,
    urkunde_request,
    veraenderungen_firma_request,
    veraenderungen_urkunde_request,
    wertetabellen_request,
)

mcp = FastMCP(
    "firmenbuch",
    instructions=(
        "Austrian Firmenbuch (Business Register) via the official BMJ "
        "FBW-WebServices (HVD) SOAP API. Requires FIRMENBUCH_API_KEY. "
        "Company search returns FNR (Firmenbuchnummer); use it for extracts "
        "and document searches."
    ),
)

_client = FirmenbuchClient()


def _run(body_xml: str) -> dict[str, Any]:
    """Call the service and convert the flattened response into plain JSON."""
    raw = _client.call(body_xml, action="call")
    return json.loads(json.dumps(_client.parse(raw), default=str))


@mcp.tool()
def suche_firma(
    firmenwortlaut: str,
    exakte_suche: bool = False,
    suchbereich: str = "1",
    gericht: str = "",
    rechtsform: str = "",
    rechtseigenschaft: str = "",
    ortnr: str = "",
) -> dict[str, Any]:
    """Search Austrian companies by name in the Firmenbuch.

    Args:
        firmenwortlaut: Company name fragment (e.g. "mayer"). For exact matches
            set exakte_suche=true.
        exakte_suche: Exact-match instead of fuzzy search.
        suchbereich: Search scope: "1" = entire register, "2" = branches only.
        gericht: Optional court code (e.g. "007" = Handelsgericht Wien).
        rechtsform: Optional legal form (GmbH, AG, OG, KG, e.U. ...).
        rechtseigenschaft: Optional legal quality code.
        ortnr: Optional municipality number.
    """
    return _run(
        suche_firma_request(
            firmenwortlaut,
            exakte_suche=exakte_suche,
            suchbereich=suchbereich,
            gericht=gericht or None,
            rechtsform=rechtsform or None,
            rechtseigenschaft=rechtseigenschaft or None,
            ortnr=ortnr or None,
        )
    )


@mcp.tool()
def auszug(
    fnr: str,
    stichtag: str = "",
    umfang: str = "Kurzinformation",
) -> dict[str, Any]:
    """Full Firmenbuch extract (v2) for a company by Firmenbuchnummer.

    Args:
        fnr: Firmenbuchnummer, up to 6 digits plus check letter (e.g. "419999x").
        stichtag: Optional reference date (YYYY-MM-DD); defaults to today.
        umfang: "Kurzinformation" (default) or "Vollinformation".
    """
    if not stichtag:
        stichtag = date.today().isoformat()
    else:
        try:
            date.fromisoformat(stichtag)
        except ValueError as exc:
            raise ValueError("stichtag must be YYYY-MM-DD") from exc
    return _run(auszug_v2_request(fnr, stichtag, umfang))


@mcp.tool()
def suche_urkunde(fnr: str = "", az: str = "") -> dict[str, Any]:
    """List filed documents (Urkunden) for a company or an Aktenzeichen.

    Per the FBW WSDL (xs:choice) exactly ONE of the two is allowed per
    request — pass a Firmenbuchnummer OR an Aktenzeichen, never both.

    Args:
        fnr: Firmenbuchnummer (e.g. "629 a").
        az: Aktenzeichen (e.g. "007 61 Fr 2164/15 w"); used when fnr is empty.
    """
    if bool(fnr) == bool(az):
        raise ValueError("suche_urkunde: pass exactly one of fnr or az")
    return _run(suche_urkunde_request(fnrs=fnr or None, az=az or None))


@mcp.tool()
def urkunde(key: str) -> dict[str, Any]:
    """Fetch a Firmenbuch document by its KEY.

    Returns metadata plus CONTENT (base64) with CONTENTTYPE (application/pdf or
    application/xml) so callers can save the file locally.

    Args:
        key: Document KEY as returned by suche_urkunde / veraenderungen_urkunde,
            e.g. "304188_0070711322495_000___000_30_7730290_XML".
    """
    return _run(urkunde_request(key))


@mcp.tool()
def veraenderungen_firma(
    von: str,
    bis: str,
    gericht: str = "",
    rechtsform: str = "",
) -> dict[str, Any]:
    """Register changes (Veraenderungen) for companies in a date range.

    Args:
        von: Start date YYYY-MM-DD (inclusive).
        bis: End date YYYY-MM-DD (inclusive; must be >= von; the FBW API
            limits the range to a maximum of 7 days).
        gericht: Optional court code filter.
        rechtsform: Optional legal form filter (e.g. "AG").
    """
    return _run(veraenderungen_firma_request(von, bis, gericht or None, rechtsform or None))


@mcp.tool()
def veraenderungen_urkunde(von: str, bis: str) -> dict[str, Any]:
    """Filed-document changes (Urkunden) in a date range.

    Args:
        von: Start date YYYY-MM-DD (inclusive).
        bis: End date YYYY-MM-DD (inclusive; must be >= von; the FBW API
            limits the range to a maximum of 7 days).
    """
    return _run(veraenderungen_urkunde_request(von, bis))


@mcp.tool()
def wertetabellen(tabelle: str = "ALL", stichtag: str = "") -> dict[str, Any]:
    """Fetch Firmenbuch code/value tables (courts, legal forms, document types...).

    These are the code tables needed for filtering: GERICHT court codes (FBHG),
    legal forms (FBFORM), document types (FBDOKT/FBURKT), municipalities (FBORT),
    etc.

    Args:
        tabelle: One of FBDOKT, FBFORM, FBFUNH, FBFUNK, FBGELD, FBHG, FBLAND,
            FBORT, FBPLZ, FBURKT, FBTTXT, or ALL (default).
        stichtag: Optional reference date YYYY-MM-DD.
    """
    if stichtag:
        try:
            date.fromisoformat(stichtag)
        except ValueError as exc:
            raise ValueError("stichtag must be YYYY-MM-DD") from exc
    return _run(wertetabellen_request(tabelle, stichtag or None))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http", action="store_true", help="Run HTTP streamable on :8000")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.http:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    try:
        main()
    except FirmenbuchAuthError as exc:  # pragma: no cover - startup convenience
        raise SystemExit(f"error: {exc}") from exc
