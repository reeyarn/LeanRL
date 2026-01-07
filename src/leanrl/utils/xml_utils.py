"""
XML Utilities for EDGAR/XBRL Processing

Helper functions for handling XML content, particularly for in-memory filesystem operations.
"""

import re


def fix_xml_header_spacing(content: str) -> str:
    """
    Replace newlines with spaces ONLY in XML declarations and root element opening tags.
    Preserves newlines in the document content (including embedded HTML).
    
    This function addresses the XML attribute spacing issue when XML attributes are split
    across multiple lines. It ensures attributes remain space-separated for strict XML parsers
    like ElementTree, while preserving formatting in document content.
    
    Args:
        content: XML content as a string
        
    Returns:
        XML content with fixed header spacing, content preserved
        
    Example:
        Input:
            <?xml version="1.0"
                  encoding="UTF-8"?>
            <schema
              elementFormDefault="qualified"
              xmlns:fern="...">
              <element>Content with
              embedded newlines</element>
            </schema>
            
        Output:
            <?xml version="1.0" encoding="UTF-8"?>
            <schema elementFormDefault="qualified" xmlns:fern="...">
              <element>Content with
              embedded newlines</element>
            </schema>
    """
    if not content or not isinstance(content, str):
        return content
    
    # Strip leading/trailing whitespace first (XML declaration must start at column 0)
    content = content.strip()
    
    # Pattern breakdown:
    # ^               - Start of string
    # (?:             - Non-capturing group for optional XML declaration
    #   <\?xml[^>]*\?>  - Match <?xml...?>
    # )?              - Make XML declaration optional
    # \s*             - Optional whitespace after declaration
    # <[^/>][^>]*>    - Match opening tag: < followed by non-/ char, then anything until >
    #                   (this ensures we match <schema...> but not </schema> or <element/>)
    
    pattern = r'^((?:<\?xml[^>]*\?>)?\s*<[^/>][^>]*>)'
    
    def replace_newlines_in_header(match):
        header = match.group(1)
        # Replace newlines with spaces in the header, then normalize multiple spaces
        fixed = re.sub(r'\n+', ' ', header)
        # Normalize multiple spaces to single space (common after newline replacement)
        fixed = re.sub(r'\s+', ' ', fixed)
        return fixed
    
    # Only replace in the first match (the header)
    result = re.sub(pattern, replace_newlines_in_header, content, count=1, flags=re.DOTALL)
    
    return result


def smart_join_lines(content: str) -> str:
    """
    Intelligently join lines by analyzing context around each newline.
    
    For each newline, decide whether to:
    - Remove it entirely (join with '') - for broken tag names, HTML entities
    - Replace with space (' ') - for attribute spacing
    - Keep it ('\n') - for content between tags
    
    Args:
        content: XML/HTML content as a string
        
    Returns:
        Content with intelligently fixed newlines
    """
    if not content or not isinstance(content, str):
        return content
    
    lines = content.split('\n')
    if len(lines) <= 1:
        return content
    
    result_parts = [lines[0]]  # Start with first line
    
    for i in range(1, len(lines)):
        prev_line = lines[i - 1]
        curr_line = lines[i]
        
        # Get the context: end of previous line and start of current line
        prev_end = prev_line[-50:] if prev_line else ''
        curr_start = curr_line[:50] if curr_line else ''
        
        # Decision rules for what to insert between prev and curr line:
        
        # RULE 1: Inside HTML entity (e.g., "&lt\n;", "&am\np;")
        # Pattern: ends with & followed by letters/numbers, next starts with letters/numbers then ;
        if re.search(r'&[a-zA-Z0-9#]+$', prev_end) and re.match(r'^[a-zA-Z0-9#]*;', curr_start):
            # Join with nothing - remove newline entirely
            result_parts.append(curr_line)
            continue
        
        # RULE 2: Inside a tag name (e.g., "</li\nnk:label>", "<ta\ng>")
        # Pattern: inside < and > with no = sign (attributes have =)
        # Check if we're inside an unclosed tag
        last_open = prev_end.rfind('<')
        last_close = prev_end.rfind('>')
        if last_open > last_close:  # We're inside a tag
            # Check if there's an = sign, which indicates we're in attributes
            after_open = prev_end[last_open:]
            if '=' not in after_open and '=' not in curr_start.split('>')[0]:
                # No attributes yet - we're in the tag name, join with nothing
                result_parts.append(curr_line)
                continue
        
        # RULE 3: Inside tag attributes (e.g., 'attr="value"\nattr2="value2"')
        # Pattern: inside < and >, has = signs
        if last_open > last_close:  # Still inside a tag
            # We're in attributes area, join with space
            result_parts.append(' ' + curr_line)
            continue
        
        # RULE 4: Between tags or in content
        # Default: preserve the newline (join with \n)
        result_parts.append('\n' + curr_line)
    
    return ''.join(result_parts)


def fix_all_tag_spacing(content: str) -> str:
    """
    Fix attribute spacing and broken tags/entities throughout the document.
    
    Uses intelligent line joining to decide for each newline whether to:
    - Remove it (for broken tag names, HTML entities)  
    - Replace with space (for attribute spacing)
    - Keep it (for content between tags)
    
    This preserves text content while fixing XML syntax issues caused by newlines.
    
    Args:
        content: XML content as a string
        
    Returns:
        XML content with fixed spacing throughout
    """
    if not content or not isinstance(content, str):
        return content
    
    # Strip leading/trailing whitespace
    content = content.strip()
    
    # Use intelligent line joining based on context
    result = smart_join_lines(content)
    
    return result


def safe_fix_xml_spacing(content: str, is_schema: bool = False) -> str:
    """
    Safely fix XML spacing with different strategies based on content type.
    
    Args:
        content: XML content as a string
        is_schema: If True, applies most aggressive fixing (for XSD files).
                   If False, fixes all tag spacing but preserves content (for XBRL instance documents).
    
    Returns:
        XML content with fixed spacing
    """
    if not content or not isinstance(content, str):
        return content
    
    if is_schema:
        # For XSD schema files: most aggressive approach is safe
        # These files are pure XML schema definitions without embedded HTML
        content = re.sub(r'\n', ' ', content)
        content = re.sub(r'\s+', ' ', content)  # Normalize multiple spaces
        content = content.strip()
    else:
        # For instance documents and linkbases: fix all tag spacing but preserve content
        # This addresses attribute spacing issues throughout the document
        content = fix_all_tag_spacing(content)
    
    return content

