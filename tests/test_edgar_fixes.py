"""
Regression tests for the three LeanRL fixes surfaced by the MDIS face-note
panel build (md_private/handoff-20260702-mdis-face-note-findings.md):

1. extract_filing_to_memfs must classify the instance document by content
   (contextRef / xbrli:context), not filename suffix.
2. Filing date parsing must not crash on malformed SGML headers.
3. Filing must support strict_local=True (no silent HTTP fallback) and
   GetRequest must retry with backoff on 429/503.

Run with:  pytest tests/test_edgar_fixes.py
"""
import gzip
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Allow running from the repo root without an installed package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from leanrl.edgar.edgar_helper import extract_filing_to_memfs  # noqa: E402
from leanrl.edgar import filing as filing_module  # noqa: E402
from leanrl.edgar import requests_wrapper as rw  # noqa: E402
from leanrl.edgar.edgar import EG_LOCAL  # noqa: E402
from leanrl.edgar.filing import Filing  # noqa: E402


# ---------------------------------------------------------------------------
# Stubs and fixtures
# ---------------------------------------------------------------------------

class StubDocText:
    def __init__(self, data):
        self.data = data


class StubDoc:
    def __init__(self, data):
        self.doc_text = StubDocText(data)


class StubFiling:
    """Duck-typed stand-in for Filing: only .documents is used."""
    def __init__(self, named_contents):
        self.documents = {name: StubDoc(content) for name, content in named_contents}


class DictFS:
    """Duck-typed stand-in for a pyfilesystem2 memory FS."""
    def __init__(self):
        self.files = {}

    def writetext(self, name, content, encoding='utf-8'):
        self.files[name] = content


INSTANCE_XML = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance">'
    '<xbrli:context id="FY2009"><xbrli:entity>0001000697</xbrli:entity></xbrli:context>'
    '<us-gaap:Assets contextRef="FY2009" unitRef="usd" decimals="-3">1000</us-gaap:Assets>'
    '</xbrli:xbrl>'
)

# Early-era combined definition/reference linkbase (Waters FY2009 style).
# Deliberately contains no contextRef / xbrli:context.
DEFNREF_XML = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<DefinitionAndReference xmlns:link="http://www.xbrl.org/2003/linkbase">'
    '<link:definitionLink xlink:role="http://example.com/role">arcs</link:definitionLink>'
    '<link:referenceLink>refs</link:referenceLink>'
    '</DefinitionAndReference>'
)

DEF_LINKBASE_XML = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase">'
    '<link:definitionLink>arcs</link:definitionLink>'
    '</link:linkbase>'
)

SMALL_LINKBASE_XML = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase">x</link:linkbase>'
)

XSD_CONTENT = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">e</xs:schema>'
)


def make_sgml(acceptance_line):
    """Minimal EDGAR SGML filing with a configurable ACCEPTANCE-DATETIME line."""
    return (
        "<SEC-DOCUMENT>0000950123-10-017583.txt : 20100301\n"
        "<SEC-HEADER>0000950123-10-017583.hdr.sgml : 20100301\n"
        f"{acceptance_line}\n"
        "ACCESSION NUMBER:\t\t0000950123-10-017583\n"
        "CONFORMED SUBMISSION TYPE:\t10-K\n"
        "</SEC-HEADER>\n"
        "<DOCUMENT>\n"
        "<TYPE>10-K\n"
        "<SEQUENCE>1\n"
        "<FILENAME>a12345.htm\n"
        "<DESCRIPTION>FORM 10-K\n"
        "<TEXT>\n"
        "Sample text content without markup.\n"
        "</TEXT>\n"
        "</DOCUMENT>\n"
        "</SEC-DOCUMENT>\n"
    )


SGML_VALID = make_sgml("<ACCEPTANCE-DATETIME>20100226172326")
# Malformed header: empty ACCEPTANCE-DATETIME, so the SGML parser returns the
# following "ACCESSION NUMBER: ..." text as the element value ('ACCESSIO'[:8]).
SGML_MALFORMED = make_sgml("<ACCEPTANCE-DATETIME>")

FILING_URL = 'https://www.sec.gov/Archives/edgar/data/1000697/0000950123-10-017583.txt'


# ---------------------------------------------------------------------------
# 1. extract_filing_to_memfs: instance classification by content
# ---------------------------------------------------------------------------

def test_defnref_is_not_classified_as_instance():
    """Waters FY2009 case: defnref.xml must not win the 'xml' (instance) key."""
    filing = StubFiling([
        ('wat-20091231.xsd', XSD_CONTENT),
        ('wat-20091231_pre.xml', SMALL_LINKBASE_XML),
        ('wat-20091231_lab.xml', SMALL_LINKBASE_XML),
        ('wat-20091231_cal.xml', SMALL_LINKBASE_XML),
        ('wat-20091231.xml', INSTANCE_XML),
        ('defnref.xml', DEFNREF_XML),  # comes after the instance -> old code overwrote 'xml'
    ])
    mem_fs = DictFS()

    files_map = extract_filing_to_memfs(filing, mem_fs)

    assert files_map['xml'] == 'wat-20091231.xml'
    assert 'contextRef' in mem_fs.files[files_map['xml']]
    # defnref is a combined definition+reference linkbase
    assert files_map.get('def') == 'defnref.xml'
    assert files_map.get('ref') == 'defnref.xml'


def test_def_suffix_does_not_overwrite_instance():
    """_def.xml appearing after the instance must land in 'def', not 'xml'."""
    filing = StubFiling([
        ('abc-20101231.xml', INSTANCE_XML),
        ('abc-20101231_def.xml', DEF_LINKBASE_XML),
    ])
    mem_fs = DictFS()

    files_map = extract_filing_to_memfs(filing, mem_fs)

    assert files_map['xml'] == 'abc-20101231.xml'
    assert files_map.get('def') == 'abc-20101231_def.xml'


def test_ref_suffix_classified_as_reference_linkbase():
    filing = StubFiling([
        ('abc-20101231.xml', INSTANCE_XML),
        ('abc-20101231_ref.xml', SMALL_LINKBASE_XML),
    ])
    mem_fs = DictFS()

    files_map = extract_filing_to_memfs(filing, mem_fs)

    assert files_map['xml'] == 'abc-20101231.xml'
    assert files_map.get('ref') == 'abc-20101231_ref.xml'


def test_largest_content_validated_instance_wins():
    big_instance = INSTANCE_XML.replace(
        '</xbrli:xbrl>',
        '<us-gaap:Liabilities contextRef="FY2009" unitRef="usd">500</us-gaap:Liabilities>' * 50
        + '</xbrli:xbrl>',
    )
    filing = StubFiling([
        ('big-20091231.xml', big_instance),
        ('small-20091231.xml', INSTANCE_XML),  # also instance-like, but smaller and later
    ])
    mem_fs = DictFS()

    files_map = extract_filing_to_memfs(filing, mem_fs)

    assert files_map['xml'] == 'big-20091231.xml'


def test_instance_with_ref_in_ticker_still_wins():
    """Content check must dominate the ref-ish filename heuristic (e.g. ticker REFR)."""
    filing = StubFiling([
        ('refr-20091231.xml', INSTANCE_XML),
    ])
    mem_fs = DictFS()

    files_map = extract_filing_to_memfs(filing, mem_fs)

    assert files_map['xml'] == 'refr-20091231.xml'


# ---------------------------------------------------------------------------
# 2. Filing date parsing on malformed SGML headers
# ---------------------------------------------------------------------------

def test_parse_acceptance_datetime_valid():
    parse = filing_module.parse_acceptance_datetime
    assert parse('20100226172326') == datetime(2010, 2, 26)


def test_parse_acceptance_datetime_malformed_returns_none():
    parse = filing_module.parse_acceptance_datetime
    # first 8 chars are 'ACCESSIO'; embedded digit runs are accession digits,
    # not dates
    assert parse('ACCESSION NUMBER:\t\t0000950123-10-017583') is None
    assert parse('') is None
    assert parse(None) is None


def test_process_text_survives_malformed_header():
    filing = object.__new__(Filing)
    filing.url = 'test://malformed-header'

    filing._process_text(SGML_MALFORMED)

    assert filing.date_filed is None
    assert 'a12345.htm' in filing.documents


def test_process_text_parses_valid_header():
    filing = object.__new__(Filing)
    filing.url = 'test://valid-header'

    filing._process_text(SGML_VALID)

    assert filing.date_filed == datetime(2010, 2, 26)
    assert 'a12345.htm' in filing.documents


# ---------------------------------------------------------------------------
# 3a. GetRequest: backoff + retry on 429/503
# ---------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, status_code, text='', headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self.encoding = None


def _install_fake_get(monkeypatch, responses):
    calls = []

    def fake_get(url, headers=None):
        calls.append(url)
        return responses[min(len(calls), len(responses)) - 1]

    sleeps = []
    monkeypatch.setattr(rw.requests, 'get', fake_get)
    monkeypatch.setattr(time, 'sleep', lambda s: sleeps.append(s))
    return calls, sleeps


def test_get_request_retries_on_503(monkeypatch):
    calls, sleeps = _install_fake_get(monkeypatch, [
        FakeResponse(503, 'slow down'),
        FakeResponse(503, 'slow down'),
        FakeResponse(200, 'ok'),
    ])

    req = rw.GetRequest('http://example.com/x')

    assert req.response.text == 'ok'
    assert len(calls) == 3
    assert len(sleeps) == 2


def test_get_request_gives_up_after_max_retries(monkeypatch):
    calls, _sleeps = _install_fake_get(monkeypatch, [FakeResponse(503, 'slow down')])

    with pytest.raises(rw.RequestException):
        rw.GetRequest('http://example.com/x', max_retries=2)

    assert len(calls) == 3  # initial attempt + 2 retries


def test_get_request_honors_retry_after(monkeypatch):
    calls, sleeps = _install_fake_get(monkeypatch, [
        FakeResponse(429, 'rate limited', headers={'Retry-After': '7'}),
        FakeResponse(200, 'ok'),
    ])

    req = rw.GetRequest('http://example.com/x')

    assert req.response.text == 'ok'
    assert sleeps and sleeps[0] >= 7


def test_get_request_still_raises_on_404(monkeypatch):
    calls, sleeps = _install_fake_get(monkeypatch, [FakeResponse(404, 'not found')])

    with pytest.raises(rw.RequestException):
        rw.GetRequest('http://example.com/x')

    assert len(calls) == 1  # no retry on non-throttling errors
    assert not sleeps


# ---------------------------------------------------------------------------
# 3b. Filing strict_local
# ---------------------------------------------------------------------------

def _forbid_network(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError('network access attempted during strict_local test')

    monkeypatch.setattr(filing_module, 'GetRequest', boom)


def _cache_path_for(egl, url):
    """Mirror Filing._get_cache_path layout for test setup."""
    import re
    cik, filename = re.search(r'/data/(\d+)/(\d+-\d+-\d+\.txt)$', url).groups()
    acc_num = filename.split('.')[0]
    return egl.cache_dir / '10k-bycik' / cik / acc_num / (filename + '.gz')


def test_strict_local_raises_on_cache_miss(tmp_path, monkeypatch):
    _forbid_network(monkeypatch)
    egl = EG_LOCAL(edgar_root_dir=str(tmp_path))

    with pytest.raises(FileNotFoundError, match='strict_local'):
        Filing(url=FILING_URL, egl=egl, strict_local=True)


def test_strict_local_loads_stale_cache_without_network(tmp_path, monkeypatch):
    """A cached filing older than CACHE_VALIDITY_DAYS must still be used
    in strict_local mode instead of silently re-fetching from sec.gov."""
    _forbid_network(monkeypatch)
    egl = EG_LOCAL(edgar_root_dir=str(tmp_path))

    cache_path = _cache_path_for(egl, FILING_URL)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(cache_path, 'wt', encoding='utf-8') as f:
        f.write(SGML_VALID)
    stale = (datetime.now() - timedelta(days=40)).timestamp()
    os.utime(cache_path, (stale, stale))

    filing = Filing(url=FILING_URL, egl=egl, strict_local=True)

    assert 'a12345.htm' in filing.documents
    assert filing.date_filed == datetime(2010, 2, 26)


def test_default_behavior_still_fetches(tmp_path, monkeypatch):
    """Without strict_local, a cache miss falls back to HTTP as before."""
    fetched = []

    class FakeGetRequest:
        def __init__(self, url, *args, **kwargs):
            fetched.append(url)
            self.response = FakeResponse(200, SGML_VALID)

    monkeypatch.setattr(filing_module, 'GetRequest', FakeGetRequest)
    egl = EG_LOCAL(edgar_root_dir=str(tmp_path))

    filing = Filing(url=FILING_URL, egl=egl)

    assert fetched == [FILING_URL]
    assert 'a12345.htm' in filing.documents
