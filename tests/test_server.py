"""Tests for the MCP tool layer: tool registration and request wiring."""

import sys
import types
from unittest.mock import patch

import pytest

mcp_stub = types.ModuleType("mcp")
server_stub = types.ModuleType("mcp.server")
fastmcp_stub = types.ModuleType("mcp.server.fastmcp")


class _FakeFastMCP:
    def __init__(self, *a, **k):
        self.settings = types.SimpleNamespace(host="127.0.0.1", port=8000)
        self._tools = {}

    def tool(self, *a, **k):
        def deco(fn):
            self._tools[fn.__name__] = fn
            return fn

        return deco

    def run(self, transport="stdio"):
        self._ran = transport


mcp_stub.server = server_stub
server_stub.fastmcp = fastmcp_stub
fastmcp_stub.FastMCP = _FakeFastMCP
for name, mod in [("mcp", mcp_stub), ("mcp.server", server_stub), ("mcp.server.fastmcp", fastmcp_stub)]:
    sys.modules.setdefault(name, mod)

from server import (  # noqa: E402
    auszug,
    mcp,
    suche_firma,
    suche_urkunde,
    urkunde,
    veraenderungen_firma,
    veraenderungen_urkunde,
    wertetabellen,
)


def test_all_tools_registered():
    assert set(mcp._tools) == {
        "suche_firma",
        "auszug",
        "suche_urkunde",
        "urkunde",
        "veraenderungen_firma",
        "veraenderungen_urkunde",
        "wertetabellen",
    }


@pytest.fixture()
def fake_response():
    return lambda body: {"ok": True, "body": body}


def test_tool_suche_firma_wiring(fake_response):
    with patch("server._run", fake_response):
        out = suche_firma("mayer")
    assert out["ok"] is True
    assert "SUCHEFIRMAREQUEST" in out["body"]


def test_tool_auszug_wiring(fake_response):
    with patch("server._run", fake_response):
        out = auszug("419999x", umfang="Vollinformation")
    assert "AUSZUG_V2_REQUEST" in out["body"]
    assert "419999x" in out["body"]


def test_tool_urkunde_wiring(fake_response):
    with patch("server._run", fake_response):
        out = urkunde("304188_0070711322495_000___000_30_7730290_XML")
    assert "URKUNDEREQUEST" in out["body"]


def test_tool_veraenderungen_wiring(fake_response):
    with patch("server._run", fake_response):
        out = veraenderungen_firma("2014-11-25", "2014-11-25", gericht="007")
        assert "GERICHT>007<" in out["body"]
        out2 = veraenderungen_urkunde("2014-11-25", "2014-11-25")
        assert "VERAENDERUNGENURKUNDEREQUEST" in out2["body"]


def test_tool_suche_urkunde_wiring(fake_response):
    with patch("server._run", fake_response):
        out = suche_urkunde(fnr="629 a")
        assert "629a" in out["body"]
        out2 = suche_urkunde(az="007 61 Fr 2164/15 w")
        assert "AZ>007 61 Fr 2164/15 w<" in out2["body"]


def test_suche_urkunde_rejects_both_or_neither(fake_response):
    with pytest.raises(ValueError):
        suche_urkunde(fnr="629 a", az="007 61 Fr 2164/15 w")
    with pytest.raises(ValueError):
        suche_urkunde()


def test_suche_urkunde_request_rejects_multi_fnr():
    from firmenbuch.client import suche_urkunde_request

    with pytest.raises(ValueError):
        suche_urkunde_request(["435836k", "629a"])


def test_wertetabellen_registered_and_wiring(fake_response):
    assert "wertetabellen" in mcp._tools
    with patch("server._run", fake_response):
        out = wertetabellen(tabelle="FBHG")
    assert "TABELLE>FBHG<" in out["body"]
