# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LeanRL is a lightweight, memory-efficient Python library for extracting information from XBRL filings and taxonomies (US GAAP, IFRS, ESEF) **without loading the full DTS** (Discovery Tree Set). Design philosophy: process one XML file at a time via streaming, skip strict XBRL validation and heavyweight object models, and return plain Python structures (`dict`, `list`, `pandas.DataFrame`). Published on PyPI as `leanrl`.

## Commands

```bash
# Install for development
pip install -e .                    # or: uv pip install -e ".[dev]"

# Lint (config in pyproject.toml: line-length 100, rules E/F/I/UP)
ruff check src/

# Type check (strict mode, targets Python 3.9)
mypy src/leanrl

# Build distribution (hatchling backend)
hatch build
```

### Tests

`tests/test1.py` … `test5.py` are **runnable scripts, not pytest suites** — run one directly:

```bash
python tests/test3.py    # from repo root
```

Caveats:
- Several scripts expect a full US GAAP taxonomy extracted at `/tmp/us-gaap-2020-01-31/`; smaller sample files live in `tests/data/` (schema, label/ref linkbases, and `stm/` linkbases for soi, sfp-cls, scf).
- `test4.py`/`test5.py` (EDGAR) need network access to sec.gov and/or a local EDGAR cache.
- Paths inside the scripts are partly hard-coded relative to the repo root or `/tmp`.

## Architecture

Layered package under `src/leanrl/`; each layer only depends on layers above it:

1. **`core/`** — foundation used by all parsers.
   - `namespaces.py`: `Namespaces`, `qname()`, `Roles` (label/link role URIs), `ArcRoles` (arc role URIs), `NS_*` tag constants. All namespace handling goes through here.
   - `streaming.py`: `stream_xml()` / `stream_xml_with_ancestors()` — `iterparse`-based streaming with element cleanup. This is the memory-efficiency primitive every parser is built on.

2. **`linkbases/`** — one module per XBRL linkbase type: `label.py`, `reference.py`, `calculation.py`, `definition.py`, `presentation.py`. `hierarchy.py` holds the shared `ConceptNode`/`ConceptTree` structures that both `definition.py` and `presentation.py` build (they differ only in arcrole). `calculation.py` has its own `CalculationTree` carrying summation weights. See `linkbases/README.md` for per-parser usage.

3. **`taxonomy/`** — operates on a whole taxonomy directory (e.g. `us-gaap-2020-01-31/` with `elts/`, `stm/`, `dis/` subfolders).
   - `schema.py`: XSD parser producing `ConceptSchema` records (type, period, balance, abstract…).
   - `helper.py`: `build_taxonomy_dataframe()` — the flagship aggregator that scans all statement/disclosure linkbases plus schema/labels/references into one master DataFrame; `build_stm_dis_trees()`, `find_concept_stm_dis()` map concepts to statements.
   - `constants.py`: maps statement/disclosure abbreviations (`soi`, `sfp`, `scf`, `dis-*`…) to full names. `docs/soi.md`, `docs/scf.md`, `docs/elts.md` explain these taxonomy conventions.

4. **`edgar/`** — SEC EDGAR access and filing processing: `EG_LOCAL` (local cache manager), `Stock` → `Filing` → `Document`/`DocumentText` chain, `sgml.py`/`dtd.py` for SEC SGML parsing, `edgar_helper.py:extract_filing_to_memfs()` to unpack a filing's XBRL files into a pyfilesystem2 memory FS for parsing with the layers above.
   - Local cache root comes from the `EDGAR_ROOT_DIR` env var (default `/mnt/text/edgar`).
   - **Undeclared dependencies:** the edgar module imports `fs` (pyfilesystem2), `lxml`, and `bs4`, and `loader.py`/`xbrl_worker.py` depend on the external sibling package `openesef` — none of these are in `pyproject.toml` dependencies. Core/linkbases/taxonomy work without them.

5. **`utils/`** — `href.py` (extract concept names from xlink hrefs), `xml_utils.py`.

### Public API convention

Everything public is re-exported through `src/leanrl/__init__.py` (with `__all__`). A new public function must be exported in its subpackage `__init__.py` **and** added to the top-level `__init__.py` imports and `__all__`.

### Known inconsistencies

- Version is out of sync: `pyproject.toml` says 0.1.6, `leanrl/__init__.py:__version__` says 0.1.0. `pyproject.toml` is authoritative.
- `src/documentation.md` is the maintained API reference — update it when changing public signatures.
- `edgar/edgar_helper copy.py` and `edgar/edgar_test.py` are scratch/leftover files inside the package.

## Domain Notes

- XSD schema files must keep strict XML formatting when copied/extracted (attribute spacing matters for downstream parsing) — see `extract_filing_to_memfs` and `DocumentText` notes in `src/documentation.md`.
- Taxonomy file naming follows US GAAP conventions: `us-gaap-{doc|lab|ref}-YYYY-MM-DD.xml` in `elts/`, and `us-gaap-stm-{soi|sfp-cls|scf-indir|…}-{pre|def|cal}-YYYY-MM-DD.xml` in `stm/`.
- Redistribution of FASB/IFRS taxonomy files is subject to the license terms in README.md — preserve embedded copyright notices in any bundled taxonomy files.
