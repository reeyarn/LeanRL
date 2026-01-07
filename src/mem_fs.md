# XML Processing Issue: Attribute Spacing When Saving to Filesystem

## Major Issue: XML Attribute Spacing When Removing Newlines

**Problem:**
In `document_text.py`, newlines were being removed with:
```python
value = re.sub(r"\n", '', value)  # ❌ Removes newlines entirely
```

**Why This Breaks XML:**
When XML attributes are on separate lines (common in formatted XML):
```xml
<schema 
  elementFormDefault="qualified"
  xmlns:fern="...">
```

Removing newlines without preserving spaces produces:
```xml
<schema elementFormDefault="qualified"xmlns:fern="...">
                                     ↑ Missing space!
```

This creates **invalid XML** because attributes must be separated by whitespace. Strict XML parsers like `ElementTree` will raise:
```
ParseError: not well-formed (invalid token): line 1, column 132
```

## The Solution: Intelligent Context-Based Line Joining

**⚠️ Important:** A blanket replacement of ALL newlines with spaces can break embedded HTML content in XBRL documents (footnotes, tables, iXBRL content, etc.).

**The Intelligent Fix:**
Analyze the context around EACH newline to decide whether to:
- **Remove it entirely** (join with `''`) - for broken HTML entities, tag names
- **Replace with space** (join with `' '`) - for XML attribute spacing  
- **Keep it** (join with `'\n'`) - for text content between tags

```python
from leanrl.utils.xml_utils import smart_join_lines, safe_fix_xml_spacing

# For instance documents: intelligent context-based fixing
content = safe_fix_xml_spacing(content, is_schema=False)

# For XSD schema files: aggressive fix (pure XML, no HTML)
content = safe_fix_xml_spacing(content, is_schema=True)
```

### How `smart_join_lines()` Works:

For each line boundary, it examines the end of the previous line and start of the current line:

1. **Inside HTML entity** (e.g., `&lt\n;`, `&am\np;`): Remove newline → `&lt;`, `&amp;`
2. **Inside tag name** (e.g., `</li\nnk:label>`): Remove newline → `</link:label>`
3. **Inside tag attributes** (e.g., `attr1="v1"\nattr2="v2"`): Add space → `attr1="v1" attr2="v2"`
4. **Between tags / in content** (e.g., `<p>Line1\nLine2</p>`): Keep newline → preserved

**Key Takeaway:**
When processing XML for strict parsers (like `ElementTree`), **use intelligent context-aware fixes** that analyze each newline individually rather than blanket replacements. This fixes broken XML syntax (entities, tag names, attribute spacing) while preserving legitimate content formatting.

## Related Files
- `src/leanrl/utils/xml_utils.py` - Contains the surgical fix functions
- `src/leanrl/edgar/document_text.py` - Uses surgical fix for all document types
- `src/leanrl/edgar/edgar_helper.py` - Uses context-aware fixing (aggressive for XSD, surgical for others)
- `src/leanrl/edgar/edgar_test.py` - Test version with validation, uses context-aware fixing
- `src/leanrl/taxonomy/schema.py` - Parser that requires valid XML formatting

