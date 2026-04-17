import json
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

# Paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CARDS_RAW_PATH = os.path.join(ROOT_DIR, "data/cards.json")
CARDS_COMPILED_PATH = os.path.join(ROOT_DIR, "data/cards_compiled.json")
QA_DATA_PATH = os.path.join(ROOT_DIR, "data/qa_data.json")

class TestEnricher:
    def __init__(self):
        self.cards_raw = {}
        self.id_to_no = {}
        self.qa_data = {}
        self.load_data()

    def load_data(self):
        print("Loading data sources...")
        if os.path.exists(CARDS_RAW_PATH):
            with open(CARDS_RAW_PATH, "r", encoding="utf-8") as f:
                self.cards_raw = json.load(f)
        
        if os.path.exists(CARDS_COMPILED_PATH):
            with open(CARDS_COMPILED_PATH, "r", encoding="utf-8") as f:
                compiled = json.load(f)
                for db_name in ["member_db", "live_db", "energy_db"]:
                    db = compiled.get(db_name, {})
                    for cid, card in db.items():
                        self.id_to_no[int(cid)] = card.get("card_no")

        if os.path.exists(QA_DATA_PATH):
            with open(QA_DATA_PATH, "r", encoding="utf-8") as f:
                qa_list = json.load(f)
                for qa in qa_list:
                    qid = qa.get("id", "").upper()
                    if qid:
                        self.qa_data[qid] = qa

    def get_card_metadata(self, query) -> Optional[Dict]:
        card_no = None
        if isinstance(query, int):
            card_no = self.id_to_no.get(query)
        else:
            card_no = query

        if not card_no or card_no not in self.cards_raw:
            return None
        
        raw = self.cards_raw[card_no]
        return {
            "card_no": card_no,
            "name": raw.get("name"),
            "ability": raw.get("ability", "").strip(),
            "cost": raw.get("cost"),
            "rare": raw.get("rare")
        }

    def format_card_comment(self, meta: Dict) -> str:
        name_line = f"// CARD: {meta['card_no']} | {meta['name']} (Cost {meta['cost']}, {meta['rare']})"
        ability = meta['ability'].replace("\n", " ")
        ability_line = f"// JP: {ability}"
        return f"{name_line}\n{ability_line}"

    def format_qa_comment(self, qid: str) -> Optional[str]:
        qa = self.qa_data.get(qid.upper())
        if not qa:
            return None
        q = qa.get("question", "").replace("\n", " ").strip()
        a = qa.get("answer", "").replace("\n", " ").strip()
        return f"// QA: {qid} | Q: {q}\n// A: {a}"

    def enrich_file(self, filepath: str, dry_run: bool = False):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        new_lines = []
        
        # Regex patterns
        # 1. Card IDs (integers, usually 4 digits for members/lives)
        # Matches: card_id = 4430; or stage[0] = 4430; or id: 4430,
        card_id_re = re.compile(r"(\b(?:card_id|source_card_id|id|stage\[\d+\])\s*[:=]\s*)(\d+)\b")
        
        # 2. Card Nos (strings)
        card_no_re = re.compile(r"\"((?:LL|PL!)[A-Z!]+-[a-zA-Z0-9]+-[0-9]+-[A-Z＋+]+)\"")
        
        # 3. QA IDs
        qa_re = re.compile(r"\b[qQ](\d+)\b")

        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip lines that are already part of an enriched block
            if line.strip().startswith("// CARD:") or line.strip().startswith("// JP:") or line.strip().startswith("// QA:") or line.strip().startswith("// A:"):
                # Potential update logic could go here, but for now we'll just skip and re-inject if needed
                # or better: we'll look ahead and see if the next line matches.
                i += 1
                continue

            comment_to_add = None

            # Check for QA first (often in function names)
            qa_match = qa_re.search(line)
            if qa_match:
                qid = f"Q{qa_match.group(1)}"
                comment_to_add = self.format_qa_comment(qid)

            # Then Check for Card Nos (precise)
            if not comment_to_add:
                no_match = card_no_re.search(line)
                if no_match:
                    meta = self.get_card_metadata(no_match.group(1))
                    if meta:
                        comment_to_add = self.format_card_comment(meta)

            # Then Check for Card IDs (range 1-10000)
            if not comment_to_add:
                id_match = card_id_re.search(line)
                if id_match:
                    cid = int(id_match.group(2))
                    if 1 <= cid <= 10000:
                        meta = self.get_card_metadata(cid)
                        if meta:
                            comment_to_add = self.format_card_comment(meta)

            if comment_to_add:
                # Check if above line is already this comment to avoid duplication
                indent = len(line) - len(line.lstrip())
                indented_comment = "\n".join([( " " * indent + l) for l in comment_to_add.splitlines()])
                
                prev_lines_block = "\n".join(new_lines[-2:]) if len(new_lines) >= 2 else ""
                if comment_to_add not in prev_lines_block:
                    new_lines.append(indented_comment)
            
            new_lines.append(line)
            i += 1

        new_content = "\n".join(new_lines) + ("\n" if content.endswith("\n") else "")
        
        if content != new_content:
            if dry_run:
                print(f"[DRY RUN] Would update {filepath}")
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {filepath}")
        else:
            print(f"No changes for {filepath}")

def main():
    enricher = TestEnricher()
    
    targets = [
        "engine_rust_src/src/qa_verification_tests.rs",
        "engine_rust_src/src/qa"
    ]
    
    dry_run = "--dry-run" in sys.argv
    
    for t in targets:
        full_path = os.path.join(ROOT_DIR, t)
        if os.path.isfile(full_path):
            enricher.enrich_file(full_path, dry_run=dry_run)
        elif os.path.isdir(full_path):
            for root, _, files in os.walk(full_path):
                for f in files:
                    if f.endswith(".rs"):
                        enricher.enrich_file(os.path.join(root, f), dry_run=dry_run)

if __name__ == "__main__":
    main()
