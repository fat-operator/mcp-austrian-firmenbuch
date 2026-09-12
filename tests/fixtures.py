"""Request envelope fixtures from the official FBW spec v1.3."""

AUSZUG_V2 = (
    '<aus:AUSZUG_V2_REQUEST xmlns:aus="ns://firmenbuch.justiz.gv.at/Abfrage/v2/AuszugRequest">'
    "<aus:FNR>5h</aus:FNR>"
    "<aus:STICHTAG>2015-12-22</aus:STICHTAG>"
    "<aus:UMFANG>Kurzinformation</aus:UMFANG>"
    "</aus:AUSZUG_V2_REQUEST>"
)

URKUNDE = (
    '<urk:URKUNDEREQUEST xmlns:urk="ns://firmenbuch.justiz.gv.at/Abfrage/UrkundeRequest">'
    "<urk:KEY>304188_0070711322495_000___000_30_7730290_XML</urk:KEY>"
    "</urk:URKUNDEREQUEST>"
)

VERAENDERUNGEN_FIRMA = (
    '<ver:VERAENDERUNGENFIRMAREQUEST xmlns:ver="ns://firmenbuch.justiz.gv.at/Abfrage/VeraenderungenFirmaRequest">'
    "<ver:VON>2014-11-25</ver:VON>"
    "<ver:BIS>2014-11-25</ver:BIS>"
    "<ver:GERICHT>007</ver:GERICHT>"
    "<ver:RECHTSFORM>AG</ver:RECHTSFORM>"
    "</ver:VERAENDERUNGENFIRMAREQUEST>"
)

VERAENDERUNGEN_URKUNDE = (
    '<ver:VERAENDERUNGENURKUNDEREQUEST xmlns:ver="ns://firmenbuch.justiz.gv.at/Abfrage/VeraenderungenUrkundeRequest">'
    "<ver:VON>2014-11-25</ver:VON>"
    "<ver:BIS>2014-11-25</ver:BIS>"
    "</ver:VERAENDERUNGENURKUNDEREQUEST>"
)

SUCHE_FIRMA = (
    '<suc:SUCHEFIRMAREQUEST xmlns:suc="ns://firmenbuch.justiz.gv.at/Abfrage/SucheFirmaRequest">'
    "<suc:FIRMENWORTLAUT>mayer</suc:FIRMENWORTLAUT>"
    "<suc:EXAKTESUCHE>false</suc:EXAKTESUCHE>"
    "<suc:SUCHBEREICH>1</suc:SUCHBEREICH>"
    "<suc:GERICHT/>"
    "<suc:RECHTSFORM/>"
    "<suc:RECHTSEIGENSCHAFT/>"
    "<suc:ORTNR/>"
    "</suc:SUCHEFIRMAREQUEST>"
)

SUCHE_URKUNDE = (
    '<suc:SUCHEURKUNDEREQUEST xmlns:suc="ns://firmenbuch.justiz.gv.at/Abfrage/SucheUrkundeRequest">'
    "<suc:FNR>629a</suc:FNR>"
    "</suc:SUCHEURKUNDEREQUEST>"
)

AUSZUG_RESPONSE = """<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">
<env:Header/><env:Body>
<ns6:AUSZUG_V2_RESPONSE
 ns6:ABFRAGEZEITPUNKT="2025-01-16T14:03:33.146+01:00" ns6:FNR="58468 h"
 ns6:PRUEFSUMME="452407D2F7C4C4A3ED83D51DFB961E82" ns6:STICHTAG="2020-11-10"
 ns6:UMFANG="Kurzinformation"
 xmlns:ns6="ns://firmenbuch.justiz.gv.at/Abfrage/v2/AuszugResponse">
<ns6:FIRMA>
<ns6:FI_DKZ02 ns6:AUFRECHT="true" ns6:VNR="001">
<ns6:BEZEICHNUNG>EDV-Technik Dipl.-Ing. Went</ns6:BEZEICHNUNG>
<ns6:BEZEICHNUNG>Gesellschaft m.b.H.</ns6:BEZEICHNUNG>
</ns6:FI_DKZ02>
<ns6:FI_DKZ03 ns6:AUFRECHT="true" ns6:VNR="034">
<ns6:STELLE>Kaerntner Strasse 337</ns6:STELLE>
<ns6:STAAT>AUT</ns6:STAAT>
<ns6:PLZ>8054</ns6:PLZ>
<ns6:ORT>Graz</ns6:ORT>
<ns6:ZUSTELLBAR>true</ns6:ZUSTELLBAR>
</ns6:FI_DKZ03>
</ns6:FIRMA>
</ns6:AUSZUG_V2_RESPONSE>
</env:Body></env:Envelope>"""

SUCHE_FIRMA_RESPONSE = """<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">
<env:Header/><env:Body>
<ns13:SUCHEFIRMARESPONSE ns13:REQUEST_EXAKTESUCHE="false"
 ns13:REQUEST_FIRMENWORTLAUT="mayer" ns13:REQUEST_SUCHBEREICH="1"
 xmlns:ns13="ns://firmenbuch.justiz.gv.at/Abfrage/SucheFirmaResponse">
<ns13:ERGEBNIS>
<ns13:FNR>145733p</ns13:FNR>
<ns13:NAME>"A &amp; S" Mayer OEG</ns13:NAME>
<ns13:SITZ>Wien</ns13:SITZ>
<ns13:RECHTSFORM><ns13:CODE>OG</ns13:CODE><ns13:TEXT>Offene Gesellschaft</ns13:TEXT></ns13:RECHTSFORM>
<ns13:GERICHT><ns13:CODE>007</ns13:CODE><ns13:TEXT>Handelsgericht Wien</ns13:TEXT></ns13:GERICHT>
</ns13:ERGEBNIS>
<ns13:ERGEBNIS>
<ns13:FNR>145734x</ns13:FNR>
<ns13:NAME>Mayer Handel GmbH</ns13:NAME>
<ns13:SITZ>Graz</ns13:SITZ>
<ns13:RECHTSFORM><ns13:CODE>GmbH</ns13:CODE><ns13:TEXT>Gesellschaft mit beschraenkter Haftung</ns13:TEXT></ns13:RECHTSFORM>
<ns13:GERICHT><ns13:CODE>006</ns13:CODE><ns13:TEXT>Landesgericht fuer Zivilrechtssachen Graz</ns13:TEXT></ns13:GERICHT>
</ns13:ERGEBNIS>
</ns13:SUCHEFIRMARESPONSE>
</env:Body></env:Envelope>"""

URKUNDE_RESPONSE = """<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">
<env:Header/><env:Body>
<ns7:URKUNDERESPONSE ns7:STICHTAG="2015-12-23"
 xmlns:ns7="ns://firmenbuch.justiz.gv.at/Abfrage/UrkundeResponse">
<ns7:METADATEN>
<ns7:KEY>304188_0070711322495_000___000_30_7730290_XML</ns7:KEY>
<ns7:URKID>7730290</ns7:URKID>
<ns7:FNR>304188 k</ns7:FNR>
<ns7:AZ>007 071 Fr 22495/13 p</ns7:AZ>
<ns7:DOKUMENTART><ns7:CODE>48</ns7:CODE><ns7:TEXT>Jahresabschluss</ns7:TEXT></ns7:DOKUMENTART>
<ns7:DOKUMENTENDATUM>2012-12-31</ns7:DOKUMENTENDATUM>
<ns7:ZNR>000</ns7:ZNR>
<ns7:PNR/>
<ns7:FKEN/>
<ns7:UNR>000</ns7:UNR>
<ns7:DKZ>30</ns7:DKZ>
<ns7:VNR>006</ns7:VNR>
<ns7:BEMERKUNG/>
<ns7:STICHTAG>2012-12-31</ns7:STICHTAG>
<ns7:GKL>K</ns7:GKL>
<ns7:VON>2013-11-13</ns7:VON>
<ns7:OEFFENTLICH>true</ns7:OEFFENTLICH>
</ns7:METADATEN>
<ns7:DOKUMENT>
<ns7:CONTENTTYPE>application/xml</ns7:CONTENTTYPE>
<ns7:DATEIENDUNG>xml</ns7:DATEIENDUNG>
<ns7:CONTENT>PD94bWwgdmVyc2lvbj0iMS4wIj8+</ns7:CONTENT>
</ns7:DOKUMENT>
</ns7:URKUNDERESPONSE>
</env:Body></env:Envelope>"""

VERAENDERUNGEN_FIRMA_RESPONSE = """<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">
<env:Header/><env:Body>
<ns9:VERAENDERUNGENFIRMARESPONSE ns9:BIS="2014-11-25" ns9:GERICHT="007"
 ns9:RECHTSFORM="AG" ns9:VON="2014-11-25"
 xmlns:ns9="ns://firmenbuch.justiz.gv.at/Abfrage/VeraenderungenFirmaResponse">
<ns9:VERAENDERUNG>
<ns9:FNR>73589 w</ns9:FNR><ns9:VNR>032</ns9:VNR>
<ns9:VOLLZUGSDATUM>2014-11-25</ns9:VOLLZUGSDATUM>
<ns9:ARTDERVERAENDERUNG>Aenderung</ns9:ARTDERVERAENDERUNG>
</ns9:VERAENDERUNG>
<ns9:VERAENDERUNG>
<ns9:FNR>257770 z</ns9:FNR><ns9:VNR>012</ns9:VNR>
<ns9:VOLLZUGSDATUM>2014-11-25</ns9:VOLLZUGSDATUM>
<ns9:ARTDERVERAENDERUNG>Aenderung</ns9:ARTDERVERAENDERUNG>
</ns9:VERAENDERUNG>
</ns9:VERAENDERUNGENFIRMARESPONSE>
</env:Body></env:Envelope>"""

SUCHE_URKUNDE_RESPONSE = """<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">
<env:Header/><env:Body>
<ns15:SUCHEURKUNDERESPONSE ns15:REQUEST_FNR="629 a"
 xmlns:ns15="ns://firmenbuch.justiz.gv.at/Abfrage/SucheUrkundeResponse">
<ns15:ERGEBNIS>
<ns15:KEY>000629_6380470600057_000___000_30_1310866_PDF</ns15:KEY>
<ns15:FNR>629 a</ns15:FNR>
<ns15:AZ>638 047 Fr 57/06 i</ns15:AZ>
<ns15:DOKUMENTART><ns15:CODE>48</ns15:CODE><ns15:TEXT>Jahresabschluss</ns15:TEXT></ns15:DOKUMENTART>
<ns15:CONTENTTYPE>application/pdf</ns15:CONTENTTYPE>
<ns15:DATEIENDUNG>pdf</ns15:DATEIENDUNG>
<ns15:GROESSE>19343</ns15:GROESSE>
<ns15:BEMERKUNG>31.3.2004</ns15:BEMERKUNG>
<ns15:STICHTAG>2004-03-31</ns15:STICHTAG>
<ns15:GKL/>
<ns15:VNR>011</ns15:VNR>
<ns15:EINGEREICHT>2006-01-02</ns15:EINGEREICHT>
</ns15:ERGEBNIS>
</ns15:SUCHEURKUNDERESPONSE>
</env:Body></env:Envelope>"""

FAULT_SOAP12 = """<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">
<env:Header/><env:Body>
<env:Fault>
<env:Code><env:Value>env:Receiver</env:Value></env:Code>
<env:Reason><env:Text xml:lang="en">Stichtag darf nicht in der Zukunft sein</env:Text></env:Reason>
</env:Fault>
</env:Body></env:Envelope>"""

FAULT_SOAP11 = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
<soapenv:Body>
<soapenv:Fault>
<faultcode>soapenv:Receiver</faultcode>
<faultstring>BIS-Datum darf nicht vor dem VON-Datum liegen</faultstring>
</soapenv:Fault>
</soapenv:Body></soapenv:Envelope>"""
