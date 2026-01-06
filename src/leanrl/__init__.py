"""
LeanRL - Lean (non-XML) approach to process XBRL

A lightweight, memory-efficient Python library for extracting
specific information from XBRL filings and taxonomies.
"""

__version__ = "0.1.0"

# Core: Namespaces and streaming
from .core.namespaces import (
    Namespaces,
    Roles,
    ArcRoles,
    qname,
    NS_LINK,
    NS_XLINK,
    NS_XBRLI,
)
from .core.streaming import stream_xml

# Linkbase parsers
from .linkbases import (
    # Label
    parse_label_linkbase,
    parse_all_labels,
    # Reference
    Reference,
    parse_reference_linkbase,
    parse_reference_linkbase_flat,
    # Definition / Presentation
    ConceptNode,
    ConceptTree,
    parse_definition_linkbase,
    parse_presentation_linkbase,
    get_hierarchy_dataframe,
    # Calculation
    CalculationRelationship,
    CalculationNode,
    CalculationTree,
    parse_calculation_linkbase,
    get_calculation_dataframe,
    # Helper
    get_specific_role_tree,
)

# Taxonomy schema parsers
from .taxonomy import (
    ConceptSchema,
    parse_schema,
    parse_schema_to_dict,
    get_concept_types,
    get_schema_dataframe,
    extract_concepts_from_schema,
    statement_full_names,
    disclosure_full_names,
    # Helper functions
    StatementInfo,
    find_file_by_pattern,
    build_stm_dis_trees,
    find_concept_stm_dis,
    build_taxonomy_dataframe,
    build_taxonomy_dataframe_from_zip,
)

# Utilities
from .utils import extract_concept_from_href

# EDGAR - SEC filing access and processing
from .edgar import (
    # Core EDGAR
    EG_LOCAL,
    FilingInfo,
    get_index_json,
    get_latest_quarter_dir,
    find_latest_filing_info_going_back_from,
    get_filing_info,
    get_financial_filing_info,
    InvalidInputException,
    # Stock
    Stock,
    update_symbols_data,
    should_update_symbols_file,
    NoFilingInfoException,
    # Filing
    Filing,
    Statements,
    # Document
    Document,
    DocumentText,
    clean_doc,
    # Data structures
    DTD,
    Sgml,
    SgmlException,
    # Financial
    FinancialReportEncoder,
    FinancialElement,
    FinancialInfo,
    FinancialReport,
    MetaDataParsingException,
    get_financial_report,
    # Loader
    get_edgar_local_path,
    get_xbrl_df_by_ticker_year,
    load_xbrl_filing,
    #get_fact_df,
    #get_xbrl_df,
    #run_xbrl_worker,
    # Versioned pickle
    #VersionedPickle,
    # Requests
    GetRequest,
    RequestException,
    # Helper
    extract_filing_to_memfs,
)

__all__ = [
    '__version__',
    # Core
    'Namespaces',
    'Roles',
    'ArcRoles',
    'qname',
    'NS_LINK',
    'NS_XLINK',
    'NS_XBRLI',
    'stream_xml',
    # Linkbases - Label
    'parse_label_linkbase',
    'parse_all_labels',
    # Linkbases - Reference
    'Reference',
    'parse_reference_linkbase',
    'parse_reference_linkbase_flat',
    # Linkbases - Definition/Presentation
    'ConceptNode',
    'ConceptTree',
    'parse_definition_linkbase',
    'parse_presentation_linkbase',
    'get_hierarchy_dataframe',
    # Linkbases - Calculation
    'CalculationRelationship',
    'CalculationNode',
    'CalculationTree',
    'parse_calculation_linkbase',
    'get_calculation_dataframe',
    # Linkbases - Helper
    'get_specific_role_tree',
    # Taxonomy Schema
    'ConceptSchema',
    'parse_schema',
    'parse_schema_to_dict',
    'get_concept_types',
    'get_schema_dataframe',
    'extract_concepts_from_schema',
    # Taxonomy constants
    'statement_full_names',
    'disclosure_full_names',
    # Taxonomy helpers
    'StatementInfo',
    'find_file_by_pattern',
    'build_stm_dis_trees',
    'find_concept_stm_dis',
    'build_taxonomy_dataframe',
    'build_taxonomy_dataframe_from_zip',
    # Utils
    'extract_concept_from_href',
    # EDGAR - Core
    'EG_LOCAL',
    'FilingInfo',
    'get_index_json',
    'get_latest_quarter_dir',
    'find_latest_filing_info_going_back_from',
    'get_filing_info',
    'get_financial_filing_info',
    'InvalidInputException',
    # EDGAR - Stock
    'Stock',
    'update_symbols_data',
    'should_update_symbols_file',
    'NoFilingInfoException',
    # EDGAR - Filing
    'Filing',
    'Statements',
    # EDGAR - Document
    'Document',
    'DocumentText',
    'clean_doc',
    # EDGAR - Data structures
    'DTD',
    'Sgml',
    'SgmlException',
    # EDGAR - Financial
    'FinancialReportEncoder',
    'FinancialElement',
    'FinancialInfo',
    'FinancialReport',
    'MetaDataParsingException',
    'get_financial_report',
    # EDGAR - Loader
    'get_edgar_local_path',
    'get_xbrl_df_by_ticker_year',
    'load_xbrl_filing',
    # 'get_fact_df',
    # 'get_xbrl_df',
    # 'run_xbrl_worker',
    # EDGAR - Versioned pickle
    #'VersionedPickle',
    # EDGAR - Requests
    'GetRequest',
    'RequestException',
    # EDGAR - Helper
    'extract_filing_to_memfs',
]