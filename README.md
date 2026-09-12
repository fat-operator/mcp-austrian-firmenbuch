# mcp-austrian-firmenbuch

MCP server exposing the Austrian **Firmenbuch** (Austrian Business Register / Company
Register) via the official BMJ **FBW-WebServices (HVD)** SOAP API, as
[High Value Datasets](https://justizonline.gv.at/jop/web/iwg) under Commission
Implementing Regulation (EU) 2023/138.

Implemented against the official interface specification *FBW-WebServices (HVD)
Schnittstellenbeschreibung*, Version 1.3 (22.05.2025).

## Requirements

- Python 3.10+
- `mcp>=1,<2` (FastMCP API)
- A valid JustizOnline IWG API token (see below)

## API key — how to request one

The API is **free of charge**, but every call (including the WSDL) requires a
token. To obtain one:

1. You need an **ID Austria** account.
2. Log in to [JustizOnline](https://justizonline.gv.at/jop/web/) with your ID Austria.
3. Go to [Information on the Reuse of Information (IWG)](https://justizonline.gv.at/jop/web/iwg)
   and click the tile **"Antrag auf Informationsweiterverwendung"**
   ("Application for information reuse") — direct link:
   <https://justizonline.gv.at/jop/web/iwg/register>
4. Apply for the API **"Company data in accordance with Annex 5 of Commission
   Implementing Regulation (EU) 2023/138 … (High Value Datasets (HVD) of the
   Business Register)"** (internal code **FBW**). The application is decided by
   the Federal Ministry of Justice (BMJ).
5. Once approved, your token appears on JustizOnline under your profile, tab
   **"Informationsweiterverwendung"** ("Information Reuse").

Set the token as `FIRMENBUCH_API_KEY` in your environment (or a repo-local
`.env` — see `.env.example`). The server sends it as the `X-API-KEY` request
header on every SOAP call.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install "mcp>=1,<2"
cp .env.example .env   # put your token into .env
```

Note (this workspace): `builder/repos/` sits on a filesystem that rejects
symlinks, so in-repo venvs cannot be created. Use
`uv venv /opt/hermes/.local/opt/mcp-firmenbuch-venv` +
`uv pip install --python /opt/hermes/.local/opt/mcp-firmenbuch-venv/bin/python -e .`
instead; tests run with that interpreter.

## Run

```bash
python server.py            # stdio MCP server
python server.py --http     # or HTTP streamable on :8000/mcp
```

### MCP client registration (stdio)

```json
{
  "mcpServers": {
    "firmenbuch": {
      "command": "python",
      "args": ["/path/to/mcp-austrian-firmenbuch/server.py"],
      "env": { "FIRMENBUCH_API_KEY": "<your-token>" }
    }
  }
}
```

## Tools

| Tool | Description |
|---|---|
| `firmenbuch_suche_firma` | Search companies by name (`firmenwortlaut`), optional filters: court, legal form, legal quality, municipality number |
| `firmenbuch_auszug` | Company extract (v2) by Firmenbuchnummer; optional `stichtag` date and `umfang` (Kurzinformation/Vollinformation) |
| `firmenbuch_suche_urkunde` | List filed documents for a Firmenbuchnummer **or** an Aktenzeichen (`az`) — the WSDL `xs:choice` allows exactly one of the two per request |
| `firmenbuch_urkunde` | Fetch a document by its `KEY` (returns base64 content + metadata) |
| `firmenbuch_veraenderungen_firma` | Register changes for companies in a date range (VON/BIS, **max 7 days** per request), optional court/legal-form filter |
| `firmenbuch_veraenderungen_urkunde` | Filed-document changes in a date range (VON/BIS, **max 7 days** per request) |
| `firmenbuch_wertetabellen` | Fetch code/value tables (courts `FBHG`, legal forms `FBFORM`, document types `FBDOKT`/`FBURKT`, municipalities `FBORT`, ...). Undocumented in spec v1.3 but part of the live WSDL; requires a token scope that covers it — otherwise the service returns "Zugriff nicht erlaubt!" |

### Identifiers

- **Firmenbuchnummer (FNR)**: up to 6 digits plus a check letter, e.g. `419999x`
  or `58468 h` (spaces are tolerated).
- **Urkunde KEY**: e.g. `304188_0070711322495_000___000_30_7730290_XML`
  (returned by `suche_urkunde` / `veraenderungen_urkunde`).

## Technical notes

- Endpoint: `https://justizonline.gv.at/jop/api/at.gv.justiz.fbw/ws`
- WSDL: `https://justizonline.gv.at/jop/api/at.gv.justiz.fbw/ws/fbw.wsdl` (also key-protected)
- SOAP 1.2 (`Content-Type: application/soap+xml;charset=UTF-8`), header `X-API-KEY`
- Rate limiting: HTTP **429 Too Many Requests** when exceeded — the server
  surfaces this as a clear error instead of retry-storming.
- SOAP faults inside HTTP 5xx error bodies are decoded and surfaced with their
  German reason text (e.g. "Der Zeitraum darf 7 Tage nicht überschreiten" for
  veraenderungen ranges > 7 days, "Zugriff nicht erlaubt!" when the token's
  HVD scope does not cover an operation).
- All tools accept the raw XML string in the response body (`raw=True`) if you
  need fields this server does not parse out.

Data license / terms: use under the JustizOnline IWG terms of use
(<https://justizonline.gv.at/jop/web/iwg/terms>). Cite the source (BMJ Firmenbuch)
when republishing.

## Tests

```bash
python -m pytest -q
```

Unit tests cover XML envelope building and response parsing against fixtures
derived from the official spec examples — no live API access needed.


## License

Licensed under the Apache License, Version 2.0 — see [LICENSE](LICENSE).

Not affiliated with the BMJ / JustizOnline / the Austrian Commercial Register.
The Firmenbuch **data** obtained through this server is not covered by this
license: users are responsible for complying with the JustizOnline IWG terms
of use (<https://justizonline.gv.at/jop/web/iwg/terms>) when consuming or
republishing register data. Each user brings their own API token.
