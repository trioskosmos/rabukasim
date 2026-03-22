import argparse
import json
import os
import re
import sys
import time
from typing import Dict, List, Optional

# Add project root to path to allow imports from engine/compiler
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from verify.bytecode_decoder import decode_bytecode


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class DataStore:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.cards_raw = {}
        self.cards_compiled = {}
        self.qa_data = []
        self.manual_pseudo = {}
        self.consolidated_pseudo = {}
        self.no_to_compiled = {} # card_no -> compiled_data
        
        # Group/Unit mappings (Internal)
        self.GROUP_MAP = {
             "MUSE": 0, "MUS": 0, "μ'S": 0, "Μ'S": 0, "U'S": 0, "M'S": 0,
             "AQOURS": 1, "AQUOURS": 1,
             "NIJIGASAKI": 2, "NIJIGAKU": 2, "NIJI": 2,
             "LIELLA": 3,
             "HASUNOSORA": 4, "HASU": 4,
             "ARISE": 10,
             "SAINT_SNOW": 11,
             "SUNNY_PASSION": 12,
             "MUSICAL": 13
        }
        self.loaded = False

    def load_all(self):
        if self.loaded:
            return
        print("--- Loading Sources ---")
        t0 = time.time()

        # Load Raw
        try:
            with open(os.path.join(self.base_path, "data/cards.json"), "r", encoding="utf-8") as f:
                self.cards_raw = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cards.json: {e}")

        # Load Compiled
        try:
            with open(os.path.join(self.base_path, "data", "cards_compiled.json"), "r", encoding="utf-8") as f:
                self.cards_compiled = json.load(f)
                for cid, c in self.cards_compiled.items():
                    c_no = c.get("card_no")
                    if c_no:
                        self.no_to_compiled[c_no] = c
                        self.no_to_compiled[c_no]["_id"] = cid
        except Exception as e:
            print(f"Warning: Failed to load cards_compiled.json: {e}")

        # Load Manual Pseudocode
        try:
            with open(os.path.join(self.base_path, "data/manual_pseudocode.json"), "r", encoding="utf-8") as f:
                self.manual_pseudo = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load manual_pseudocode.json: {e}")

        # Load QA Data
        try:
            with open(os.path.join(self.base_path, "data/qa_data.json"), "r", encoding="utf-8") as f:
                self.qa_data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load qa_data.json: {e}")

        # Load Consolidated Pseudocode
        try:
            with open(os.path.join(self.base_path, "data", "consolidated_abilities.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
                # Create a card_no mapping for faster lookup
                self.consolidated_pseudo = {}
                self.consolidated_pseudo_by_no = {}
                for text, entry in data.items():
                    self.consolidated_pseudo[text.strip()] = entry
                    if isinstance(entry, dict) and "cards" in entry:
                        for cno in entry["cards"]:
                            self.consolidated_pseudo_by_no[cno] = entry
        except Exception as e:
            self.consolidated_pseudo = {}
            self.consolidated_pseudo_by_no = {}
            print(f"Warning: Failed to load consolidated_abilities.json: {e}")

        self.loaded = True
        print(f"Sources loaded in {time.time() - t0:.2f}s")


class RustTestScanner:
    def __init__(self, rust_dir: str = "engine_rust_src/src"):
        self.rust_dir = rust_dir
        self.cache: Dict[str, List[str]] = {}
        self.indexed = False

    def index(self, force=False):
        if self.indexed and not force:
            return
        if not os.path.exists(self.rust_dir):
            return

        print("--- Indexing Rust Tests ---")
        t0 = time.time()
        # Pre-scan for common card patterns: LL-xxx-xxx or PL!xxx
        # We store which files contain which card_no or QA ID
        for root, _, files in os.walk(self.rust_dir):
            for file in files:
                if file.endswith(".rs"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            # Find likely card numbers or test tags
                            # This regex matches LL-... or PL!... format
                            matches = re.findall(r"(?:LL|PL!)[A-Z!]+-[a-zA-Z0-9]+-[0-9]+-[A-Z＋+]+", content)
                            # Also find repro_ and test_ functions
                            for m in matches:
                                self.cache.setdefault(m, []).append(filepath)
                                # Normalized variant
                                if "＋" in m:
                                    self.cache.setdefault(m.replace("＋", "+"), []).append(filepath)
                                elif "+" in m:
                                    self.cache.setdefault(m.replace("+", "＋"), []).append(filepath)

                            # Find QA IDs (e.g., QA-001) if applicable
                            qa_matches = re.findall(r"QA-[0-9]+", content)
                            for m in qa_matches:
                                self.cache.setdefault(m, []).append(filepath)
                                
                    except Exception:
                        pass
        self.indexed = True
        print(f"Indexed Rust tests in {time.time() - t0:.2f}s")

    def find_tests_for_card(self, card_no: str, related_qas: List[Dict], shared_cards: List[str]) -> List[str]:
        if not self.indexed:
            self.index()
            
        search_terms = set([card_no])
        if "＋" in card_no: search_terms.add(card_no.replace("＋", "+"))
        if "+" in card_no: search_terms.add(card_no.replace("+", "＋"))
        
        for q in related_qas:
            qid = q.get("id")
            if qid: search_terms.add(qid)
            
        for sc in shared_cards:
            search_terms.add(sc)
            if "＋" in sc: search_terms.add(sc.replace("＋", "+"))
            if "+" in sc: search_terms.add(sc.replace("+", "＋"))

        files_to_check = set()
        for term in search_terms:
            if term in self.cache:
                files_to_check.update(self.cache[term])
        
        results = []
        for filepath in sorted(files_to_check):
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if any(term in line for term in search_terms):
                            func_name = "Unknown Test"
                            for j in range(i, -1, -1):
                                if "fn test_" in lines[j] or "fn repro_" in lines[j] or "fn " in lines[j]:
                                    m = re.search(r"fn\s+([a-zA-Z0-9_]+)\s*\(", lines[j])
                                    if m:
                                        func_name = m.group(1)
                                        break
                            results.append(f"{filename}::{func_name}")
            except Exception:
                pass
        return sorted(list(set(results)))


class CardReporter:
    def __init__(self, ds: DataStore, scanner: Optional[RustTestScanner] = None):
        self.ds = ds
        self.scanner = scanner

    def resolve_card(self, query: str):
        # 1. Exact No
        raw, compiled, cid = self._find_by_no(query)
        if not raw and not compiled and query.isdigit():
            # 2. ID
            compiled, cid = self._find_by_id(query)
            if compiled:
                raw = self.ds.cards_raw.get(compiled.get("card_no"))
        
        if not raw and not compiled:
            # 3. Fuzzy match
            return self._search_fuzzy(query)
            
        return {
            "raw": raw,
            "compiled": compiled,
            "cid": cid,
            "card_no": compiled.get("card_no") if compiled else raw.get("card_no") if raw else query
        }

    def _find_by_no(self, no: str):
        nos = [no]
        if "＋" in no: nos.append(no.replace("＋", "+"))
        if "+" in no: nos.append(no.replace("+", "＋"))
        nos = list(dict.fromkeys(nos))

        raw = None
        for n in nos:
            raw = self.ds.cards_raw.get(n)
            if raw: break

        for n in nos:
            for db_name in ["member_db", "live_db", "energy_db"]:
                db = self.ds.cards_compiled.get(db_name, {})
                for c_id, card in db.items():
                    if card.get("card_no") == n:
                        return raw, card, c_id
        return raw, None, None

    def _find_by_id(self, qid_str: str):
        try:
            qid = int(qid_str)
        except ValueError:
            return None, None

        for db_name in ["member_db", "live_db", "energy_db"]:
            db = self.ds.cards_compiled.get(db_name, {})
            if str(qid) in db:
                return db[str(qid)], str(qid)
            for cid, c in db.items():
                if (int(cid) & 0x0FFF) == qid:
                    return c, cid
        return None, None

    def _search_fuzzy(self, query: str):
        found = []
        q_low = query.lower()
        for no, c in self.ds.cards_raw.items():
            if q_low in str(c).lower() or q_low in no.lower():
                found.append(no)
        return found

    def _filter_cards(self, args):
        found = []
        for no, card_raw in self.ds.cards_raw.items():
            compiled = self.ds.no_to_compiled.get(no, {})
            
            match = True
            # Group Filter
            if args.group:
                query_g = args.group.upper()
                target_gid = self.ds.GROUP_MAP.get(query_g)
                # If it's a number string, use it directly
                if target_gid is None and query_g.isdigit():
                    target_gid = int(query_g)
                
                c_groups = compiled.get("groups", [])
                if target_gid is not None:
                    if target_gid not in c_groups: match = False
                else:
                    # If we don't have a mapping, just fail for now or check if any group matches string
                    match = False
                    
            # Member/Name Filter
            if args.member:
                if args.member.lower() not in card_raw.get("name", "").lower(): match = False
                
            # Rarity Filter
            if args.rarity:
                if args.rarity.lower() != card_raw.get("rare", "").lower(): match = False
                
            if match:
                found.append(no)
        return found

    def run_interactive(self):
        print("\n--- Card Finder Interactive Mode ---")
        print("Type a card ID, number, or fuzzy search. 'exit' to quit.")
        print("Use /group, /rarity, /member to filter.")
        
        while True:
            try:
                line = input("\ncf> ").strip()
                if not line or line.lower() in ('exit', 'quit'):
                    break
                
                # Handle filter commands? (Optional complexity)
                # For now just treat as lookup
                self.handle_query(line, skip_tests=True)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

    def get_full_data(self, resolved: Dict, skip_tests: bool = False):
        raw = resolved.get("raw")
        resolved.get("compiled")
        card_no = resolved.get("card_no")
        
        # QA
        related_qas = []
        if card_no:
            for qa in self.ds.qa_data:
                related_cards = qa.get("related_cards", [])
                if any(rc.get("card_no") == card_no for rc in related_cards):
                    related_qas.append(qa)
        
        # Shared Abilities
        shared_cards = []
        baseline = (raw.get("ability", "") if raw else "").strip()
        if baseline:
            for no, c in self.ds.cards_raw.items():
                if no != card_no and c.get("ability", "").strip() == baseline:
                    shared_cards.append(no)
        
        # Tests
        tests = []
        if not skip_tests and self.scanner:
            tests = self.scanner.find_tests_for_card(card_no, related_qas, shared_cards)
            
        return {
            **resolved,
            "qas": related_qas,
            "shared": shared_cards,
            "tests": tests
        }

    def handle_query(self, query: str, skip_tests: bool = False, output_file: str = None, json_mode: bool = False):
        actual_query = extract_card_no(query)
        res = self.resolve_card(actual_query)
        
        if isinstance(res, list):
            print(f"Found {len(res)} matches for '{query}':")
            for n in res[:10]: print(f"  - {n}")
            if len(res) > 10: print(f"  ... and {len(res)-10} more.")
            return

        if json_mode:
            print(json.dumps(res.get("compiled") or res.get("raw"), indent=2, ensure_ascii=False))
            return

        data = self.get_full_data(res, skip_tests=skip_tests)
        
        if output_file:
            self.generate_report(data, output_file)
        else:
            self.display_ai(data)

    def display_ai(self, data: Dict):
        raw = data.get("raw")
        compiled = data.get("compiled")
        card_no = data.get("card_no")
        cid = data.get("cid")
        
        print(f"\n### Card Analysis: {card_no}")
        if cid:
            val = int(cid)
            print(f"- **IDs**: Packed=`{val}`, Logic=`{val & 0x0FFF}`, Var=`{val >> 12}`")

        if raw:
            print(f"- **Name**: {raw.get('name')}")
            ability_text = raw.get('ability', '').replace('\n', ' ')
            print(f"- **JP Ability**: {ability_text}")
            
            # Pseudocode resolution
            ab_norm = raw.get("ability", "").strip()
            pseudo = ""
            if card_no in self.ds.manual_pseudo:
                pseudo = self.ds.manual_pseudo[card_no].get("pseudocode")
                print(f"- **Pseudocode (Manual)**: `{pseudo}`")
            elif card_no in self.ds.consolidated_pseudo_by_no:
                pseudo = self.ds.consolidated_pseudo_by_no[card_no]
                if isinstance(pseudo, dict): pseudo = pseudo.get("pseudocode", "")
                print(f"- **Pseudocode (Consolidated by Card No)**: `{pseudo}`")
            elif ab_norm in self.ds.consolidated_pseudo:
                pseudo = self.ds.consolidated_pseudo[ab_norm]
                if isinstance(pseudo, dict): pseudo = pseudo.get("pseudocode", "")
                print(f"- **Pseudocode (Consolidated by Text)**: `{pseudo}`")
            else:
                pseudo = raw.get("pseudocode", "")
                print(f"- **Pseudocode (Raw)**: `{pseudo}`")

        if compiled:
            for i, ab in enumerate(compiled.get("abilities", [])):
                trig = ab.get("trigger", 0)
                bc = ab.get("bytecode", [])
                print(f"\n#### Ability {i} (Trigger: {trig})")
                print(f"**Bytecode**: `{bc}`")
                print("**Decoded**:\n```\n{0}\n```".format(decode_bytecode(bc)))

        if data.get("qas"):
            print(f"- **QA Rulings**: {len(data['qas'])} items.")
        if data.get("tests"):
            print(f"- **Rust Tests**: {', '.join(data['tests'][:3])}{'...' if len(data['tests']) > 3 else ''}")
        print("\n---\n")

    def generate_report(self, data: Dict, output_path: str):
        raw = data.get("raw")
        compiled = data.get("compiled")
        card_no = data.get("card_no")
        cid = data.get("cid")
        
        lines = [f"# Card Report: {card_no}"]
        
        if cid:
            val = int(cid)
            lines.append("\n## IDs")
            lines.append(f"- **Engine Packed ID**: `{val}`")
            lines.append(f"- **Logic ID**: `{val & 0x0FFF}`")
            lines.append(f"- **Variant Index**: `{val >> 12}`")

        lines.append("\n## Metadata")
        if raw:
            lines.append(f"- **Name**: {raw.get('name')}")
            lines.append(f"- **Card No**: {raw.get('card_no')}")
            lines.append(f"- **Ability (JP)**:\n```\n{raw.get('ability')}\n```")
            
            # Image support
            img = raw.get("image_url") or raw.get("img_path")
            if img:
                # If it's a relative path, try to make it a file:// URL for VS Code
                if not img.startswith("http"):
                    abs_img = os.path.abspath(img)
                    img_url = f"file:///{abs_img.replace(os.sep, '/')}"
                else:
                    img_url = img
                lines.append(f"\n![{raw.get('name')}]({img_url})")

        if data.get("qas"):
            lines.append(f"\n## QA Rulings ({len(data['qas'])})")
            for qa in data["qas"]:
                lines.append(f"**{qa.get('id')}**: {qa.get('question')}\n> {qa.get('answer')}\n")

        lines.append(f"\n## Rust Engine Tests ({len(data['tests'])})")
        if data.get("tests"):
            for t in data["tests"]: lines.append(f"- `{t}`")
        else:
            lines.append("\n> [!CAUTION]\n> No known Rust tests cover this card.")

        if compiled:
            lines.append("\n## Compiled Logic")
            for i, ab in enumerate(compiled.get("abilities", [])):
                lines.append(f"\n### Ability {i}")
                lines.append(f"- **Trigger**: `{ab.get('trigger')}`")
                
                # Filters as table
                filters = ab.get("filters", [])
                if filters:
                    lines.append("\n#### Filters")
                    lines.append("| Type | Target | Details |")
                    lines.append("| :--- | :--- | :--- |")
                    for f in filters:
                        lines.append(f"| {f.get('card_type', 'Any')} | {f.get('target_player', 'Self')} | {f.get('summary', '')} |")

                lines.append(f"\n#### Decoded Bytecode\n```\n{decode_bytecode(ab.get('bytecode', []))}\n```")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Report generated: {output_path}")

    def loop(self):
        self.run_interactive()


def extract_card_no(query):
    pattern = r"([A-Z!]+-[a-zA-Z0-9]+-[0-9]+-[A-Z＋-]+)"
    match = re.search(pattern, query)
    if match: return match.group(1)
    pattern_simple = r"/([^/]+)\.(?:webp|png|jpg)$"
    match_simple = re.search(pattern_simple, query)
    if match_simple: return match_simple.group(1)
    return query


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Unified card lookup and report generator.")
    parser.add_argument("queries", nargs="*", help="Card No, URL, Packed ID, or Logic ID")
    parser.add_argument("-o", "--output", help="Write report(s) to folder or file", type=str)
    parser.add_argument("-i", "--interactive", action="store_true", help="Enter interactive mode")
    parser.add_argument("--json", action="store_true", help="Output raw JSON and exit")
    parser.add_argument("--no-tests", action="store_true", help="Skip Rust test scanning")
    parser.add_argument("--group", help="Filter by group name (fuzzy)")
    parser.add_argument("--member", help="Filter by member name (fuzzy)")
    parser.add_argument("--rarity", help="Filter by rarity")

    args = parser.parse_args()

    # Determine base path (assume repo root)
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    ds = DataStore(base_path)
    ds.load_all()
    
    scanner = None if args.no_tests else RustTestScanner()
    reporter = CardReporter(ds, scanner)

    # Handle Filters
    if args.group or args.member or args.rarity:
        results = reporter._filter_cards(args)
        print(f"Found {len(results)} cards matching filters.")
        for r in results[:20]: print(f"  - {r}")
        if len(results) > 20: print(f"  ... and {len(results) - 20} more.")
        
        # If no queries, we are done
        if not args.queries:
            return

    if args.interactive or (not args.queries and not any([args.group, args.member, args.rarity])):
        reporter.run_interactive()
        return

    for q in args.queries:
        reporter.handle_query(q, skip_tests=args.no_tests, output_file=args.output, json_mode=args.json)


if __name__ == "__main__":
    main()
