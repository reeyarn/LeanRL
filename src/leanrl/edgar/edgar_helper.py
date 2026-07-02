
import fs
from .filing import Filing
import re
import logging 
from ..utils.xml_utils import safe_fix_xml_spacing

logger = logging.getLogger(__name__)


# Only XBRL instance documents declare contexts; linkbases never do.
_INSTANCE_MARKERS = ('contextRef', '<xbrli:context')


def _looks_like_instance(content: str) -> bool:
    """Content-based check for an XBRL instance document."""
    return any(marker in content for marker in _INSTANCE_MARKERS)


def extract_filing_to_memfs(filing: Filing, mem_fs):
    """
    Extracts XBRL files from the Filing instance directly into the provided in-memory filesystem.
    Returns a dictionary of filenames.

    The instance document ('xml' key) is validated by content (contextRef /
    xbrli:context), not by filename: early-era filings (2009-2010) ship
    combined or renamed linkbases (e.g. defnref.xml) that a suffix-only rule
    misclassifies as the instance. When several files pass the content check,
    the largest one wins.

    Usage:
    memfs = fs.open_fs('mem://');
    files_map = extract_filing_to_memfs(filing, memfs); memfs.listdir("/")
    """
    extracted_filenames = {'xsd': None, 'pre': None, 'lab': None}
    instance_size = -1
    
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
                # Process dict values for XSD: use aggressive approach (safe for schema files)
                parts = []
                for v in doc.doc_text.data.values():
                    if v:
                        v_str = str(v)
                        # For XSD schema files, aggressive spacing fix is safe (no HTML content)
                        v_str = safe_fix_xml_spacing(v_str, is_schema=True)
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
        elif fname_lower.endswith('_def.xml'):
            # must come before the generic .xml branch, or _def.xml files
            # overwrite the instance under the 'xml' key
            extracted_filenames['def'] = fname_lower
            is_target = True
        elif fname_lower.endswith('_ref.xml'):
            extracted_filenames['ref'] = fname_lower
            is_target = True
        elif fname_lower.startswith("filingsummary"):
            extracted_filenames['filingsummary'] = fname_lower
            is_target = True
        elif fname_lower.endswith(".xml"):
            if _looks_like_instance(content):
                # Instance candidate: content decides, largest wins (early-era
                # filings can ship several XML members)
                if len(content) > instance_size:
                    extracted_filenames['xml'] = fname_lower
                    instance_size = len(content)
                is_target = True
                logger.debug(f"Identified XML instance document: {fname_lower}")
            else:
                # No contexts -> a combined or renamed linkbase (e.g. Waters
                # FY2009 defnref.xml = definition + reference). Specific
                # suffix matches above still take precedence.
                if 'def' in fname_lower and extracted_filenames.get('def') is None:
                    extracted_filenames['def'] = fname_lower
                    is_target = True
                if 'ref' in fname_lower and extracted_filenames.get('ref') is None:
                    extracted_filenames['ref'] = fname_lower
                    is_target = True
                if not is_target:
                    logger.debug(f"Skipping non-instance XML file: {fname_lower}")
        if is_target:
            # Write directly to memory
            try:
                mem_fs.writetext(fname_lower, content, encoding='utf-8')
                logger.debug(f"Wrote {fname_lower} to memory.")
            except Exception as e:
                logger.error(f"Failed to write {fname_lower} to memory: {e}")
                
    return extracted_filenames