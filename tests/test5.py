import fs 
from leanrl.edgar.filing import Filing
from leanrl.edgar import extract_filing_to_memfs_test
from leanrl.edgar import extract_filing_to_memfs
from leanrl import EG_LOCAL
from leanrl import get_edgar_local_path 
url = "https://www.sec.gov/Archives/edgar/data/5272/0001047469-11-001283.txt"; 

edgar_root_dir = get_edgar_local_path(); 
egl = EG_LOCAL(edgar_root_dir = edgar_root_dir)
filing = Filing(url=url, egl=egl)

# Try memory filesystem first
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memfs = fs.open_fs('mem://')
files_map = None
active_fs = memfs
using_tempfs = False
temp_dir = None

files_map = extract_filing_to_memfs(filing, memfs)
print(files_map)

files_map = extract_filing_to_memfs_test(filing, memfs, validate_xml=True, strict_validation=True)


exit()

try:
    # Use strict_validation=False to see detailed errors without stopping
    logger.info("Attempting extraction with memory filesystem...")
    files_map = extract_filing_to_memfs_test(filing, memfs, validate_xml=True, strict_validation=True)
    logger.info("Successfully extracted files to memory filesystem")
except Exception as e:
    logger.warning(f"Memory filesystem operation failed: {e}")
    logger.info("Falling back to temporary filesystem...")
    
    # Create temporary directory and use it as filesystem
    # Use osfs (OS filesystem) instead of tempfs protocol since we already have the directory
    temp_dir = tempfile.mkdtemp(prefix='leanrl_extract_')
    tempfs = fs.open_fs(f'osfs://{temp_dir}')
    active_fs = tempfs
    using_tempfs = True
    
    try:
        logger.info(f"Created temporary filesystem at: {temp_dir}")
        files_map = extract_filing_to_memfs_test(filing, tempfs, validate_xml=True, strict_validation=False)
        logger.info("Successfully extracted files to temporary filesystem")
        logger.warning(f"Note: Files are in temporary directory: {temp_dir}")
        logger.warning("Files will be cleaned up when filesystem is closed or program exits")
    except Exception as tempfs_err:
        logger.error(f"Temporary filesystem operation also failed: {tempfs_err}")
        raise

print(f"Files map: {files_map}")
if using_tempfs:
    print(f"Using temporary filesystem at: {temp_dir}")
else:
    print("Using memory filesystem")
