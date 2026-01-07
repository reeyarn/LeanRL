
import fs
from .filing import Filing
import re
import logging 

logger = logging.getLogger(__name__)


def extract_filing_to_memfs(filing: Filing, mem_fs):
    """
    Extracts XBRL files from the Filing instance directly into the provided in-memory filesystem.
    Returns a dictionary of filenames.
    
    Usage: 
    memfs = fs.open_fs('mem://'); 
    files_map = extract_filing_to_memfs(filing, memfs); memfs.listdir("/")
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
            #logger.debug(f"Skipping auxiliary XML file: {fname_lower} (not processing or validating)")
            continue        
        content = None
        
        # For XSD schema files, always use raw data to preserve strict XML formatting
        # BeautifulSoup's string conversion can introduce formatting that breaks strict XML parsers
        if fname_lower.endswith('.xsd'):
            # Priority: raw data for schema files
            if hasattr(doc.doc_text, 'data') and isinstance(doc.doc_text.data, str):
                content = doc.doc_text.data
            elif hasattr(doc.doc_text, 'data') and isinstance(doc.doc_text.data, dict):
                # Process dict values: replace newlines with spaces to preserve XML attribute spacing
                parts = []
                for v in doc.doc_text.data.values():
                    if v:
                        v_str = str(v)
                        # Replace newlines with spaces and strip (same fix as DocumentText.__init__)
                        v_str = re.sub(r"\n", ' ', v_str)
                        v_str = v_str.strip()
                        parts.append(v_str)
                content = " ".join(parts)  # Join with space, not newline
        else:
            # For other XML files, use parsed XML/XBRL objects (BeautifulSoup)
            # --- FIX: Safely access dynamic attributes using getattr ---
            # DocumentText only creates .xml or .xbrl attributes if those tags existed in the source.
            doc_xml = getattr(doc.doc_text, 'xml', None)
            doc_xbrl = getattr(doc.doc_text, 'xbrl', None)
            
            # 1. Try parsed XML/XBRL objects (BeautifulSoup objects)
            if doc_xml:
                content = str(doc_xml)
            elif doc_xbrl:
                content = str(doc_xbrl)
            # 2. Fallback to raw data if it's a string
            elif hasattr(doc.doc_text, 'data') and isinstance(doc.doc_text.data, str):
                content = doc.doc_text.data
            # 3. Fallback if data is a dict but specific tags weren't attributes
            elif hasattr(doc.doc_text, 'data') and isinstance(doc.doc_text.data, dict):
                # Process dict values: replace newlines with spaces to preserve XML attribute spacing
                parts = []
                for v in doc.doc_text.data.values():
                    if v:
                        v_str = str(v)
                        # Replace newlines with spaces and strip (same fix as DocumentText.__init__)
                        v_str = re.sub(r"\n", ' ', v_str)
                        v_str = v_str.strip()
                        parts.append(v_str)
                content = " ".join(parts)  # Join with space, not newline
            
        if not content: 
            continue
        
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
            # extracted_filenames['xml'] = fname_lower
            # is_target = True
            # Exclude auxiliary/report files that are NOT the main XML instance document
            # Common auxiliary patterns: r\d+.xml, report.xml, financial_report.xml
            is_auxiliary = (
                re.match(r'^r\d+\.xml$', fname_lower) or  # r1.xml, r17.xml, etc.
                fname_lower in ['report.xml', 'financial_report.xml', 'reports.xml']
            )
            
            # if is_auxiliary:
            #     logger.debug(f"Skipping auxiliary XML file: {fname_lower}")
            # else:
            if not is_auxiliary:
                # Only treat as XML instance document if it's not auxiliary
                # Instance documents typically have date patterns: ticker-YYYYMMDD.xml or ticker-YYYYMMDD_htm.xml
                extracted_filenames['xml'] = fname_lower
                is_target = True
                logger.debug(f"Identified XML instance document: {fname_lower}")

        elif fname_lower.endswith('_def.xml'):
            extracted_filenames['def'] = fname_lower
            is_target = True
        if is_target:
            # Write directly to memory
            try:
                mem_fs.writetext(fname_lower, content, encoding='utf-8')
                logger.debug(f"Wrote {fname_lower} to memory.")
            except Exception as e:
                logger.error(f"Failed to write {fname_lower} to memory: {e}")
                
    return extracted_filenames