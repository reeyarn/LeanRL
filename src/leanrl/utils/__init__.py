"""
EasyRL Utilities

Common helper functions for XBRL processing.
"""

from .href import (
    extract_concept_from_href,
    parse_href,
    parse_concept_name,
    normalize_concept_name,
    is_valid_concept_name,
)

from .xml_utils import (
    fix_xml_header_spacing,
    fix_all_tag_spacing,
    safe_fix_xml_spacing,
)

__all__ = [
    'extract_concept_from_href',
    'parse_href',
    'parse_concept_name',
    'normalize_concept_name',
    'is_valid_concept_name',
    'fix_xml_header_spacing',
    'fix_all_tag_spacing',
    'safe_fix_xml_spacing',
]