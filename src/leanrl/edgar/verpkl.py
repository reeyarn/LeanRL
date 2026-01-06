"""
XBRL filing loader with versioned caching support.

This module provides functionality to load XBRL filings from SEC EDGAR, with support
for versioned caching of parsed objects. The caching system handles:
- Versioned pickle files for Instance and Taxonomy objects
- XML content caching
- In-memory filesystem (memfs) state preservation

The version number is centrally managed in openesef.__init__.PICKLE_VERSION.
"""

import gzip
import pickle
import logging
#from openesef.version import PICKLE_VERSION
import traceback
import lxml
#from datetime import datetime
#import fs
#import sys
#import json
import logging 
logger = logging.getLogger(__name__)



def load_xbrl_filing(ticker=None, year=None, filing_url=None, edgar_local_path='/text/edgar', memory_threshold_gb=16, return_data_pool=False):
    """
    Loads an XBRL filing either by ticker and year or by URL.

    Args:
        ticker (str, optional): Stock ticker symbol. Defaults to None.
        year (int, optional): Filing year. Defaults to None.
        filing_url (str, optional): URL of the filing. Defaults to None.
        edgar_local_path (str, optional): Path to local Edgar repository. Defaults to '/text/edgar'.

    Returns:
        tuple: A tuple containing the Instance object (xid) and the Taxonomy object (tax), or (None, None) on failure.
    """
    #tracemalloc.start()
    memfs = fs.open_fs('mem://') # Create in-memory filesystem
    #edgar_local_path='/text/edgar'
    egl = EG_LOCAL(edgar_local_path)
    xid = None; tax = None; 
    cik = None; tfnm = None; cache_dir = None; xid_cache = None; tax_cache = None; dpl_cache = None
    #ticker="AAPL"; year=2010
    if ticker and year:
        stock = Stock(ticker, egl=egl)
        filing = stock.get_filing(period='annual', year=year)
        cik = stock.cik 
        tfnm = filing.tfnm
    elif filing_url:
        filing = Filing(url=filing_url, egl=egl)
        cik = filing.cik
        tfnm = filing.tfnm
    else:
        logger.error("Either ticker and year or filing_url must be provided.")
        if return_data_pool:
            return None, None, None
        else:
            return None, None

    if not filing:
        logger.error("Filing not found.")
        if return_data_pool:
            return None, None, None
        else:
            return None, None

    # trying to load existing data 
    
    if cik and tfnm:
        cache_dir = f"{edgar_local_path}/10k-bycik/{cik}/{tfnm}"
        xid_cache = f"{cache_dir}/xid.p.gz"
        tax_cache = f"{cache_dir}/tax.p.gz"
        dpl_cache = f"{cache_dir}/data_pool.p.gz"
    entry_points = []
    for key, filename in filing.xbrl_files.items():
        logger.debug(f"Caching XBRL file: {key}, {filename}")
        content = filing.documents[filename].doc_text.data
        content = list(content.values())[0] if isinstance(content, dict) else content
        with memfs.open(filename, 'w') as f:
            f.write(content)
        logger.debug(f"Cached {filename} to memory, length={len(content)}")
        if "xml" in filename:
            entry_points.append(f"mem://{filename}")

    if False and xid_cache and os.path.exists(xid_cache) and tax_cache and os.path.exists(tax_cache) and dpl_cache and os.path.exists(dpl_cache): #and os.path.exists(xml_cache):
        logger.info(f"Loading filing objects from cache: {cache_dir}")
        try:            
            # Now load using VersionedPickle
            xid = VersionedPickle.load(xid_cache, memfs=memfs)
            tax = VersionedPickle.load(tax_cache, memfs=memfs)
            data_pool = VersionedPickle.load(dpl_cache, memfs=memfs)
            logger.info(f"Loaded filing objects from cache: {cache_dir}")
            if return_data_pool:
                return xid, tax, data_pool
            else:
                return xid, tax
        except ValueError as e:
            logger.warning(f"Cache version error: {e}")
            traceback.print_exc()   
        except Exception as e:
            logger.warning(f"Failed to load cached filing objects: {e}")    
            traceback.print_exc()



    data_pool = Pool(max_error=32, esef_filing_root="mem://", memfs=memfs)
    tax = Taxonomy(
        entry_points=entry_points,
        container_pool=data_pool,
        esef_filing_root="mem://",
        memfs=memfs
    )
    data_pool.current_taxonomy = tax
    # mem_tops(top_n=10)
    # check_memory_usage(threshold_gb=memory_threshold_gb)
    
    xid = None
    if filing.xbrl_files.get("xml"):
        xml_filename = filing.xbrl_files.get("xml")
        instance_str = filing.documents[xml_filename].doc_text.data
        instance_str = list(instance_str.values())[0] if isinstance(instance_str, dict) else instance_str
        instance_byte = instance_str.encode('utf-8')
        instance_io = BytesIO(instance_byte)
        instance_tree = lxml_etree.parse(instance_io)
        root = instance_tree.getroot()
        #data_pool.cache_from_string(location=xml_filename, content=instance_str, memfs=memfs)
        xid = Instance(container_pool=data_pool, root=root, memfs=memfs)
        data_pool.add_instance(xid, key=f"mem://{xml_filename}", attach_taxonomy=False)
        data_pool.add_taxonomy(entry_points, esef_filing_root="mem://", memfs=memfs)
        #xid.pool.instances
        # mem_tops(top_n=10)
        # check_memory_usage(threshold_gb=memory_threshold_gb)
        
    else:
        logger.warning("No XML instance document found in filing.")

    if True and cache_dir and xid_cache and tax_cache: 
        try:
            os.makedirs(cache_dir, exist_ok=True) if not os.path.exists(cache_dir) else None
            
            # Save using VersionedPickle
            VersionedPickle.save(xid, xid_cache)
            VersionedPickle.save(tax, tax_cache)
            VersionedPickle.save(data_pool, dpl_cache)
            logger.info(f"Cached filing objects to: {cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to cache filing objects: {e}")
            traceback.print_exc()

    
    if return_data_pool:
        return xid, tax, data_pool
    else:
        return xid, tax

    """
    Loads an XBRL filing either by ticker and year or by URL.

    Args:
        ticker (str, optional): Stock ticker symbol. Defaults to None.
        year (int, optional): Filing year. Defaults to None.
        filing_url (str, optional): URL of the filing. Defaults to None.
        edgar_local_path (str, optional): Path to local Edgar repository. Defaults to '/text/edgar'.

    Returns:
        tuple: A tuple containing the Instance object (xid) and the Taxonomy object (tax), or (None, None) on failure.
    """
    #tracemalloc.start()
    memfs = fs.open_fs('mem://') # Create in-memory filesystem
    #edgar_local_path='/text/edgar'
    egl = EG_LOCAL(edgar_local_path)
    xid = None; tax = None; 
    #cik = None; tfnm = None; cache_dir = None; xid_cache = None; tax_cache = None; #xml_cache = None
    #ticker="AAPL"; year=2010
    if ticker and year:
        stock = Stock(ticker, egl=egl)
        filing = stock.get_filing(period='annual', year=year)
        # cik = stock.cik 
        # tfnm = filing.tfnm
    elif filing_url:
        filing = Filing(url=filing_url, egl=egl)
        # cik = filing.cik
        # tfnm = filing.tfnm
    else:
        logger.error("Either ticker and year or filing_url must be provided.")
        return None, None

    if not filing:
        logger.error("Filing not found.")
        return None, None

    # trying to load existing data 
    
    # if cik and tfnm:
    #     cache_dir = f"{edgar_local_path}/10k-bycik/{cik}/{tfnm}"
    #     xid_cache = f"{cache_dir}/xid.p.gz"
    #     tax_cache = f"{cache_dir}/tax.p.gz"
        #xml_cache = f"{cache_dir}/xml_content.json.gz"
        

    entry_points = []
    for key, filename in filing.xbrl_files.items():
        logger.debug(f"Caching XBRL file: {key}, {filename}")
        content = filing.documents[filename].doc_text.data
        content = list(content.values())[0] if isinstance(content, dict) else content
        with memfs.open(filename, 'w') as f:
            f.write(content)
        logger.debug(f"Cached {filename} to memory, length={len(content)}")
        if "xml" in filename:
            entry_points.append(f"mem://{filename}")


    # if False and os.path.exists(xid_cache) and os.path.exists(tax_cache): #and os.path.exists(xml_cache):
    #     try:
            
    #         # Now load using VersionedPickle
    #         xid = VersionedPickle.load(xid_cache, memfs=memfs)
    #         tax = VersionedPickle.load(tax_cache, memfs=memfs)
            
    #         logger.info(f"Loaded filing objects from cache: {cache_dir}")
    #         return xid, tax
    #     except ValueError as e:
    #         logger.warning(f"Cache version error: {e}")
    #     except Exception as e:
    #         logger.warning(f"Failed to load cached filing objects: {e}")    


    data_pool = Pool(max_error=32, esef_filing_root="mem://", memfs=memfs)
    tax = Taxonomy(
        entry_points=entry_points,
        container_pool=data_pool,
        esef_filing_root="mem://",
        memfs=memfs
    )
    data_pool.current_taxonomy = tax
    # mem_tops(top_n=10)
    # check_memory_usage(threshold_gb=memory_threshold_gb)
    
    xid = None
    if filing.xbrl_files.get("xml"):
        xml_filename = filing.xbrl_files.get("xml")
        instance_str = filing.documents[xml_filename].doc_text.data
        instance_str = list(instance_str.values())[0] if isinstance(instance_str, dict) else instance_str
        instance_byte = instance_str.encode('utf-8')
        instance_io = BytesIO(instance_byte)
        instance_tree = lxml_etree.parse(instance_io)
        root = instance_tree.getroot()
        data_pool.cache_from_string(location=xml_filename, content=instance_str, memfs=memfs)
        xid = Instance(container_pool=data_pool, root=root, memfs=memfs)
        # mem_tops(top_n=10)
        # check_memory_usage(threshold_gb=memory_threshold_gb)
        
    else:
        logger.warning("No XML instance document found in filing.")

    # Extract CIK and filing number for cache path

    
    # # Save to cache
    # if False and cache_dir and xid_cache and tax_cache: #and xml_cache 
    #     try:
    #         os.makedirs(cache_dir, exist_ok=True) if not os.path.exists(cache_dir) else None
            
    #         # # Save XML content
    #         # xml_content = {}
    #         # for filename in filing.xbrl_files.values():
    #         #     if memfs.exists(filename):
    #         #         xml_content[filename] = memfs.readtext(filename)
            
    #         # with gzip.open(xml_cache, 'wt') as f:
    #         #     json.dump(xml_content, f)
            
    #         # Save using VersionedPickle
    #         VersionedPickle.save(xid, xid_cache, memfs=memfs)
    #         VersionedPickle.save(tax, tax_cache, memfs=memfs)
    #         logger.info(f"Cached filing objects to: {cache_dir}")
    #     except Exception as e:
    #         logger.warning(f"Failed to cache filing objects: {e}")
    
    return xid, tax        