"""Read-only clients for public U.S. National Library of Medicine and FDA APIs.

Three reference sources, none of which require a key:

* **openFDA** drug labels -- labelled uses, warnings, contraindications.
* **RxNorm** -- normalises a typed medicine name to standard concepts.
* **MedlinePlus** -- plain-language consumer health topics.

These are *reference lookups*, never a prescribing engine. Every function
returns either a result dict or ``{"error": "..."}``; nothing raises, so the UI
can render a failure without special-casing exceptions.

Responses are read with a byte cap. The payloads are small by design, and a cap
protects the parser from a malformed or hostile response -- Python's
``xml.etree`` is documented as vulnerable to entity-expansion ("billion
laughs") attacks, and a cap also bounds a compressed-response bomb.
"""

from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT = 10
MAX_RESPONSE_BYTES = 4 * 1024 * 1024  # these APIs return far less than this
SUMMARY_LENGTH = 280
USER_AGENT = "CareCheck/2.0 (educational symptom-triage prototype)"

#: Retry only idempotent reads, and only on transient server-side failures.
_RETRY = Retry(
    total=2,
    backoff_factor=0.5,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET"]),
    raise_on_status=False,
)

_session: Optional[requests.Session] = None


def get_session() -> requests.Session:
    """A process-wide session with connection pooling and bounded retries."""
    global _session
    if _session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        session.mount("https://", HTTPAdapter(max_retries=_RETRY))
        _session = session
    return _session


class ResponseTooLarge(Exception):
    """The endpoint returned more data than CareCheck is willing to parse."""


@dataclass(frozen=True)
class Payload:
    """A fully-read, size-capped response body."""

    status: int
    body: bytes
    encoding: Optional[str] = None

    @property
    def text(self) -> str:
        return self.body.decode(self.encoding or "utf-8", errors="replace")

    def json(self) -> Any:
        """Parse the body as JSON. Raises ``ValueError`` on malformed input."""
        return json.loads(self.text or "null")


def _read_capped(response: requests.Response) -> bytes:
    """Read a response body, refusing anything over ``MAX_RESPONSE_BYTES``."""
    chunks, total = [], 0
    for chunk in response.iter_content(chunk_size=65536):
        total += len(chunk)
        if total > MAX_RESPONSE_BYTES:
            raise ResponseTooLarge(f"response exceeded {MAX_RESPONSE_BYTES} bytes")
        chunks.append(chunk)
    return b"".join(chunks)


def _fetch(url: str, params: dict, *, allow_404: bool = False) -> Payload:
    """GET with a timeout, bounded retries and a size cap.

    Raises ``requests.RequestException`` on transport or HTTP failure and
    ``ResponseTooLarge`` if the body exceeds the cap.
    """
    with get_session().get(url, params=params, timeout=TIMEOUT, stream=True) as response:
        if allow_404 and response.status_code == 404:
            return Payload(404, b"", response.encoding)
        response.raise_for_status()
        return Payload(response.status_code, _read_capped(response), response.encoding)


# --- RxNorm -----------------------------------------------------------------

def normalize_medicine_rxnorm(medicine_name: str) -> dict[str, Any]:
    """Map a typed medicine name onto standard RxNorm concepts."""
    query = (medicine_name or "").strip()
    if not query:
        return {"error": "Enter a medicine name first."}

    try:
        data = _fetch("https://rxnav.nlm.nih.gov/REST/drugs.json", {"name": query}).json() or {}
    except ResponseTooLarge:
        return {"error": "RxNorm returned an unexpectedly large response."}
    except requests.RequestException as exc:
        return {"error": f"RxNorm request failed: {exc}"}
    except ValueError:
        return {"error": "RxNorm returned invalid JSON."}

    groups = (data.get("drugGroup") or {}).get("conceptGroup") or []
    matches = [
        {
            "rxcui": concept.get("rxcui"),
            "name": concept.get("name"),
            "synonym": concept.get("synonym"),
            "tty": concept.get("tty"),
        }
        for group in groups
        for concept in (group.get("conceptProperties") or [])
    ]
    return {"query": query, "matches": matches[:20]}


# --- MedlinePlus ------------------------------------------------------------

def _strip_html(text: str) -> str:
    """Summaries arrive as escaped HTML with <span class="qt0"> highlights."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text or ""))).strip()


def parse_medlineplus_xml(xml_text: str) -> list[dict[str, str]]:
    """Extract (title, url, summary) triples from a MedlinePlus search result."""
    results = []
    for doc in ET.fromstring(xml_text).iter("document"):
        fields: dict[str, str] = {}
        for content in doc.findall("content"):
            fields.setdefault(content.get("name"), _strip_html(content.text))
        title, url_value = fields.get("title"), doc.get("url")
        if title and url_value:
            summary = fields.get("FullSummary") or fields.get("snippet") or ""
            if len(summary) > SUMMARY_LENGTH:
                summary = summary[:SUMMARY_LENGTH].rsplit(" ", 1)[0] + "…"
            results.append({"title": title, "url": url_value, "summary": summary})
    return results


def search_medlineplus(topic: str) -> dict[str, Any]:
    """Search MedlinePlus consumer health topics."""
    query = (topic or "").strip()
    if not query:
        return {"error": "Enter a health topic first."}

    try:
        response = _fetch(
            "https://wsearch.nlm.nih.gov/ws/query",
            {"db": "healthTopics", "term": query, "retmax": 10, "rettype": "brief"},
        )
        return {"query": query, "results": parse_medlineplus_xml(response.text)}
    except ResponseTooLarge:
        return {"error": "MedlinePlus returned an unexpectedly large response."}
    except requests.RequestException as exc:
        return {"error": f"MedlinePlus request failed: {exc}"}
    except ET.ParseError:
        return {"error": "MedlinePlus returned an unreadable response."}


# --- openFDA drug labels ----------------------------------------------------

#: openFDA search is Lucene-flavoured; these characters would change the query
#: or break the quoted phrase, so they are dropped rather than escaped.
_LUCENE_SPECIAL = re.compile(r'[\\"+\-!(){}\[\]^~*?:/]|&&|\|\|')

_LABEL_FIELDS = ("purpose", "indications_and_usage", "warnings", "contraindications")


def _clean_lucene_term(term: str) -> str:
    """Strip characters that carry meaning inside an openFDA search phrase."""
    return re.sub(r"\s+", " ", _LUCENE_SPECIAL.sub(" ", term)).strip()


def _first(values: Any, fallback: str = "Not listed") -> str:
    """openFDA returns most label fields as single-element lists."""
    if isinstance(values, list) and values:
        return str(values[0])
    return fallback


def search_openfda_medicine(medicine_name: str) -> dict[str, Any]:
    """Search FDA drug labels for a medicine's labelled uses and warnings.

    An educational label lookup, not a prescribing engine: results depend
    entirely on what manufacturers submitted, and label text never establishes
    that a medicine is suitable for a particular person.
    """
    query = (medicine_name or "").strip()
    if not query:
        return {"error": "Enter a medicine name first."}

    term = _clean_lucene_term(query)
    if not term:
        return {"error": "Enter a medicine name using letters or numbers."}

    records: list[dict] = []
    failed = False
    for field in ("generic_name", "brand_name", "substance_name"):
        try:
            payload = _fetch(
                "https://api.fda.gov/drug/label.json",
                {"search": f'openfda.{field}:"{term}"', "limit": 5},
                allow_404=True,  # openFDA uses 404 for "no matches"
            )
            if payload.status == 404:
                continue
            records.extend((payload.json() or {}).get("results") or [])
            if records:
                break
        except ResponseTooLarge:
            failed = True
        except (requests.RequestException, ValueError):
            failed = True

    if not records:
        if failed:
            return {"error": "FDA label lookup failed. Try again, or use RxNorm or MedlinePlus."}
        return {"query": query, "matches": []}

    matches, seen = [], set()
    for item in records:
        openfda = item.get("openfda") or {}
        key = (_first(openfda.get("generic_name"), ""),
               _first(openfda.get("brand_name"), ""),
               item.get("set_id") or "")
        if key in seen:
            continue
        seen.add(key)
        matches.append({
            "brand_name": _first(openfda.get("brand_name")),
            "generic_name": _first(openfda.get("generic_name")),
            "manufacturer": _first(openfda.get("manufacturer_name")),
            "set_id": item.get("set_id"),
            **{field: _first(item.get(field)) for field in _LABEL_FIELDS},
        })
    return {"query": query, "matches": matches[:5]}
