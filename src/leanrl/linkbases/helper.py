


# from typing import Dict, List, Set
# from dataclasses import dataclass, field
import xml.etree.ElementTree as ET

# from ..core.namespaces import qname, ArcRoles
# from ..utils import extract_concept_from_href
# from .hierarchy import ConceptNode, ConceptTree


def get_specific_role_tree(pre_filename, role_keywords, memfs=None):
    """
    Parses the _pre.xml file.
    1. Selects the 'best' presentationLink (most arcs) matching the keywords.
    2. Resolves Locators (labels) to actual Concept Names.
    3. Returns the Root and Adjacency Map using clean Concept Names.
    """
    
    # --- Helpers ---
    def local_name(tag):
        return tag.split('}')[-1] if '}' in tag else tag
    
    def get_attr(elem, attr_name):
        # Try standard XLink first
        val = elem.get(f'{{http://www.w3.org/1999/xlink}}{attr_name}')
        if val: return val
        # Fuzzy match key names (robustness)
        for key, value in elem.attrib.items():
            if key.endswith(f'}}{attr_name}') or key == attr_name:
                return value
        return None
    # ---------------
    
    # 1. Open and Parse
    if memfs:
        with memfs.open(pre_filename, 'rb') as f:
            tree = ET.parse(f)
            root_xml = tree.getroot()
    else:
        with open(pre_filename, 'rb') as f:
            tree = ET.parse(f)
            root_xml = tree.getroot()
    
    candidates = []
    
    # 2. Find ALL Candidate Links and Score them
    # 'comprehensive', may not be a bad keyword
    bad_keywords = ['parenthetical',  'equity', 
    'cashflow', 'disclosure', 'detail', 'full', "note", "textblock", "equity", "balance", "position", "information"]
    for elem in root_xml.iter():
        if local_name(elem.tag) == 'presentationLink':
            role = get_attr(elem, 'role')
            if not role: continue
            
            role_lower = str(role).lower()
            
            # --- IMPROVED MATCHING LOGIC ---
            # 1. Check keywords in the Role URI
            uri_match_count = sum(1 for k in role_keywords if k in role_lower)
            
            # 2. Check for "Anchor" concepts inside this link (Highly Reliable)
            # We look for locators pointing to Income Statement abstracts
            has_income_abstract = False
            locators = [c for c in elem if local_name(c.tag) == 'loc']
            for loc in locators:
                href = get_attr(loc, 'href') or ""
                if "IncomeStatementAbstract" in href or "StatementOfOperationsAbstract" in href:
                    has_income_abstract = True
                    break

            # 3. Check if it's a "bad" link (Notes/Equity/etc)
            if any(k in role_lower for k in bad_keywords):
                continue

            # Calculate a score: 
            # - Abstract match is worth 10 points
            # - URI keyword matches are worth 1 point each
            score = (10 if has_income_abstract else 0) + uri_match_count

            if score > 0:
                arcs = [c for c in elem if local_name(c.tag) == 'presentationArc']
                if len(arcs) > 0:
                    candidates.append({
                        'elem': elem,
                        'role': role,
                        'score': score,
                        'arc_count': len(arcs),
                        'role_len': len(role)
                    })    
    if not candidates:
        return None, None
    
    # 3. Select Best Candidate
    # Logic: # Score (highest), Role Length (shortest)
    # wrong assumption: More arcs = Primary Statement. 
    best_link = sorted(candidates, key=lambda x: (x['score'], -x['role_len']), reverse=True)[0]
    target_link = best_link['elem']
    
    # print(f"DEBUG: Selected Pre Link: {best_link['role']} (Arcs: {best_link['arc_count']})")
    
    # 4. Build Map (Label -> Concept) AND Adjacency Graph
    loc_map = {}
    adj = {}
    all_children = set()
    all_nodes = set()
    
    # First Pass: Map Locators
    for child in target_link:
        if local_name(child.tag) == 'loc':
            label = get_attr(child, 'label')
            href = get_attr(child, 'href')
            if label and href:
                # "...xsd#us-gaap_Revenues" -> "us-gaap_Revenues"
                concept_name = href.split('#')[-1]
                loc_map[label] = concept_name
    
    # Second Pass: Build Arcs using Resolved Names
    for child in target_link:
        if local_name(child.tag) == 'presentationArc':
            parent_label = get_attr(child, 'from')
            child_label = get_attr(child, 'to')
            order = float(get_attr(child, 'order') or 1.0)
            
            if parent_label and child_label:
                # RESOLVE HERE:
                parent = loc_map.get(parent_label, parent_label)
                child = loc_map.get(child_label, child_label)
                
                if parent not in adj:
                    adj[parent] = []
                
                adj[parent].append((child, order))
                all_children.add(child)
                all_nodes.add(parent)
                all_nodes.add(child)
    
    # 5. Sort Children by Order
    for parent in adj:
        adj[parent].sort(key=lambda x: x[1]) # Sort by order (2nd element)
        # Flatten structure for output: [(child, order), ...] -> [(child, order), ...]
        # (The consuming function expects this list of tuples)
    
    # 6. Find Root
    potential_roots = all_nodes - all_children
    if not potential_roots: return None, None
    
    root = list(potential_roots)[0]
    
    # Prefer Abstract roots for statements
    for r in potential_roots:
        if 'Statement' in r and 'Abstract' in r:
            root = r
            break
    
    return root, adj
