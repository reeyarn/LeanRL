Here is the documentation for the **LeanRL**  Python package.

`import leanrl`

---

# LeanRL Package Documentation

**Version:** 0.1.5
**Description:** A lightweight, memory-efficient Python library for accessing SEC EDGAR filings and extracting information from XBRL filings and taxonomies.

---

## Module Overview

**LeanRL** provides five main modules:

1. **`core`** - Base infrastructure, namespace management, and XML streaming utilities
2. **`linkbases`** - Parsers for XBRL linkbases (Label, Reference, Definition, Presentation, Calculation)
3. **`taxonomy`** - Tools for parsing XSD schemas and aggregating taxonomy data
4. **`edgar`** - Tools for accessing and processing SEC EDGAR filings (NEW in v0.1.5)
5. **`utils`** - Utility functions for href parsing and concept name handling

---

## 1. Core Module (`core`)

This module provides the base infrastructure, namespace management, and memory-efficient XML streaming capabilities.

### File: `core/namespaces.py`

#### Class: `Namespace`
A dataclass representing an XML namespace.
*   **Attributes:**
    *   `prefix` (str): The common prefix (e.g., 'us-gaap').
    *   `uri` (str): The full namespace URI.
    *   `tag` (property, str): The ElementTree formatted namespace (e.g., `{http://...}`).

#### Class: `Namespaces`
A collection of constant `Namespace` objects.
*   **Class Constants (Type: `Namespace`):**
    *   `LINK`: XBRL Linkbase namespace.
    *   `XLINK`: XLink namespace.
    *   `XBRLI`: XBRL Instance namespace.
    *   `XBRLDI`: XBRL Dimensions namespace.
    *   `XBRLDT`: XBRL Dimensions namespace (Typed).
    *   `XS`, `XSD`: XML Schema namespaces.
    *   `XSI`: XML Schema Instance namespace.
    *   `US_GAAP`, `DEI`, `SRT`: US GAAP and SEC namespaces.
    *   `IFRS`: IFRS namespace.
    *   `ISO4217`, `XML`: Generic namespaces.
*   **Class Methods:**
    *   `as_dict() -> dict[str, str]`: Returns a dictionary mapping prefixes to URIs.
    *   `from_prefix(prefix: str) -> Namespace | None`: Looks up a namespace object by its string prefix.

#### Function: `qname`
Constructs a qualified name for ElementTree tag/attribute matching.
*   **Input:**
    *   `prefix` (str): Namespace prefix (e.g., 'link').
    *   `local_name` (str): Local element name (e.g., 'loc').
*   **Output:** `str` (Format: `{uri}local_name`).

#### Class: `Roles`
Standard XBRL role URI constants.
*   **Constants (Type: `str`):** `LABEL`, `TERSE_LABEL`, `VERBOSE_LABEL`, `DOCUMENTATION`, `PERIOD_START_LABEL`, `PERIOD_END_LABEL`, `TOTAL_LABEL`, `NEGATED_LABEL`, `REFERENCE`, `DEFINITION_REF`, `DISCLOSURE_REF`, `LINK`, `PRESENTATION_LINK`, `CALCULATION_LINK`, `DEFINITION_LINK`, `LABEL_LINK`, `REFERENCE_LINK`.

#### Class: `ArcRoles`
Standard XBRL arc role URI constants.
*   **Constants (Type: `str`):** `PARENT_CHILD`, `SUMMATION_ITEM`, `HYPERCUBE_DIMENSION`, `DIMENSION_DOMAIN`, `DOMAIN_MEMBER`, `ALL`, `NOT_ALL`, `CONCEPT_LABEL`, `CONCEPT_REFERENCE`, `FACT_FOOTNOTE`, `GENERAL_SPECIAL`, `ESSENCE_ALIAS`, `SIMILAR_TUPLES`, `REQUIRES_ELEMENT`.

#### File Level Constants
Shortcuts for `Namespaces.X.tag`.
*   **Constants (Type: `str`):** `NS_LINK`, `NS_XLINK`, `NS_XBRLI`, `NS_XBRLDI`, `NS_XBRLDT`, `NS_XS`, `NS_XSD`, `NS_XSI`, `NS_US_GAAP`, `NS_DEI`, `NS_SRT`, `NS_IFRS`, `NS_ISO4217`, `NS_XML`.

---

### File: `core/streaming.py`

#### Function: `stream_xml`
Streams XML elements with automatic memory cleanup using `iterparse`.
*   **Input:**
    *   `xml_file` (str | Path): Path to the XML file.
    *   `tags_of_interest` (Set[str] | None, default=None): Specific qualified tags to yield.
*   **Output:** `Iterator[tuple[str, ET.Element]]` (Yields tag name and Element object).

#### Function: `stream_xml_with_ancestors`
Streams XML elements while tracking the ancestor path.
*   **Input:**
    *   `xml_file` (str | Path): Path to the XML file.
    *   `tags_of_interest` (Set[str] | None, default=None): Specific qualified tags to yield.
*   **Output:** `Iterator[tuple[str, ET.Element, list[ET.Element]]]` (Yields tag, element, and list of ancestor elements).

---

## 2. Linkbases Module (`linkbases`)

Parsers for Label, Reference, Definition, Presentation, and Calculation linkbases.

### File: `linkbases/hierarchy.py`
Shared data structures for hierarchical linkbases.

#### Class: `ConceptNode`
A node in a hierarchy tree.
*   **Attributes:**
    *   `concept` (str): Concept name.
    *   `parent` (str | None): Parent concept name.
    *   `children` (List[str]): List of child concept names.
    *   `order` (float): Sort order.
    *   `depth` (int): Tree depth.

#### Class: `ConceptTree`
A tree structure representing concept hierarchies (Definition/Presentation).
*   **Methods:**
    *   `get(concept: str) -> ConceptNode | None`: Get node object.
    *   `get_parent(concept: str) -> str | None`: Get parent name.
    *   `get_children(concept: str) -> List[str]`: Get sorted child names.
    *   `get_ancestors(concept: str) -> List[str] | None`: Get list of ancestors (parent to root).
    *   `get_ancestor_path(concept: str) -> List[str] | None`: Get list of ancestors (root to concept).
    *   `get_descendants(concept: str, max_depth: int | None) -> List[str] | None`: Get all descendant names.
    *   `get_siblings(concept: str) -> List[str] | None`: Get sibling names.
    *   `find_common_ancestor(concept1: str, concept2: str) -> str | None`: Find the lowest common ancestor of two concepts.
    *   `to_dict() -> Dict[str, Any]`: Convert tree to nested dictionary.
    *   `print_tree(root: str | None, indent: str) -> str`: String representation.

#### Function: `get_hierarchy_dataframe`
*   **Input:** `tree` (ConceptTree).
*   **Output:** `pd.DataFrame` (Columns: concept, parent, depth, order, path).

---

### File: `linkbases/label.py`

#### Function: `parse_label_linkbase`
Extracts labels for a specific role.
*   **Input:**
    *   `xml_file` (str): Path to file.
    *   `role` (str, default=Roles.DOCUMENTATION): Label role URI.
*   **Output:** `Dict[str, str]` (Map: concept -> label text).

#### Function: `parse_all_labels`
Extracts all label types.
*   **Input:** `xml_file` (str).
*   **Output:** `Dict[str, Dict[str, str]]` (Map: concept -> {role -> text}).

---

### File: `linkbases/reference.py`

#### Class: `Reference`
Represents an authoritative literature reference.
*   **Attributes:** `role` (str), `parts` (Dict[str, str]).
*   **Methods:**
    *   `to_dict() -> Dict[str, Any]`: Dictionary representation.
    *   `format_citation() -> str`: Human-readable string (e.g., "FASB ASC...").

#### Function: `parse_reference_linkbase`
*   **Input:**
    *   `xml_file` (str).
    *   `role` (str | None, default=None).
*   **Output:** `Dict[str, List[Reference]]` (Map: concept -> list of Reference objects).

#### Function: `parse_reference_linkbase_flat`
*   **Input:** Same as `parse_reference_linkbase`.
*   **Output:** `Dict[str, List[Dict[str, str]]]` (Returns dicts instead of objects).

---

### File: `linkbases/calculation.py`

#### Class: `CalculationRelationship` (Dataclass)
*   **Attributes:** `parent` (str), `child` (str), `weight` (float), `order` (float).

#### Class: `CalculationNode` (Dataclass)
*   **Attributes:** `concept` (str), `parent` (str | None), `weight` (float), `children` (List[tuple[str, float]]), `order` (float).

#### Class: `CalculationTree`
*   **Methods:**
    *   `get_components(concept: str) -> Dict[str, float] | None`: Returns {child: weight}.
    *   `get_formula(concept: str) -> str | None`: Human-readable formula string.
    *   `validate_calculation(concept: str, values: Dict[str, float]) -> tuple[bool, float, float] | None`: Validates math (is_valid, expected, actual).

#### Function: `parse_calculation_linkbase`
*   **Input:** `xml_file` (str).
*   **Output:** `CalculationTree`.

#### Function: `get_calculation_dataframe`
*   **Input:** `tree` (CalculationTree).
*   **Output:** `pd.DataFrame` (Columns: parent, child, weight, order).

---

### File: `linkbases/definition.py` & `linkbases/presentation.py`

#### Function: `parse_definition_linkbase`
*   **Input:**
    *   `xml_file` (str).
    *   `arcrole` (str | None, default=ArcRoles.DOMAIN_MEMBER).
*   **Output:** `ConceptTree`.

#### Function: `parse_presentation_linkbase`
*   **Input:** `xml_file` (str).
*   **Output:** `ConceptTree` (Uses `PARENT_CHILD` arcrole).

---

## 3. Taxonomy Module (`taxonomy`)

Tools for parsing XSD schemas and aggregating taxonomy data.

### File: `taxonomy/schema.py`

#### Class: `ConceptSchema` (Dataclass)
Metadata for a concept.
*   **Attributes:** `name`, `id`, `type`, `period_type`, `balance`, `abstract`, `substitution_group`, `nillable`.
*   **Properties:** `is_monetary`, `is_instant`, `is_duration`, `is_debit`, `is_credit`, `short_name`.

#### Function: `parse_schema`
*   **Input:**
    *   `schema_path` (str).
    *   `prefix` (str, default='us-gaap').
    *   `filter_monetary`, `filter_instant`, `filter_duration`, `include_abstract` (bools).
*   **Output:** `List[ConceptSchema]`.

#### Function: `parse_schema_to_dict`
*   **Input:** Same as `parse_schema`.
*   **Output:** `Dict[str, ConceptSchema]`.

#### Function: `get_concept_types`
*   **Input:** `schema_path` (str).
*   **Output:** `Dict[str, Set[str]]` (Summary of types used in schema).

#### Function: `get_schema_dataframe`
*   **Input:** Same as `parse_schema`.
*   **Output:** `pd.DataFrame`.

#### Function: `extract_concepts_from_schema`
*   **Input:** Same as `parse_schema`.
*   **Output:** `List[str]` (List of concept names only).

---

### File: `taxonomy/constants.py`

#### File Level Constants
*   `statement_full_names` (Dict[str, str]): Maps abbreviations (e.g., 'soi', 'sfp') to full statement names.
*   `disclosure_full_names` (Dict[str, str]): Maps abbreviations to full disclosure names.

---

### File: `taxonomy/helper.py`

#### Class: `StatementInfo` (Dataclass)
*   **Attributes:** `statement_type` (str), `path` (List[str]), `depth` (int).

#### Function: `find_file_by_pattern`
*   **Input:** `directory` (Path), `pattern` (str).
*   **Output:** `Optional[Path]`.

#### Function: `build_stm_dis_trees`
Scans directories to build trees for statements/disclosures.
*   **Input:**
    *   `base_path` (str).
    *   `tree_type` (str, default='def').
    *   `debug` (bool, default=False).
*   **Output:** `Dict[str, ConceptTree]`.

#### Function: `find_concept_stm_dis`
Locates which statement a concept belongs to.
*   **Input:**
    *   `concept` (str).
    *   `trees` (Dict[str, ConceptTree]).
*   **Output:** `Optional[StatementInfo]`.

#### Function: `build_taxonomy_dataframe`
Builds a master DataFrame of the taxonomy.
*   **Input:**
    *   `base_path` (str).
    *   `output_file` (str | None, default=None).
    *   `debug` (bool, default=False).
*   **Output:** `pd.DataFrame` (Contains labels, refs, schema data, calculation paths).

#### Function: `build_taxonomy_dataframe_from_zip`
Wrapper to process a zipped taxonomy file.
*   **Input:** `zip_file` (str).
*   **Output:** `pd.DataFrame`.

---

## 4. EDGAR Module (`edgar`)

This module provides tools for accessing, downloading, and processing SEC EDGAR filings.

**Important Notes:**
- The module automatically caches downloaded filings to reduce network requests.
- XSD schema files are processed with strict XML formatting preservation to ensure valid parsing.
- Supports both file path and file-like object inputs for maximum flexibility (e.g., memory filesystems).

### File: `edgar/edgar.py`

#### Class: `EG_LOCAL`
Local EDGAR cache manager.
*   **Attributes:**
    *   `edgar_root_dir` (str): Root directory for EDGAR cache (default: '/mnt/text/edgar' or from env var `EDGAR_ROOT_DIR`).
    *   `symbols_data_path` (str): Path to symbols CSV file.
    *   `cache_dir_str` (str): Cache directory for downloaded filings.

#### Class: `FilingInfo` (Dataclass)
Information about a specific filing.
*   **Attributes:** `form_type`, `company_name`, `cik`, `date_filed`, `file_name`.

#### Function: `get_index_json`
Retrieves the index.json for a specific quarter.
*   **Input:** `year` (int), `quarter` (int).
*   **Output:** `dict` (Index data).

#### Function: `get_latest_quarter_dir`
*   **Output:** `tuple[int, int]` (year, quarter).

#### Function: `find_latest_filing_info_going_back_from`
Finds the latest filing of a specific form type.
*   **Input:** `cik` (str), `form_type` (str), `start_year` (int), `start_quarter` (int), `egl` (EG_LOCAL).
*   **Output:** `FilingInfo | None`.

#### Function: `get_filing_info`
Gets filing information for a specific period.
*   **Input:** `cik` (str), `year` (int), `quarter` (int), `form_type` (str), `egl` (EG_LOCAL).
*   **Output:** `FilingInfo | None`.

#### Function: `get_financial_filing_info`
Gets financial filing (10-K/10-Q) information.
*   **Input:** `cik` (str), `period` (str, 'annual' or 'quarterly'), `year` (int), `egl` (EG_LOCAL).
*   **Output:** `FilingInfo | None`.

---

### File: `edgar/stock.py`

#### Class: `Stock`
Represents a publicly traded company with access to its SEC filings.
*   **Constructor:**
    *   `Stock(symbol_or_cik=None, *, symbol=None, cik=None, egl=EG_LOCAL())`.
    *   Can initialize with ticker symbol ('AAPL') or CIK ('320193').
*   **Attributes:**
    *   `symbol` (str): Stock ticker symbol.
    *   `cik` (str): Central Index Key.
    *   `company_name` (str): Company name.
    *   `egl` (EG_LOCAL): EDGAR local cache manager.
*   **Methods:**
    *   `get_filing(period: str, year: int) -> Filing | None`: Get Filing object for specified period and year.
    *   `get_all_filings(form_type: str) -> List[FilingInfo]`: Get all filings of a specific type.

#### Function: `update_symbols_data`
Downloads fresh company tickers data from SEC.
*   **Input:** `egl` (EG_LOCAL, default=EG_LOCAL()).
*   **Output:** None (updates symbols CSV file).

#### Function: `should_update_symbols_file`
Checks if symbols file needs updating.
*   **Input:** `days` (int, default=28), `egl` (EG_LOCAL).
*   **Output:** `bool`.

---

### File: `edgar/filing.py`

#### Class: `Statements`
Container for statement type constants.
*   **Constants:** `INCOME`, `BALANCE_SHEET`, `CASH_FLOW`, `STOCKHOLDERS_EQUITY`, `COMPREHENSIVE_INCOME`, `PARENTHETICAL`.

#### Class: `Filing`
Represents an SEC filing with document access and caching.
*   **Constructor:** `Filing(url: str, company: str | None, egl: EG_LOCAL)`.
*   **Attributes:**
    *   `url` (str): URL of the filing.
    *   `company` (str | None): Company name.
    *   `documents` (dict): Dictionary of Document objects keyed by filename.
    *   `xbrl_files` (dict): Dictionary mapping XBRL file types to filenames.
    *   `date_filed` (datetime): Filing date.
    *   `cik` (str): Company CIK.
    *   `tfnm` (str): Filing accession number.
*   **Methods:**
    *   `get_xbrl_files() -> dict`: Returns dictionary of XBRL file types and filenames.

---

### File: `edgar/document.py`

#### Class: `Document`
Represents a single document within a filing.
*   **Attributes:**
    *   `type` (str): Document type (e.g., '10-K', 'EX-101.SCH').
    *   `sequence` (str): Document sequence number.
    *   `filename` (str): Document filename.
    *   `description` (str | None): Document description.
    *   `doc_text` (DocumentText): Document text content.

---

### File: `edgar/document_text.py`

#### Class: `DocumentText`
Represents the text content of a document with parsed XML/XBRL attributes.
*   **Attributes:**
    *   `data` (str | dict): Raw document data.
    *   `xml` (BeautifulSoup | None): Parsed XML content (if applicable).
    *   `xbrl` (BeautifulSoup | None): Parsed XBRL content (if applicable).
*   **Note:** When converting to string for file operations, newlines are replaced with spaces to preserve XML attribute spacing.

#### Function: `clean_doc`
Cleans XBRL tags from document text.
*   **Input:** `text` (str | dict).
*   **Output:** `str`.

---

### File: `edgar/loader.py`

#### Function: `get_edgar_local_path`
Gets the configured EDGAR local path.
*   **Output:** `str` (Default: '/mnt/text/edgar').

#### Function: `load_xbrl_filing`
Loads an XBRL filing into memory with parsed instance and taxonomy.
*   **Input:**
    *   `ticker` (str | None): Stock ticker (optional).
    *   `year` (int | None): Filing year (optional).
    *   `filing_url` (str | None): Direct filing URL (optional).
    *   `edgar_local_path` (str): Local EDGAR cache path.
    *   `memory_threshold_gb` (int, default=16): Memory threshold.
    *   `return_data_pool` (bool, default=False): Whether to return data pool.
*   **Output:** `tuple[Instance | None, Taxonomy | None]` or `tuple[Instance | None, Taxonomy | None, Pool | None]`.

#### Function: `get_xbrl_df_by_ticker_year`
Gets XBRL data as DataFrame for a specific ticker and year.
*   **Input:**
    *   `ticker` (str): Stock ticker.
    *   `year` (int): Filing year.
    *   `force_reload` (bool, default=False): Force reload from source.
    *   `memory_threshold_gb` (int, default=16).
    *   `edgar_local_path` (str).
*   **Output:** `pd.DataFrame | None`.

---

### File: `edgar/edgar_helper.py`

#### Function: `extract_filing_to_memfs`
Extracts XBRL files from a Filing instance to an in-memory filesystem.
*   **Input:**
    *   `filing` (Filing): Filing object.
    *   `mem_fs` (FS): PyFilesystem2 memory filesystem object.
*   **Output:** `dict` (Map of file types to filenames: {'xsd': filename, 'pre': filename, 'lab': filename, ...}).
*   **Note:** Preserves strict XML formatting for XSD schema files to ensure valid parsing.

---

### File: `edgar/dtd.py`

#### Class: `DTD`
Document Type Definition for EDGAR SGML documents.
*   Contains tag definitions for parsing SEC SGML filings.

---

### File: `edgar/sgml.py`

#### Class: `Sgml`
SGML parser for SEC filings.
*   **Constructor:** `Sgml(text: str, dtd: DTD)`.
*   **Attributes:**
    *   `map` (dict): Parsed SGML structure.

#### Class: `SgmlException`
Exception raised during SGML parsing.

---

### File: `edgar/requests_wrapper.py`

#### Class: `GetRequest`
Wrapper for HTTP GET requests with retry logic.

#### Class: `RequestException`
Exception raised for request errors.

---

### File: `edgar/financials.py`

#### Class: `FinancialElement`
Represents a single financial statement element.

#### Class: `FinancialInfo`
Financial information for a reporting period.

#### Class: `FinancialReport`
Complete financial report with multiple periods.

#### Class: `FinancialReportEncoder`
JSON encoder for FinancialReport objects.

#### Function: `get_financial_report`
Extracts financial report from HTML text.
*   **Input:** `company` (str), `date_filed` (datetime), `financial_html_text` (str).
*   **Output:** `FinancialReport`.

---

## 5. Utils Module (`utils`)

### File: `utils/href.py`

#### Function: `extract_concept_from_href`
*   **Input:** `href` (str).
*   **Output:** `str` (Concept name extracted from anchor, e.g., 'us-gaap_Assets').

#### Function: `parse_href`
*   **Input:** `href` (str).
*   **Output:** `tuple[str, str]` (file_path, fragment).

#### Function: `parse_concept_name`
*   **Input:** `concept` (str).
*   **Output:** `tuple[str, str]` (prefix, local_name).

#### Function: `normalize_concept_name`
*   **Input:** `concept` (str).
*   **Output:** `str` (Normalized with underscore separator).

#### Function: `is_valid_concept_name`
*   **Input:** `concept` (str).
*   **Output:** `bool`.
*   


## Usage Examples

### Example 1: Accessing SEC Filings

```python
from leanrl import Stock, Filing, EG_LOCAL, extract_filing_to_memfs
import fs

# Initialize EDGAR local cache
egl = EG_LOCAL(edgar_root_dir='/mnt/text/edgar/')

# Method 1: Using Stock class with ticker
stock = Stock('AAPL', egl=egl)
filing = stock.get_filing(period='annual', year=2023)

if filing:
    print(f"Filing URL: {filing.url}")
    print(f"Date filed: {filing.date_filed}")
    print(f"XBRL files: {filing.xbrl_files}")
    
    # Access specific documents
    for filename, doc in filing.documents.items():
        print(f"  {filename}: {doc.type}")

# Method 2: Direct filing URL
filing_url = "https://www.sec.gov/Archives/edgar/data/320193/0000320193-23-000106.txt"
filing = Filing(url=filing_url, egl=egl)

# Method 3: Extract filing to memory filesystem
memfs = fs.open_fs('mem://')
files_map = extract_filing_to_memfs(filing, memfs)

# Parse schema from memory filesystem
from leanrl.taxonomy import parse_schema

with memfs.open(files_map['xsd'], 'rb') as f_xsd:
    schema = parse_schema(f_xsd)
    print(f"Parsed {len(schema)} concepts from schema")
```

### Example 2: Loading XBRL Data

```python
from leanrl import load_xbrl_filing, get_xbrl_df_by_ticker_year

# Load XBRL filing (returns Instance and Taxonomy objects)
xid, tax = load_xbrl_filing(ticker='AAPL', year=2023)

if xid and tax:
    print(f"Loaded {len(xid.facts)} facts")
    print(f"Taxonomy has {len(tax.concepts)} concepts")

# Get XBRL data as DataFrame
df = get_xbrl_df_by_ticker_year('AAPL', 2023)
if df is not None:
    print(df.head())
```

### Example 3: US-GAAP Taxonomy Analysis

```python

"""
US-GAAP Taxonomy Analysis Script (using helper functions)

This script processes the US-GAAP 2020 taxonomy files and creates a comprehensive
DataFrame with information about each concept including:
- Labels and documentation
- Statement classification (sfp, soi, scf, notes)
- Hierarchy path within each statement

This version uses the helper functions from leanrl.taxonomy.helper instead of
defining them locally.
"""

import sys
from pathlib import Path
# Add src to path if running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from leanrl import build_taxonomy_dataframe


if __name__ == '__main__':
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze US-GAAP taxonomy and build concept DataFrame'
    )
    parser.add_argument(
        'taxonomy_path',
        help='Path to US-GAAP taxonomy folder (e.g., ./us-gaap-2020-01-31)',
        default="",
    )
    parser.add_argument(
        '-o', '--output',
        default='us_gaap_taxonomy.csv',
        help='Output CSV filename (default: us_gaap_taxonomy.csv)'
    )
    try:
        args = parser.parse_args()
        base_path = str(Path(args.taxonomy_path))
        output_path = str(Path(args.output))

    except Exception as e:
        print(f"Error: {e}")
        print("No taxonomy path provided. Using default path...")
        
        base_path = "/tmp/us-gaap-2020-01-31/"
        output_path = '/tmp/us_gaap-2020-01-31-taxonomy.csv'

    # Use the helper function from taxonomy.helper
    df = build_taxonomy_dataframe(base_path, output_path)
    
    # Show some examples
    print("\n" + "=" * 60)
    print("Sample Records")
    print("=" * 60)
    
    # Show R&D expense
    rd = df[df['concept'] == 'us-gaap_ResearchAndDevelopmentExpense']
    if not rd.empty:
        print("\nResearchAndDevelopmentExpense:")
        row = rd.iloc[0]
        print(f"  Label: {row['label']}")
        print(f"  Type: {row['data_type']} | monetary={row['is_monetary']} | period={row['period_type']} | balance={row['balance']}")
        print(f"  Statements: {row['all_statements']}")
        print(f"  Path: {row['path'][:100]}..." if len(str(row['path'])) > 100 else f"  Path: {row['path']}")
    
    # Show Assets
    assets = df[df['concept'] == 'us-gaap_Assets']
    if not assets.empty:
        print("\nAssets:")
        row = assets.iloc[0]
        print(f"  Label: {row['label']}")
        print(f"  Type: {row['data_type']} | monetary={row['is_monetary']} | period={row['period_type']} | balance={row['balance']}")
        print(f"  Statements: {row['all_statements']}")
        print(f"  Path: {row['path'][:100]}..." if len(str(row['path'])) > 100 else f"  Path: {row['path']}")
```
