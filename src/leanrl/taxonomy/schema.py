"""
XBRL Taxonomy Schema Parser

Extract concept definitions from XBRL taxonomy schema (.xsd) files.
Includes metadata like type, periodType, balance, and abstract status.
"""

from typing import List, Dict, Optional, Set, Union, IO
from dataclasses import dataclass, field, asdict
from pathlib import Path
import xml.etree.ElementTree as ET


# XML Schema namespace
XS_NS = '{http://www.w3.org/2001/XMLSchema}'

# XBRL Instance namespace (for periodType, balance attributes)
XBRLI_NS = '{http://www.xbrl.org/2003/instance}'

# Common monetary type patterns
MONETARY_TYPES = {
    'xbrli:monetaryItemType',
    'monetaryItemType',
    'us-types:monetaryItemType',
}

# Patterns that indicate monetary types (suffix matching)
MONETARY_TYPE_SUFFIXES = (
    'MonetaryItemType',
    'monetaryItemType',
)


@dataclass
class ConceptSchema:
    """
    Schema metadata for an XBRL concept extracted from a taxonomy .xsd file.
    
    This represents the schema-level definition of a concept, including
    its data type, period type, balance, and other XML Schema attributes.
    
    Note: This is different from ConceptNode (which represents a node in 
    a hierarchy tree from linkbases).
    
    Attributes:
        name: Concept name (e.g., 'us-gaap_Assets')
        prefix: Namespace prefix (e.g., 'us-gaap' or 'tsla')
        id: Element ID attribute (e.g., "tsla_ResaleValueGuaranteesCurrentPortion")
        type: XML Schema type (e.g., 'xbrli:monetaryItemType')
        period_type: 'instant' or 'duration'
        balance: 'debit', 'credit', or None
        abstract: Whether this is an abstract grouping element
        substitution_group: The substitution group (e.g., 'xbrli:item')
        nillable: Whether the element can be nil
    """
    name: str
    prefix: str = ''
    id: str = ''
    type: str = ''
    period_type: Optional[str] = None  # 'instant' or 'duration'
    balance: Optional[str] = None       # 'debit' or 'credit'
    abstract: bool = False
    substitution_group: str = ''
    nillable: bool = True
    
    @property
    def is_monetary(self) -> bool:
        """Check if this concept represents a monetary value."""
        if not self.type:
            return False
        
        # Exact match
        if self.type in MONETARY_TYPES:
            return True
        
        # Suffix match (handles derived types)
        if self.type.endswith(MONETARY_TYPE_SUFFIXES):
            return True
        
        return False
    
    @property
    def is_instant(self) -> bool:
        """Check if this is a point-in-time (balance sheet) concept."""
        return self.period_type == 'instant'
    
    @property
    def is_duration(self) -> bool:
        """Check if this is a period (income statement) concept."""
        return self.period_type == 'duration'
    
    @property
    def is_debit(self) -> bool:
        """Check if this concept has debit balance."""
        return self.balance == 'debit'
    
    @property
    def is_credit(self) -> bool:
        """Check if this concept has credit balance."""
        return self.balance == 'credit'
    
    @property
    def short_name(self) -> str:
        """Get the local name without prefix."""
        if '_' in self.name:
            return self.name.split('_', 1)[1]
        return self.name
    
    @property
    def is_usgaap(self) -> bool:
        """Check if this concept is part of the US GAAP taxonomy."""
        return self.name.startswith('us-gaap_') or self.prefix.startswith('us-gaap')
    
    @property
    def is_extension(self) -> bool:
        # If it's not standard GAAP (and not SEC standard like 'dei' or 'srt'), it's an extension
        standard_prefixes = ['us-gaap', 'dei', 'srt', 'country', 'currency', 'exch', 'stpr', 'sic', "sec"]
        # If prefix is empty, check name, otherwise check prefix
        p = self.prefix if self.prefix else self.name.split('_')[0]
        if not p:
            return False
        return p.lower() not in standard_prefixes
        
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


def parse_schema(
    schema_path: Union[str, IO],
    #prefix: str = 'us-gaap',
    prefix: Optional[str] = None,
    filter_monetary: bool = False,
    filter_instant: bool = False,
    filter_duration: bool = False,
    include_abstract: bool = False,
    ) -> List[ConceptSchema]:
    """
    Parse an XBRL taxonomy schema and extract concept definitions.
    
    Args:
        schema_path: Path to the .xsd schema file or file-like object
        prefix: Namespace prefix to filter by (e.g., 'us-gaap').
                If None (default), accepts ALL concepts found in the file,
                using the prefix defined in the element 'id'.
        filter_monetary: If True, only return monetary type concepts
        filter_instant: If True, only return instant (balance sheet) concepts
        filter_duration: If True, only return duration (income statement) concepts
        include_abstract: If True, include abstract grouping elements
    
    Returns:
        List of ConceptSchema objects matching the filters
    
    Examples:
        >>> # All concrete US-GAAP concepts
        >>> schemas = parse_schema('us-gaap-2020-01-31.xsd')
        >>> len(schemas)
        15000
        
        >>> # Only monetary concepts
        >>> monetary = parse_schema('us-gaap-2020-01-31.xsd', filter_monetary=True)
        >>> 
        >>> # Balance sheet items only
        >>> bs_items = parse_schema('us-gaap-2020-01-31.xsd', 
        ...                         filter_monetary=True, 
        ...                         filter_instant=True)
        >>> 
        >>> # Income statement items only
        >>> is_items = parse_schema('us-gaap-2020-01-31.xsd',
        ...                         filter_monetary=True,
        ...                         filter_duration=True)
    """
    # Handle both string paths and file-like objects
    if isinstance(schema_path, str):
        # Direct path parsing
        tree = ET.parse(schema_path)
    else:
        # File-like object - read content and parse from string
        # This handles memory filesystem objects and other file-like objects more robustly
        content = schema_path.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        try:
            tree = ET.ElementTree(ET.fromstring(content))
        except ET.ParseError as e:
            print("\n" + "="*80)
            print("XML PARSING ERROR - DEBUG INFO")
            print("="*80)
            print(f"Error: {e}")
            print(f"\nContent length: {len(content)} characters")
            print(f"\nFirst 300 characters of content:")
            print(repr(content[:300]))
            print(f"\nCharacter at position 131 (column 132): {repr(content[131])} (ord={ord(content[131])})")
            print(f"\nContext around position 132 (chars 100-160):")
            print(repr(content[100:160]))
            print(f"\nFirst line:")
            first_line = content.split('\n')[0] if '\n' in content else content[:200]
            print(repr(first_line))
            print("="*80 + "\n")
            raise
    
    root = tree.getroot()
    
    results = []
    
    # Find all xs:element declarations
    for elem in root.iter(f'{XS_NS}element'):
        # 1. Get fundamental identifiers
        elem_id = elem.get('id', '')
        raw_name = elem.get('name', '')
        if not raw_name:
            continue
        #raw_name = elem.get('name')
        # if not name:
        #     continue

        # 2. Determine the full Concept Name
        # In XBRL, the 'id' attribute typically contains {prefix}_{name}
        # e.g., id="tsla_AutomotiveSales" or id="us-gaap_Assets"
        if elem_id:
            name = elem_id
        elif prefix:
            # Fallback: if no ID but prefix provided, construct it
            name = f'{prefix}_{raw_name}'
        else:
            # Fallback: just use the raw name (rare in strict XBRL)
            name = raw_name
        
        # # Add prefix if not present
        # if prefix and not name.startswith(f'{prefix}_'):
        #     # Check if the element has an id with the prefix
        #     elem_id = elem.get('id', '')
        #     if elem_id.startswith(f'{prefix}_'):
        #         name = elem_id
        #     else:
        #         name = f'{prefix}_{raw_name}'
        # --- NEW LOGIC: Extract Prefix ---
        current_prefix = None
        if '_' in name:
            # e.g., "us-gaap_Assets" -> "us-gaap"
            current_prefix = name.split('_', 1)[0]
        elif prefix:
            current_prefix = prefix
        # ---------------------------------        
        # 3. Apply Prefix Filter (if user specifically requested one)
        if prefix is not None:
            # If the resulting name doesn't start with the requested prefix, skip it
            if not name.startswith(f'{prefix}_'):
                continue
        
        # Get attributes
        #elem_id = elem.get('id', '')
        elem_type = elem.get('type', '')
        abstract = elem.get('abstract', 'false').lower() == 'true'
        nillable = elem.get('nillable', 'true').lower() == 'true'
        substitution_group = elem.get('substitutionGroup', '')
        
        # XBRL-specific attributes
        period_type = elem.get(f'{XBRLI_NS}periodType')
        balance = elem.get(f'{XBRLI_NS}balance')
        
        # Create concept schema
        try:
            schema = ConceptSchema(
                name=name,
                prefix=current_prefix,  # <--- Pass the extracted prefix here
                id=elem_id,
                type=elem_type,
                period_type=period_type,
                balance=balance,
                abstract=abstract,
                substitution_group=substitution_group,
                nillable=nillable,
            )
        except Exception as e:
            print(f"Error creating ConceptSchema for {name}: {e}")
            continue
        # Apply filters
        if not include_abstract and abstract:
            continue
        
        if filter_monetary and not schema.is_monetary:
            continue
        
        if filter_instant and not schema.is_instant:
            continue
        
        if filter_duration and not schema.is_duration:
            continue
        
        results.append(schema)
    
    return results


def parse_schema_to_dict(
    schema_path: Union[str, IO],
    **kwargs
    ) -> Dict[str, ConceptSchema]:
    """
    Parse schema and return as dict keyed by concept name.
    
    Same parameters as parse_schema().
    
    Returns:
        Dict mapping concept name (str) to ConceptSchema object
    """
    schemas = parse_schema(schema_path, **kwargs)
    #schemas_dict = {s.name: s for s in schemas}
    # schemas_dict["is_extension"] = schemas.is_extension
    # schemas_dict["is_usgaap"] = schemas.is_usgaap
    #return schemas_dict
    return {s.name: s for s in schemas}


def get_concept_types(schema_path: Union[str, IO]) -> Dict[str, Set[str]]:
    """
    Get a summary of all concept types in the schema.
    
    Returns:
        Dict with keys 'types', 'period_types', 'balances', 'substitution_groups'
    """
    schemas = parse_schema(schema_path, include_abstract=True)
    
    return {
        'types': set(s.type for s in schemas if s.type),
        'period_types': set(s.period_type for s in schemas if s.period_type),
        'balances': set(s.balance for s in schemas if s.balance),
        'substitution_groups': set(s.substitution_group for s in schemas if s.substitution_group),
    }


def get_schema_dataframe(schema_path: Union[str, IO], **kwargs):
    """
    Parse schema and return as pandas DataFrame.
    
    Same parameters as parse_schema().
    
    Returns:
        pandas DataFrame with concept schema information
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for get_schema_dataframe()")
    
    schemas = parse_schema(schema_path, **kwargs)
    
    rows = [s.to_dict() for s in schemas]
    df = pd.DataFrame(rows)
    
    # Add derived columns
    if not df.empty:
        df['is_monetary'] = df.apply(
            lambda r: ConceptSchema(**r).is_monetary, axis=1
        )
    
    return df


def extract_concepts_from_schema(
    schema_path: Union[str, IO],
    prefix: str = 'us-gaap',
    filter_monetary: bool = False,
    include_abstract: bool = False,
    ) -> List[str]:
    """
    Extract concept names from an XBRL taxonomy schema.
    
    This is a simplified function that returns just concept names (strings).
    For full metadata, use parse_schema() which returns ConceptSchema objects.
    
    Args:
        schema_path: Path to the .xsd schema file or file-like object
        prefix: Namespace prefix (e.g., 'us-gaap')
        filter_monetary: If True, only return monetary type concepts
        include_abstract: If True, include abstract grouping elements
    
    Returns:
        List of concept name strings (e.g., ['us-gaap_Assets', 'us-gaap_Liabilities', ...])
    
    Examples:
        >>> concepts = extract_concepts_from_schema('us-gaap-2020-01-31.xsd')
        >>> len(concepts)
        15000
        >>> concepts[:3]
        ['us-gaap_AccountingStandardsUpdateExtensibleList', ...]
    """
    schemas = parse_schema(
        schema_path,
        prefix=prefix,
        filter_monetary=filter_monetary,
        include_abstract=include_abstract,
    )
    return [s.name for s in schemas]