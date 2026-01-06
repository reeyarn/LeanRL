"""
EDGAR module for accessing and processing SEC filings.
"""

# Core EDGAR classes and functions
from .edgar import (
    EG_LOCAL,
    FilingInfo,
    get_index_json,
    get_latest_quarter_dir,
    find_latest_filing_info_going_back_from,
    get_filing_info,
    get_financial_filing_info,
    InvalidInputException,
)

# Stock and symbol management
from .stock import (
    Stock,
    update_symbols_data,
    should_update_symbols_file,
    NoFilingInfoException,
)

# Filing processing
from .filing import (
    Filing,
    Statements,
)

# Document handling
from .document import Document
from .document_text import DocumentText, clean_doc

# Data structures
from .dtd import DTD
from .sgml import Sgml, SgmlException

# Financial data
from .financials import (
    FinancialReportEncoder,
    FinancialElement,
    FinancialInfo,
    FinancialReport,
    MetaDataParsingException,
    get_financial_report,
)

# Loading and data access
from .loader import (
    get_edgar_local_path,
    get_xbrl_df_by_ticker_year,
    load_xbrl_filing,
    #get_fact_df,
    #get_xbrl_df,
    #run_xbrl_worker,
)

# Versioned pickle
#from .verpkl import VersionedPickle

# HTTP requests
from .requests_wrapper import GetRequest, RequestException

# Helper functions
from .edgar_helper import extract_filing_to_memfs

__all__ = [
    # Core EDGAR
    'EG_LOCAL',
    'FilingInfo',
    'get_index_json',
    'get_latest_quarter_dir',
    'find_latest_filing_info_going_back_from',
    'get_filing_info',
    'get_financial_filing_info',
    'InvalidInputException',
    # Stock
    'Stock',
    'update_symbols_data',
    'should_update_symbols_file',
    'NoFilingInfoException',
    # Filing
    'Filing',
    'Statements',
    # Document
    'Document',
    'DocumentText',
    'clean_doc',
    # Data structures
    'DTD',
    'Sgml',
    'SgmlException',
    # Financial
    'FinancialReportEncoder',
    'FinancialElement',
    'FinancialInfo',
    'FinancialReport',
    'MetaDataParsingException',
    'get_financial_report',
    # Loader
    'get_edgar_local_path',
    'get_xbrl_df_by_ticker_year',
    'load_xbrl_filing',
    #'get_fact_df',
    #'get_xbrl_df',
    #'run_xbrl_worker',
    # Versioned pickle
    'VersionedPickle',
    # Requests
    'GetRequest',
    'RequestException',
    # edgar_helper
    'extract_filing_to_memfs',
]