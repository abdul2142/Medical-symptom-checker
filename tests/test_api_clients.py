"""Tests for the openFDA / RxNorm / MedlinePlus clients.

No network access: ``api_clients.get_session`` is replaced with a stub, so every
transport and payload case is reproducible.
"""

from __future__ import annotations

import json

import pytest
import requests

import api_clients


# --- Test doubles -----------------------------------------------------------

class StubResponse:
    """The slice of ``requests.Response`` that ``_fetch`` relies on."""

    def __init__(self, status=200, body=b"", encoding="utf-8"):
        self.status_code = status
        self.body = body
        self.encoding = encoding

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def iter_content(self, chunk_size=65536):
        for start in range(0, len(self.body), chunk_size):
            yield self.body[start:start + chunk_size]

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class StubSession:
    """Returns queued responses and records every request made."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, params=None, timeout=None, stream=None):
        self.calls.append({"url": url, "params": params or {}})
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    @property
    def last(self):
        return self.calls[-1]


@pytest.fixture
def stub(monkeypatch):
    """Install a stub session; returns a setter taking the queued responses."""

    def install(*responses):
        session = StubSession(responses)
        monkeypatch.setattr(api_clients, "get_session", lambda: session)
        return session

    return install


def body(payload) -> bytes:
    return json.dumps(payload).encode()


# --- Session ----------------------------------------------------------------

def test_session_identifies_itself_and_is_reused(monkeypatch):
    monkeypatch.setattr(api_clients, "_session", None)
    session = api_clients.get_session()
    assert "CareCheck" in session.headers["User-Agent"]
    assert api_clients.get_session() is session


# --- Size cap ---------------------------------------------------------------

def test_oversized_response_is_refused(stub, monkeypatch):
    """A cap bounds a malformed, hostile or compressed-bomb payload."""
    monkeypatch.setattr(api_clients, "MAX_RESPONSE_BYTES", 128)
    stub(StubResponse(200, b"x" * 500))

    result = api_clients.normalize_medicine_rxnorm("ibuprofen")
    assert "unexpectedly large" in result["error"]


def test_payload_at_the_cap_is_still_read(stub, monkeypatch):
    monkeypatch.setattr(api_clients, "MAX_RESPONSE_BYTES", 4096)
    stub(StubResponse(200, body({"drugGroup": {"conceptGroup": []}})))
    assert "error" not in api_clients.normalize_medicine_rxnorm("ibuprofen")


# --- RxNorm -----------------------------------------------------------------

RXNORM_OK = {
    "drugGroup": {"conceptGroup": [
        {"tty": "SBD", "conceptProperties": [
            {"rxcui": "1", "name": "Ibuprofen 200 MG", "synonym": "", "tty": "SBD"}]},
        {"tty": "IN", "conceptProperties": [
            {"rxcui": "2", "name": "ibuprofen", "synonym": "", "tty": "IN"}]},
    ]}
}


def test_rxnorm_flattens_concept_groups(stub):
    stub(StubResponse(200, body(RXNORM_OK)))
    result = api_clients.normalize_medicine_rxnorm("ibuprofen")

    assert result["query"] == "ibuprofen"
    assert [m["rxcui"] for m in result["matches"]] == ["1", "2"]


def test_rxnorm_handles_an_empty_result(stub):
    stub(StubResponse(200, body({"drugGroup": {}})))
    assert api_clients.normalize_medicine_rxnorm("zzzz")["matches"] == []


def test_rxnorm_reports_invalid_json(stub):
    stub(StubResponse(200, b"<html>not json</html>"))
    assert "invalid JSON" in api_clients.normalize_medicine_rxnorm("ibuprofen")["error"]


def test_rxnorm_reports_a_transport_failure(stub):
    stub(requests.ConnectionError("no route to host"))
    assert "RxNorm request failed" in api_clients.normalize_medicine_rxnorm("x")["error"]


def test_rxnorm_requires_a_query(stub):
    stub()
    assert "error" in api_clients.normalize_medicine_rxnorm("   ")


# --- MedlinePlus ------------------------------------------------------------

MEDLINE_XML = """<nlmSearchResult><list>
  <document rank="0" url="https://medlineplus.gov/painrelievers.html">
    <content name="title">&lt;span class="qt0"&gt;Pain&lt;/span&gt; Relievers</content>
    <content name="FullSummary">What are pain relievers?&lt;p&gt;Medicines that reduce pain.&lt;/p&gt;</content>
  </document></list></nlmSearchResult>"""


def test_medlineplus_parses_titles_and_summaries(stub):
    stub(StubResponse(200, MEDLINE_XML.encode()))
    result = api_clients.search_medlineplus("pain")

    [item] = result["results"]
    assert item["title"] == "Pain Relievers"
    assert item["summary"] == "What are pain relievers? Medicines that reduce pain."


def test_medlineplus_truncates_long_summaries():
    long_text = "word " * 200
    xml = (f'<r><document url="https://x"><content name="title">T</content>'
           f'<content name="FullSummary">{long_text}</content></document></r>')
    [item] = api_clients.parse_medlineplus_xml(xml)

    assert len(item["summary"]) <= api_clients.SUMMARY_LENGTH + 1
    assert item["summary"].endswith("…")


def test_medlineplus_skips_documents_without_a_title_or_url():
    xml = ('<r><document url="https://x"><content name="FullSummary">s</content></document>'
           '<document><content name="title">No url</content></document></r>')
    assert api_clients.parse_medlineplus_xml(xml) == []


def test_medlineplus_reports_unreadable_xml(stub):
    stub(StubResponse(200, b"<not-xml"))
    assert "unreadable" in api_clients.search_medlineplus("pain")["error"]


def test_medlineplus_reports_a_transport_failure(stub):
    stub(requests.Timeout("timed out"))
    assert "MedlinePlus request failed" in api_clients.search_medlineplus("pain")["error"]


# --- openFDA ----------------------------------------------------------------

def label(generic="ibuprofen", brand="Advil", set_id="abc", **fields):
    return {
        "openfda": {"generic_name": [generic], "brand_name": [brand],
                    "manufacturer_name": ["Acme"]},
        "set_id": set_id,
        **{key: [value] for key, value in fields.items()},
    }


def test_openfda_maps_label_fields(stub):
    stub(StubResponse(200, body({"results": [label(
        purpose="Pain relief", indications_and_usage="For headache",
        warnings="Ask a doctor", contraindications="None known")]})))

    [match] = api_clients.search_openfda_medicine("ibuprofen")["matches"]
    assert match["generic_name"] == "ibuprofen"
    assert match["brand_name"] == "Advil"
    assert match["manufacturer"] == "Acme"
    assert match["purpose"] == "Pain relief"
    assert match["warnings"] == "Ask a doctor"


def test_openfda_fills_missing_fields_with_not_listed(stub):
    stub(StubResponse(200, body({"results": [{"openfda": {}, "set_id": "x"}]})))
    [match] = api_clients.search_openfda_medicine("ibuprofen")["matches"]

    assert match["brand_name"] == "Not listed"
    assert match["warnings"] == "Not listed"


def test_openfda_deduplicates_repeated_labels(stub):
    duplicate = label(set_id="same")
    stub(StubResponse(200, body({"results": [duplicate, dict(duplicate)]})))
    assert len(api_clients.search_openfda_medicine("ibuprofen")["matches"]) == 1


def test_openfda_tries_each_field_in_turn(stub):
    """404 means "no match" at openFDA, so the next field is tried."""
    session = stub(
        StubResponse(404),
        StubResponse(404),
        StubResponse(200, body({"results": [label()]})),
    )
    assert api_clients.search_openfda_medicine("ibuprofen")["matches"]
    assert len(session.calls) == 3
    assert 'openfda.substance_name:"ibuprofen"' == session.last["params"]["search"]


def test_openfda_no_match_is_not_an_error(stub):
    stub(StubResponse(404), StubResponse(404), StubResponse(404))
    result = api_clients.search_openfda_medicine("zzzz")

    assert result["matches"] == []
    assert "error" not in result


def test_openfda_reports_a_real_failure(stub):
    stub(*[requests.ConnectionError("down")] * 3)
    assert "FDA label lookup failed" in api_clients.search_openfda_medicine("x")["error"]


def test_openfda_requires_a_query(stub):
    stub()
    assert "error" in api_clients.search_openfda_medicine("  ")


# --- openFDA query escaping -------------------------------------------------

@pytest.mark.parametrize("raw,cleaned", [
    ('ibu"profen', "ibu profen"),
    ("ibuprofen:400", "ibuprofen 400"),
    ("co-codamol", "co codamol"),
    ("vitamin (d)", "vitamin d"),
    ("aspirin AND acetaminophen", "aspirin AND acetaminophen"),
    ("drug && other", "drug other"),
    ("wild*card?", "wild card"),
])
def test_lucene_specials_are_stripped(raw, cleaned):
    assert api_clients._clean_lucene_term(raw) == cleaned


def test_the_search_phrase_stays_quoted_and_intact(stub):
    session = stub(StubResponse(200, body({"results": [label()]})))
    api_clients.search_openfda_medicine('ibu"profen')
    assert session.last["params"]["search"] == 'openfda.generic_name:"ibu profen"'


def test_a_query_of_only_punctuation_is_rejected(stub):
    stub()
    result = api_clients.search_openfda_medicine("***")
    assert "letters or numbers" in result["error"]
