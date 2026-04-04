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

from tools.archive.verify.bytecode_decoder import decode_bytecode


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

        # Load authored ability index
        try:
            with open(os.path.join(self.base_path, "data", "ability_frame_index.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
                # Create a card_no mapping for faster lookup
                self.consolidated_pseudo = {}
                self.consolidated_pseudo_by_no = {}
                for entry in data.get("abilities", []):
                    if not isinstance(entry, dict):
                        continue
                    source_text = str(entry.get("source_text", "")).strip()
                    if source_text:
                        self.consolidated_pseudo[source_text] = entry
                    for cno in entry.get("cards", []):
                        self.consolidated_pseudo_by_no[cno] = entry
        except Exception as e:
            self.consolidated_pseudo = {}
            self.consolidated_pseudo_by_no = {}
            print(f"Warning: Failed to load ability_frame_index.json: {e}")

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
            if query.isdigit():
                print(f"[cf] No card found with card_id={query} in compiled DB.")
                # Still try fuzzy but report it
                results = self._search_fuzzy(query)
                if results:
                    print(f"  Fuzzy matches containing '{query}' in card_no ({len(results)} found):")
                    for r in results[:5]: print(f"    - {r}")
                    if len(results) > 5: print(f"    ... and {len(results)-5} more.")
                return []
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
            # Exact card_id field match
            for cid, c in db.items():
                if isinstance(c, dict) and c.get("card_id") == qid:
                    return c, cid
            # Logic ID bitmask match (lower 12 bits)
            for cid, c in db.items():
                try:
                    if (int(cid) & 0x0FFF) == qid:
                        return c, cid
                except (ValueError, TypeError):
                    pass
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

    # ── Opcode ID → name lookup ────────────────────────────────────────────
    OPCODE_NAMES = {
        0: "O_NOP", 1: "O_RETURN", 2: "O_JUMP", 3: "O_JUMP_IF_FALSE",
        10: "O_DRAW", 11: "O_ADD_BLADES", 12: "O_ADD_HEARTS", 13: "O_REDUCE_COST",
        14: "O_LOOK_DECK", 15: "O_RECOVER_LIVE", 16: "O_BOOST_SCORE", 17: "O_RECOVER_MEMBER",
        18: "O_BUFF_POWER", 19: "O_IMMUNITY", 20: "O_MOVE_MEMBER", 21: "O_SWAP_CARDS",
        22: "O_SEARCH_DECK", 23: "O_ENERGY_CHARGE", 24: "O_SET_BLADES", 25: "O_SET_HEARTS",
        26: "O_FORMATION_CHANGE", 27: "O_NEGATE_EFFECT", 28: "O_ORDER_DECK", 29: "O_META_RULE",
        30: "O_SELECT_MODE", 31: "O_MOVE_TO_DECK", 32: "O_TAP_OPPONENT", 33: "O_PLACE_UNDER",
        34: "O_FLAVOR_ACTION", 35: "O_RESTRICTION", 36: "O_BATON_TOUCH_MOD", 37: "O_SET_SCORE",
        38: "O_SWAP_ZONE", 39: "O_TRANSFORM_COLOR", 40: "O_REVEAL_CARDS", 41: "O_LOOK_AND_CHOOSE",
        42: "O_CHEER_REVEAL", 43: "O_ACTIVATE_MEMBER", 44: "O_ADD_TO_HAND", 45: "O_COLOR_SELECT",
        47: "O_TRIGGER_REMOTE", 48: "O_REDUCE_HEART_REQ", 49: "O_MODIFY_SCORE_RULE",
        50: "O_ADD_STAGE_ENERGY", 51: "O_SET_TAPPED", 53: "O_TAP_MEMBER",
        57: "O_PLAY_MEMBER_FROM_HAND", 58: "O_MOVE_TO_DISCARD", 60: "O_GRANT_ABILITY",
        61: "O_INCREASE_HEART_COST", 62: "O_REDUCE_YELL_COUNT", 63: "O_PLAY_MEMBER_FROM_DISCARD",
        64: "O_PAY_ENERGY", 65: "O_SELECT_MEMBER", 66: "O_DRAW_UNTIL", 67: "O_SELECT_PLAYER",
        68: "O_SELECT_LIVE", 69: "O_REVEAL_UNTIL", 70: "O_INCREASE_COST", 71: "O_PREVENT_PLAY_TO_SLOT",
        72: "O_SWAP_AREA", 73: "O_TRANSFORM_HEART", 74: "O_SELECT_CARDS", 75: "O_OPPONENT_CHOOSE",
        76: "O_PLAY_LIVE_FROM_DISCARD", 77: "O_REDUCE_LIVE_SET_LIMIT", 78: "O_SET_TARGET_SELF",
        79: "O_SET_TARGET_OPPONENT", 80: "O_PREVENT_SET_TO_SUCCESS_PILE", 81: "O_ACTIVATE_ENERGY",
        82: "O_PREVENT_ACTIVATE", 83: "O_SET_HEART_COST", 90: "O_PREVENT_BATON_TOUCH",
        91: "O_LOOK_DECK_DYNAMIC", 92: "O_REDUCE_SCORE", 93: "O_REPEAT_ABILITY",
        94: "O_LOSE_EXCESS_HEARTS", 95: "O_SKIP_ACTIVATE_PHASE", 96: "O_PAY_ENERGY_DYNAMIC",
        97: "O_PLACE_ENERGY_UNDER_MEMBER", 106: "O_CALC_SUM_COST", 125: "O_LOOK_REORDER_DISCARD",
        126: "O_DIV_VALUE", 127: "O_TRANSFORM_BLADES",
        
        # Conditions
        200: "C_TURN_1", 201: "C_HAS_MEMBER", 202: "C_HAS_COLOR", 203: "C_COUNT_STAGE",
        204: "C_COUNT_HAND", 205: "C_COUNT_DISCARD", 206: "C_IS_CENTER", 207: "C_LIFE_LEAD",
        208: "C_COUNT_GROUP", 209: "C_GROUP_FILTER", 210: "C_OPPONENT_HAS", 211: "C_SELF_IS_GROUP",
        212: "C_MODAL_ANSWER", 213: "C_COUNT_ENERGY", 214: "C_HAS_LIVE_CARD", 215: "C_COST_CHECK",
        216: "C_RARITY_CHECK", 217: "C_HAND_HAS_NO_LIVE", 218: "C_COUNT_SUCCESS_LIVE",
        219: "C_OPPONENT_HAND_DIFF", 220: "C_SCORE_COMPARE", 221: "C_HAS_CHOICE",
        222: "C_OPPONENT_CHOICE", 223: "C_COUNT_HEARTS", 224: "C_COUNT_BLADES",
        225: "C_OPPONENT_ENERGY_DIFF", 226: "C_HAS_KEYWORD", 227: "C_DECK_REFRESHED",
        228: "C_HAS_MOVED", 229: "C_HAND_INCREASED", 230: "C_COUNT_LIVE_ZONE",
        231: "C_BATON", 232: "C_TYPE_CHECK", 233: "C_IS_IN_DISCARD", 234: "C_AREA_CHECK",
        235: "C_COST_LEAD", 236: "C_SCORE_LEAD", 237: "C_HEART_LEAD", 238: "C_HAS_EXCESS_HEART",
        239: "C_NOT_HAS_EXCESS_HEART", 240: "C_TOTAL_BLADES", 241: "C_COST_COMPARE",
        242: "C_BLADE_COMPARE", 243: "C_HEART_COMPARE", 244: "C_OPPONENT_HAS_WAIT",
        245: "C_IS_TAPPED", 246: "C_IS_ACTIVE", 247: "C_LIVE_PERFORMED",
        248: "C_IS_PLAYER", 249: "C_IS_OPPONENT", 250: "C_COUNT_UNIQUE_COLORS",
        301: "C_COUNT_ENERGY_EXACT", 302: "C_COUNT_BLADE_HEART_TYPES",
        303: "C_OPPONENT_HAS_EXCESS_HEART", 304: "C_SCORE_TOTAL_CHECK", 305: "C_MAIN_PHASE",
        306: "C_SELECT_MEMBER", 307: "C_SUCCESS_PILE_COUNT", 308: "C_IS_SELF_MOVE",
        309: "C_DISCARDED_CARDS", 310: "C_YELL_REVEALED_UNIQUE_COLORS", 311: "C_SYNC_COST",
        312: "C_SUM_VALUE", 313: "C_IS_WAIT", 314: "C_ON_ABILITY_RESOLVE",
        315: "C_TARGET_MEMBER_HAS_NO_HEARTS",
    }

    TRIGGER_NAMES = {
        0: "None", 1: "OnPlay", 2: "Constant", 3: "OnLiveStart",
        4: "OnLiveSuccess", 5: "TurnEnd", 6: "TurnStart", 7: "Activated",
        8: "OnAppear", 9: "OnMove", 10: "OnBaton", 11: "OnActivate",
        12: "OnLeaves", 13: "OnAbilityResolve", 14: "OnAbilitySuccess",
        15: "Static", 
    }

    def _opname(self, op):
        return self.OPCODE_NAMES.get(op, f"op={op}")

    def _trigname(self, t):
        return self.TRIGGER_NAMES.get(t, f"trigger={t}")

    def _describe_filter(self, f: dict) -> str:
        if not f:
            return "(none)"
        parts = []
        if f.get("target_player"): parts.append({1:"Self",2:"Opponent"}.get(f["target_player"],f"player={f['target_player']}"))
        if f.get("card_type"): parts.append({1:"Member",2:"Live"}.get(f["card_type"],f"type={f['card_type']}"))
        if f.get("group_enabled"): parts.append(f"group={f.get('group_id',0)}")
        if f.get("unit_enabled"): parts.append(f"unit={f.get('unit_id',0)}")
        if f.get("char_id_1"): parts.append(f"char={f['char_id_1']}" + (f"+{f['char_id_2']}" if f.get("char_id_2") else ""))
        if f.get("color_mask"): parts.append(f"color_mask=0x{f['color_mask']:02X}")
        if f.get("special_id"):
            sid_map = {2:"NOT_MY",3:"NOT_SELF",4:"SAME_NAME",5:"EXACT_COST",6:"SELECTED",7:"NOT_SELECTED"}
            parts.append(sid_map.get(f["special_id"], f"special={f['special_id']}"))
        if f.get("value_enabled"):
            op_str = "<=" if f.get("is_le") else ">="
            kind = "cost" if f.get("is_cost_type") else "hearts"
            parts.append(f"{kind}{op_str}{f.get('value_threshold',0)}")
        if f.get("zone_mask"): parts.append(f"zone=0x{f['zone_mask']:02X}")
        if f.get("compare_accumulated"): parts.append("CMP_ACCUM")
        if not parts:
            return "(any)"
        return ", ".join(parts)

    def _format_frame_program(self, fp: dict) -> str:
        frames = fp.get("frames", []) if isinstance(fp, dict) else []
        if not fp or not frames:
            return "  (no frames)"
        lines = []
        for i, frame in enumerate(frames):
            if isinstance(frame, str):
                lines.append(f"  [{i:02d}] {frame}")
                continue
            if not isinstance(frame, dict):
                lines.append(f"  [{i:02d}] {frame}")
                continue

            # Priority 1: Check for 'semantic' -> 'decoded'
            semantic = frame.get("semantic")
            if isinstance(semantic, dict) and semantic.get("decoded"):
                lines.append(f"  [{i:02d}] {semantic['decoded']}")
                continue

            # Priority 2: Tagged Enum check (Semantic/Return/etc)
            if "Semantic" in frame:
                sem = frame["Semantic"]
                op = sem.get("opcode", 0)
                v = sem.get("value", 0)
                filt = sem.get("filter", {})
                slot = sem.get("slot", {})
                params = sem.get("params") or {}
                negated = sem.get("is_negated", False)
                op_str = self._opname(op)
                filter_str = self._describe_filter(filt)
                slot_parts = []
                if slot.get("source_zone"): slot_parts.append(f"src={slot['source_zone']}")
                if slot.get("dest_zone"): slot_parts.append(f"dst={slot['dest_zone']}")
                if slot.get("target_slot") not in (None, -1, 255): slot_parts.append(f"target={slot['target_slot']}")
                if slot.get("is_dynamic"): slot_parts.append("DYNAMIC")
                if slot.get("is_opponent"): slot_parts.append("OPPONENT")
                slot_str = ("[" + ", ".join(slot_parts) + "]") if slot_parts else ""
                per_card = ""
                if isinstance(params, dict) and (params.get("per_card") or params.get("PER_CARD")):
                    per_card = f" PER_CARD={params.get('per_card') or params.get('PER_CARD')}"
                extra = ""
                if isinstance(params, dict):
                    skipped = {"per_card","PER_CARD"}
                    rest = {k:v2 for k,v2 in params.items() if k not in skipped}
                    if rest: extra = f" params={json.dumps(rest, ensure_ascii=False)}"
                neg_str = " [NOT]" if negated else ""
                lines.append(f"  [{i:02d}] {op_str}(v={v}) filter=[{filter_str}] {slot_str}{per_card}{extra}{neg_str}")
                continue

            # Priority 3: Flat format (opcode, value, attr, slot)
            op_name = frame.get("opcode")
            if not op_name and "opcode_id" in frame:
                op_name = self._opname(frame["opcode_id"])
            
            if op_name:
                v = frame.get("value", 0)
                parts = [f"v={v}"]
                attr = frame.get("attr")
                if isinstance(attr, dict):
                    # Filter attributes?
                    attr_parts = [f"{k}={v2}" for k,v2 in attr.items()]
                    if attr_parts: parts.append(f"attr=[{', '.join(attr_parts)}]")
                slot = frame.get("slot")
                if isinstance(slot, dict):
                    sp = []
                    if slot.get("source_zone"): sp.append(f"src={slot['source_zone']}")
                    if slot.get("dest_zone"): sp.append(f"dst={slot['dest_zone']}")
                    if slot.get("target_slot") is not None: sp.append(f"target={slot['target_slot']}")
                    if sp: parts.append(f"slot=[{', '.join(sp)}]")
                
                lines.append(f"  [{i:02d}] {op_name}({', '.join(parts)})")
                continue

            # Fallback: JSON keys
            keys = ", ".join(frame.keys())
            lines.append(f"  [{i:02d}] Unknown Frame: {{{keys}}}")
            
        return "\n".join(lines) if lines else "  (empty)"

    def _format_condition(self, c: dict) -> str:
        op = c.get("condition_type", c.get("opcode", 0))
        v = c.get("value", 0)
        a = c.get("attr", 0)
        return f"{self._opname(op) if isinstance(op,int) else op}(v={v}, attr=0x{a:X})"

    def _format_cost(self, c: dict) -> str:
        op = c.get("cost_type", c.get("opcode", 0))
        v = c.get("value", 0)
        opt = " [optional]" if c.get("is_optional") else ""
        return f"{op}(v={v}){opt}"

    def display_ai(self, data: dict):
        raw = data.get("raw")
        compiled = data.get("compiled")
        card_no = data.get("card_no")
        cid = data.get("cid")

        print(f"\n{'='*60}")
        print(f"  Card: {card_no}  (engine id: {cid})")
        print(f"{'='*60}")

        if raw:
            print(f"Name    : {raw.get('name')}")
            print(f"Rarity  : {raw.get('rare','?')}  Cost: {raw.get('cost','?')}")
            print(f"\n── JP Ability Text ─────────────────────────────")
            jptxt = raw.get('ability','(none)').strip()
            for line in jptxt.splitlines():
                print(f"  {line}")
            print()

            # Pseudocode
            ab_norm = jptxt
            pseudo = ""
            if card_no in self.ds.manual_pseudo:
                pseudo = self.ds.manual_pseudo[card_no].get("pseudocode","")
                src = "manual"
            elif card_no in getattr(self.ds,'consolidated_pseudo_by_no',{}):
                pseudo = self.ds.consolidated_pseudo_by_no[card_no]
                if isinstance(pseudo, dict): pseudo = pseudo.get("pseudocode","")
                src = "consolidated"
            elif ab_norm in getattr(self.ds,'consolidated_pseudo',{}):
                pseudo = self.ds.consolidated_pseudo[ab_norm]
                if isinstance(pseudo, dict): pseudo = pseudo.get("pseudocode","")
                src = "consolidated-text"
            else:
                pseudo = raw.get("pseudocode","")
                src = "raw"
            if pseudo:
                print(f"Pseudocode ({src}): {pseudo}")

        if compiled:
            abilities = compiled.get("abilities", [])
            print(f"\n── Abilities ({len(abilities)}) ──────────────────────────────")
            for i, ab in enumerate(abilities):
                trig = ab.get("trigger",0)
                pseudo = ab.get("pseudocode","")
                once = " [once/turn]" if ab.get("is_once_per_turn") else ""
                print(f"\n  [Ability {i}] trigger={self._trigname(trig)}{once}")
                if pseudo:
                    print(f"    Pseudocode: {pseudo}")

                # Conditions
                conds = ab.get("conditions", [])
                if conds:
                    print(f"    Conditions:")
                    for c in conds:
                        print(f"      • {self._format_condition(c)}")

                # Costs
                costs = ab.get("costs", [])
                if costs:
                    print(f"    Costs:")
                    for c in costs:
                        print(f"      • {self._format_cost(c)}")

                # Filters
                filters = ab.get("filters", [])
                if filters:
                    print(f"    Filters:")
                    for f in filters:
                        print(f"      • {self._describe_filter(f)}")

                # Frame program
                fp = ab.get("frame_program")
                if fp:
                    print(f"    Semantic Frames:")
                    print(self._format_frame_program(fp))
                else:
                    # Fallback: show raw effects
                    efx = ab.get("effects", [])
                    if efx:
                        print(f"    Effects (raw):")
                        for e in efx:
                            op = e.get("effect_type",e.get("runtime_opcode","?"))
                            v = e.get("runtime_value",e.get("value","?"))
                            a = e.get("runtime_attr",e.get("attr",0))
                            s = e.get("runtime_slot",e.get("slot",0))
                            print(f"      • {op}  v={v}  attr=0x{a:X}  slot={s}")

        # QA
        qas = data.get("qas", [])
        if qas:
            print(f"\n── Q&A Rulings ({len(qas)}) ────────────────────────────")
            for qa in qas[:10]:
                print(f"  [{qa.get('id','?')}] Q: {qa.get('question','').strip()}")
                print(f"         A: {qa.get('answer','').strip()}")
                print()

        # Tests
        tests = data.get("tests", [])
        if tests:
            print(f"── Rust Tests ({len(tests)}) ──────────────────────────────")
            for t in tests[:10]:
                print(f"  • {t}")
        else:
            print("  [!] No Rust tests found for this card.")
        print()

    def generate_report(self, data: dict, output_path: str):
        raw = data.get("raw")
        compiled = data.get("compiled")
        card_no = data.get("card_no")
        cid = data.get("cid")

        lines = [f"# Card Report: {card_no}"]

        if cid:
            val = int(cid)
            lines.append(f"\n**Engine Packed ID**: `{val}`  |  **Logic ID**: `{val & 0x0FFF}`  |  **Variant**: `{val >> 12}`")

        if raw:
            lines.append(f"\n## {raw.get('name')} ({raw.get('rare','?')}, Cost {raw.get('cost','?')})")
            lines.append(f"\n### JP Ability Text\n```\n{raw.get('ability','(none)')}\n```")

            # Pseudocode
            ab_norm = raw.get("ability","").strip()
            pseudo = ""
            if card_no in self.ds.manual_pseudo:
                pseudo = self.ds.manual_pseudo[card_no].get("pseudocode","")
                pseudo_src = "Manual"
            elif card_no in getattr(self.ds,'consolidated_pseudo_by_no',{}):
                pseudo = self.ds.consolidated_pseudo_by_no[card_no]
                if isinstance(pseudo, dict): pseudo = pseudo.get("pseudocode","")
                pseudo_src = "Consolidated"
            elif ab_norm in getattr(self.ds,'consolidated_pseudo',{}):
                pseudo = self.ds.consolidated_pseudo[ab_norm]
                if isinstance(pseudo, dict): pseudo = pseudo.get("pseudocode","")
                pseudo_src = "Consolidated (text match)"
            else:
                pseudo = raw.get("pseudocode","")
                pseudo_src = "Raw"
            if pseudo:
                lines.append(f"\n**Pseudocode** ({pseudo_src}): `{pseudo}`")

        if compiled:
            abilities = compiled.get("abilities", [])
            lines.append(f"\n## Abilities ({len(abilities)})")
            for i, ab in enumerate(abilities):
                trig = ab.get("trigger",0)
                once = " [once/turn]" if ab.get("is_once_per_turn") else ""
                pseudo = ab.get("pseudocode","")
                lines.append(f"\n### Ability {i} — `{self._trigname(trig)}`{once}")
                if pseudo:
                    lines.append(f"- **Pseudocode**: `{pseudo}`")

                conds = ab.get("conditions", [])
                if conds:
                    lines.append("\n**Conditions**:")
                    for c in conds: lines.append(f"- `{self._format_condition(c)}`")

                costs = ab.get("costs", [])
                if costs:
                    lines.append("\n**Costs**:")
                    for c in costs: lines.append(f"- `{self._format_cost(c)}`")

                filters = ab.get("filters", [])
                if filters:
                    lines.append("\n**Filters**: " + " | ".join(f"`{self._describe_filter(f)}`" for f in filters))

                fp = ab.get("frame_program")
                if fp:
                    lines.append("\n**Semantic Frames**:\n```")
                    lines.append(self._format_frame_program(fp))
                    lines.append("```")
                else:
                    efx = ab.get("effects", [])
                    if efx:
                        lines.append("\n**Effects (raw)**:")
                        for e in efx:
                            op = e.get("effect_type",e.get("runtime_opcode","?"))
                            v = e.get("runtime_value",e.get("value","?"))
                            a = e.get("runtime_attr",e.get("attr",0))
                            s = e.get("runtime_slot",e.get("slot",0))
                            lines.append(f"- `{op}  v={v}  attr=0x{a:X}  slot={s}`")

        if data.get("qas"):
            lines.append(f"\n## Q&A Rulings ({len(data['qas'])})")
            for qa in data["qas"]:
                lines.append(f"\n**[{qa.get('id','?')}]** {qa.get('question','').strip()}\n> {qa.get('answer','').strip()}\n")

        lines.append(f"\n## Rust Tests ({len(data.get('tests',[]))})")
        if data.get("tests"):
            for t in data["tests"]: lines.append(f"- `{t}`")
        else:
            lines.append("\n> [!CAUTION]\n> No known Rust tests cover this card.")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Report → {output_path}")

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
    parser.add_argument("--test", help="Run a specific cargo test (substring filter)", type=str)
    parser.add_argument("--fails", help="Path to failing test list to read and display", type=str)
    parser.add_argument("--rust-dir", help="Path to engine_rust_src/src", type=str, default=None)

    args = parser.parse_args()

    # Determine base path (assume repo root)
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # --test: run cargo test directly
    if args.test:
        import subprocess
        rust_dir = args.rust_dir or os.path.join(base_path, "engine_rust_src")
        print(f"Running: cargo test --lib {args.test} -j 4 -- --nocapture")
        result = subprocess.run(
            ["cargo", "test", "--lib", args.test, "-j", "4", "--", "--nocapture"],
            cwd=rust_dir, text=True, encoding="utf-8", errors="replace"
        )
        sys.exit(result.returncode)

    # --fails: print summarized list of failures from a saved file
    if args.fails:
        if os.path.exists(args.fails):
            with open(args.fails, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if "FAILED" in line or "assertion" in line:
                        print(line.rstrip())
        else:
            print(f"File not found: {args.fails}")
        sys.exit(0)

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
