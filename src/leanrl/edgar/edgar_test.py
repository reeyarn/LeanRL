from leanrl.edgar.filing import Filing
import re
import logging 
import xml.etree.ElementTree as ET
import fs
import tempfile
import os
from ..utils.xml_utils import safe_fix_xml_spacing

logger = logging.getLogger(__name__)


def extract_filing_to_memfs_test(filing: Filing, filesystem, validate_xml=True, strict_validation=False):
    """
    Extracts XBRL files from the Filing instance directly into the provided filesystem.
    Works with any PyFilesystem2 filesystem (memfs, tempfs, osfs, etc.).
    Returns a dictionary of filenames.
    
    Args:
        filing: Filing instance to extract from
        filesystem: PyFilesystem2 filesystem object (e.g., memfs, tempfs)
        validate_xml: If True, validate XML after extraction (default: True)
        strict_validation: If True, raise exception on validation failure. If False, log warning and continue (default: False)
    
    Returns:
        dict: Dictionary mapping file types to filenames (e.g., {'xsd': 'file.xsd', 'xml': 'file.xml'})
    """
    extracted_filenames = {'xsd': None, 'pre': None, 'lab': None}
    
    #print(f"Extracting XBRL files to memory from Filing object...")
    
    for filename, doc in filing.documents.items():
        fname_lower = filename.lower()
        
        # Skip auxiliary/report files early - don't process or validate them at all
        # These are typically corrupted HTML/XML fragments that aren't useful
        is_auxiliary = (
            re.match(r'^r\d+\.xml$', fname_lower) or  # r1.xml, r17.xml, etc.
            fname_lower in ['report.xml', 'financial_report.xml', 'reports.xml']
        )
        if is_auxiliary:
            logger.debug(f"Skipping auxiliary XML file: {fname_lower} (not processing or validating)")
            continue
        
        content = None
        
        # --- FIX: Safely access dynamic attributes using getattr ---
        # DocumentText only creates .xml or .xbrl attributes if those tags existed in the source.
        doc_xml = getattr(doc.doc_text, 'xml', None)
        doc_xbrl = getattr(doc.doc_text, 'xbrl', None)
        
        # CRITICAL FIX: For ALL XBRL/XML files, prefer raw data to avoid BeautifulSoup formatting issues
        # BeautifulSoup can reformat XML in ways that break strict parsers:
        # - Removes spaces between attributes (attribute="value"xmlns instead of attribute="value" xmlns)
        # - Changes encoding/formatting that causes ParseError in strict XML parsers
        # This affects: XSD, instance documents, AND linkbase files (_pre.xml, _lab.xml, _cal.xml, _def.xml)
        is_xbrl_file = fname_lower.endswith('.xsd') or fname_lower.endswith('.xml')
        
        # Get content based on file type
        if is_xbrl_file:
            # For ALL XBRL/XML files: use raw data first to preserve exact formatting from SEC
            if hasattr(doc.doc_text, 'data') and isinstance(doc.doc_text.data, str):
                # Data is already processed by DocumentText (newlines replaced, stripped)
                # Validate it to see if it's already corrupted
                if validate_xml:
                    try:
                        ET.fromstring(doc.doc_text.data)
                        logger.debug(f"String data for {fname_lower} is valid XML")
                    except ET.ParseError as orig_err:
                        logger.warning(f"String data for {fname_lower} is already corrupted: {orig_err}")
                        # Use as-is - it's already been processed by DocumentText
                content = doc.doc_text.data
            elif hasattr(doc.doc_text, 'data') and isinstance(doc.doc_text.data, dict):
                # For dict data, prefer 'xml' or 'xbrl' tag specifically (not all tags)
                # This prevents corrupting XML by joining multiple unrelated tags
                from .dtd import DTD
                dtd = DTD()
                xml_tag = dtd.xml.tag
                xbrl_tag = dtd.xbrl.tag
                
                # Try to get the specific XML/XBRL content
                if xml_tag in doc.doc_text.data:
                    raw_content = doc.doc_text.data[xml_tag]
                elif xbrl_tag in doc.doc_text.data:
                    raw_content = doc.doc_text.data[xbrl_tag]
                else:
                    # Fallback: use first value (but log warning)
                    logger.warning(f"No 'xml' or 'xbrl' tag found in data dict for {fname_lower}, using first available value")
                    raw_content = list(doc.doc_text.data.values())[0] if doc.doc_text.data else None
                
                if raw_content:
                    raw_content_str = str(raw_content)
                    
                    # Validate original content before processing (to detect if source is already corrupted)
                    original_is_valid = False
                    if validate_xml:
                        try:
                            # Test original content (before newline replacement)
                            ET.fromstring(raw_content_str)
                            original_is_valid = True
                            logger.debug(f"Original data for {fname_lower} is valid XML")
                        except ET.ParseError as orig_err:
                            logger.warning(f"Original data for {fname_lower} is already corrupted: {orig_err}")
                            # If original is already corrupted, don't process it further - use as-is
                            # Processing might make it worse
                            content = raw_content_str
                        else:
                            # Only process if original is valid
                            # Use aggressive fix ONLY for XSD schema files (no embedded HTML)
                            # Use surgical fix for instance documents (may contain embedded HTML)
                            is_schema_file = fname_lower.endswith('.xsd')
                            content = safe_fix_xml_spacing(raw_content_str, is_schema=is_schema_file)
                    else:
                        # If not validating, use context-aware fix
                        is_schema_file = fname_lower.endswith('.xsd')
                        content = safe_fix_xml_spacing(raw_content_str, is_schema=is_schema_file)
                else:
                    content = None

            elif doc_xml:
                # Last resort: use BeautifulSoup parsed version
                logger.warning(f"Using BeautifulSoup parsed XML for {fname_lower} - may cause parsing issues")
                content = str(doc_xml)
            elif doc_xbrl:
                logger.warning(f"Using BeautifulSoup parsed XBRL for {fname_lower} - may cause parsing issues")
                content = str(doc_xbrl)
        else:
            # For non-XBRL files: any source is fine
            if doc_xml:
                content = str(doc_xml)
            elif doc_xbrl:
                content = str(doc_xbrl)
            elif hasattr(doc.doc_text, 'data') and isinstance(doc.doc_text.data, str):
                content = doc.doc_text.data
            elif hasattr(doc.doc_text, 'data') and isinstance(doc.doc_text.data, dict):
                # Process dict values: use surgical fix to preserve embedded HTML
                parts = []
                for v in doc.doc_text.data.values():
                    if v:
                        v_str = str(v)
                        # Use surgical approach: only fix XML headers, preserve content
                        v_str = safe_fix_xml_spacing(v_str, is_schema=False)
                        parts.append(v_str)
                content = "\n".join(parts)  # Join with newline to preserve structure            
        if not content: 
            continue
        
        # Convert content to bytes if it's a string (for proper encoding handling)
        if isinstance(content, str):
            # Encode as UTF-8 bytes
            content_bytes = content.encode('utf-8')
        else:
            content_bytes = content
        
        # Identify specific file types
        is_target = False
        if fname_lower.endswith('.xsd'):
            extracted_filenames['xsd'] = fname_lower
            is_target = True
        elif fname_lower.endswith('_pre.xml'):
            extracted_filenames['pre'] = fname_lower
            is_target = True
        elif fname_lower.endswith('_lab.xml'):
            extracted_filenames['lab'] = fname_lower
            is_target = True
        elif fname_lower.endswith('_cal.xml'):
            extracted_filenames['cal'] = fname_lower
            is_target = True
        elif fname_lower.startswith("filingsummary"):
            extracted_filenames['filingsummary'] = fname_lower
            is_target = True
        elif fname_lower.endswith(".xml"):
            # Note: Auxiliary files are already skipped at the start of the loop
            # Only treat as XML instance document
            # Instance documents typically have date patterns: ticker-YYYYMMDD.xml or ticker-YYYYMMDD_htm.xml
            extracted_filenames['xml'] = fname_lower
            is_target = True
            logger.debug(f"Identified XML instance document: {fname_lower}")
        elif fname_lower.endswith('_def.xml'):
            extracted_filenames['def'] = fname_lower
            is_target = True
        if is_target:
            # Write directly to filesystem as bytes (not text) to preserve exact encoding
            # This is critical for XML files that may have encoding declarations other than UTF-8
            try:
                filesystem.writebytes(fname_lower, content_bytes)
                logger.debug(f"Wrote {fname_lower} to filesystem ({len(content_bytes)} bytes).")
            except Exception as write_err:
                # Filesystem write operation failed - raise to allow caller to handle fallback
                logger.error(f"Failed to write {fname_lower} to filesystem: {write_err}")
                raise
            
            # VALIDATION: For XBRL/XML files, immediately test if they can be parsed
            # This catches corruption at extraction time rather than later
            if is_xbrl_file and validate_xml:
                try:
                    with filesystem.open(fname_lower, 'rb') as f_test:
                        ET.parse(f_test)
                    logger.debug(f"Validated {fname_lower} - XML is well-formed.")
                except ET.ParseError as e:
                    # XML is corrupted - log detailed error and fail fast
                    logger.error(f"VALIDATION FAILED: {fname_lower} is not well-formed XML: {e}")
                    logger.error(f"File size: {len(content_bytes)} bytes")
                    
                    # Try to extract error position from error message
                    error_pos = None
                    error_msg = str(e)
                    pos_match = re.search(r'column (\d+)', error_msg)
                    if pos_match:
                        error_pos = int(pos_match.group(1))
                    
                    # Log first and last parts for debugging
                    preview_start = content_bytes[:500].decode('utf-8', errors='ignore')
                    preview_end = content_bytes[-500:].decode('utf-8', errors='ignore')
                    logger.error(f"First 500 bytes: {repr(preview_start)}")
                    logger.error(f"Last 500 bytes: {repr(preview_end)}")
                    
                    # If we found the error position, show context around it
                    if error_pos and error_pos < len(content_bytes):
                        # Show 200 bytes before and after error position
                        start_pos = max(0, error_pos - 200)
                        end_pos = min(len(content_bytes), error_pos + 200)
                        error_context = content_bytes[start_pos:end_pos].decode('utf-8', errors='ignore')
                        logger.error(f"Context around error position {error_pos} (chars {start_pos}-{end_pos}):")
                        logger.error(f"{repr(error_context)}")
                        
                        # Show the exact character(s) at error position
                        if error_pos < len(content_bytes):
                            char_at_error = content_bytes[error_pos:error_pos+50].decode('utf-8', errors='ignore')
                            logger.error(f"Character(s) at position {error_pos}: {repr(char_at_error)}")
                    
                    # Check if this might be an encoding issue
                    try:
                        # Try to decode as UTF-8 to see if there are encoding issues
                        content_str = content_bytes.decode('utf-8')
                        logger.debug("File decodes as UTF-8 successfully")
                    except UnicodeDecodeError as ue:
                        logger.error(f"ENCODING ISSUE: File cannot be decoded as UTF-8: {ue}")
                        logger.error(f"Problematic bytes around position {ue.start}: {repr(content_bytes[max(0,ue.start-10):ue.end+10])}")
                    
                    # Raise exception to stop processing this filing (only if strict_validation is True)
                    if strict_validation:
                        raise ValueError(f"Extracted XBRL file {fname_lower} is corrupted and cannot be parsed as XML: {e}")
                    else:
                        logger.warning(f"Continuing despite XML validation failure for {fname_lower} (may be source file corruption)")
                        logger.warning(f"Note: Some SEC filings contain corrupted XML (e.g., spaces in HTML entities/tags).")
                        logger.warning(f"These files may not be parseable with strict XML parsers but may work with lenient parsers.")
                except Exception as e:
                    logger.error(f"Failed to validate {fname_lower}: {e}")
                    raise ValueError(f"Could not validate extracted XBRL file {fname_lower}: {e}")
                
    return extracted_filenames
