from leanrl.taxonomy import parse_schema_to_dict
from leanrl.taxonomy import parse_schema
#parse_schema_to_dict
from leanrl import Filing
from leanrl import EG_LOCAL
from leanrl import extract_filing_to_memfs
import fs

url = "https://www.sec.gov/Archives/edgar/data/1567517/0001213900-13-003646.txt"

edgar_root_dir = '/mnt/text/edgar/'
egl = EG_LOCAL(edgar_root_dir = edgar_root_dir)
filing = Filing(url=url, egl = egl)

f_xsd = "/tmp/fern-20130331.xsd"
this_schema = parse_schema(f_xsd)
#this runs correctly

memfs = fs.open_fs('mem://'); 
files_map = extract_filing_to_memfs(filing, memfs); 


with memfs.open(files_map['xsd'], 'rb') as f_xsd:
    this_schema = parse_schema(f_xsd)
    print(f"✅ Parsed {len(this_schema)} concepts from memory filesystem")

# error_msg = """
#   Cell In[3], line 2
#     this_schema = parse_schema(f_xsd)

#   File ~/Dropbox/Codes/LeanRL/src/leanrl/taxonomy/schema.py:174 in parse_schema
#     tree = ET.parse(schema_path)

#   File ~/miniconda3/lib/python3.11/xml/etree/ElementTree.py:1219 in parse
#     tree.parse(source, parser)

#   File ~/miniconda3/lib/python3.11/xml/etree/ElementTree.py:581 in parse
#     self._root = parser._parse_whole(source)

#   File <string>
# ParseError: not well-formed (invalid token): line 1, column 132
# """

# Use the string path (not the closed file object)
f_xsd_path = "/tmp/fern-20130331.xsd"
extension_dict = parse_schema_to_dict(f_xsd_path)


memfs.listdir("/")


with memfs.open(files_map['xsd'], 'rb') as f_xsd:
    extension_dict = parse_schema_to_dict(f_xsd)