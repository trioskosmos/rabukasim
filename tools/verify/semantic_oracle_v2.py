
import json
import re
import sys
import os

# Force UTF-8 for Windows consoles
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class SemanticOracleV2:
    """
    Advanced Semantic Oracle for Love Live! SIC TCG.
    Parses JP card text into sequential segments of expectations.
    """
    
    TRIGGERS = {
        "ライブ開始時": "ON_LIVE_START",
        "live_start": "ON_LIVE_START",
        "ライブ成功時": "ON_LIVE_SUCCESS",
        "live_success": "ON_LIVE_SUCCESS",
        "登場時": "ON_PLAY",
        "toujyou": "ON_PLAY",
        "起動": "ACTIVATED",
        "自動": "AUTO",
        "常時": "CONSTANT",
        "jyouji": "CONSTANT"
    }

    PATTERNS = {
        "ENERGY_COST": r'icon_energy\.png',
        "HAND_DRAW": r'(手札に加える|引く|回収する|ドロー)',
        "HAND_DISCARD": r'手札(のカード)?を.*控え室に(置く|置いてもよい)',
        "MEMBER_SACRIFICE": r'このメンバーを.*控え室に(置く|置いてもよい)',
        "ENERGY_ACTIVATE": r'(活性化|アクティブにする)',
        "SCORE_DELTA": r'スコアを.*?[＋+]([0-9１２３４５])',
        "HEART_DELTA": r'ハート.*?([0-9１２３４５])?個?を得る',
        "BLADE_BUFF": r'ブレード([0-9１２３４５])?個?を得る',
        "ENERGY_ADD": r'エネルギーに(置く|追加する)',
        "DECK_SEARCH": r'デッキ(から|のカードを).*?(探す|加える|見る)',
        "MOVE_TO_STAGE": r'舞台に.*?置く',
        "LIVE_RECOVER": r'控え室から.*?ライブを.*?戻す',
        "MEMBER_TAP": r'(休ませる|タップする|スリープにする|WAITにする|待機状態にする)',
        "PREVENT": r'(無効にする|防ぐ|できなくなる)',
    }

    def __init__(self, cards_path=None):
        if cards_path is None:
            potential_paths = [
                "data/cards.json",
                "c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/cards.json"
            ]
            for p in potential_paths:
                if os.path.exists(p):
                    cards_path = p
                    break
        
        if not cards_path or not os.path.exists(cards_path):
             raise FileNotFoundError(f"Could not find cards.json")
             
        with open(cards_path, "r", encoding="utf-8") as f:
            self.db = json.load(f)
            
        self.manual_pseudocode = {}
        manual_path = "data/manual_pseudocode.json"
        if os.path.exists(manual_path):
            with open(manual_path, "r", encoding="utf-8") as f:
                self.manual_pseudocode = json.load(f)

    def extract_segments(self, text):
        """Splits text into sequential logic segments."""
        # Split by 'その後', '。', or ':' (cost/effect delimiter)
        segments = re.split(r'その後|。|：', text)
        return [s.strip() for s in segments if s.strip()]

    def map_expectations(self, segment_text):
        """Maps a text segment to a list of expected deltas."""
        expectations = []
        
        # 1. Energy Cost
        energy_icons = len(re.findall(self.PATTERNS["ENERGY_COST"], segment_text))
        if energy_icons > 0:
            expectations.append({"tag": "ENERGY_COST", "value": energy_icons})

        # 2. Hand Delta (Draw/Recover)
        if re.search(self.PATTERNS["HAND_DRAW"], segment_text):
            count = 1
            num_match = re.search(r'([0-9１２３４５])枚', segment_text)
            if num_match:
                v_map = {"１": 1, "２": 2, "３": 3, "４": 4, "５": 5}
                count = int(v_map.get(num_match.group(1), num_match.group(1)))
            expectations.append({"tag": "HAND_DELTA", "value": count})

        # 3. Discard
        if re.search(self.PATTERNS["HAND_DISCARD"], segment_text):
             expectations.append({"tag": "HAND_DISCARD", "value": 1})
             
        # 4. Sacrifice
        if re.search(self.PATTERNS["MEMBER_SACRIFICE"], segment_text):
             expectations.append({"tag": "MEMBER_SACRIFICE", "value": True})

        # 5. Energy Activation
        if re.search(self.PATTERNS["ENERGY_ACTIVATE"], segment_text):
            expectations.append({"tag": "ENERGY_ACTIVATE", "value": True})

        # 6. Score Deltas
        score_match = re.search(self.PATTERNS["SCORE_DELTA"], segment_text)
        if score_match:
            v_map = {"１": 1, "２": 2, "３": 3, "４": 4, "５": 5}
            val = int(v_map.get(score_match.group(1), score_match.group(1)))
            expectations.append({"tag": "SCORE_DELTA", "value": val})
            
        # 7. Heart Deltas
        heart_match = re.search(self.PATTERNS["HEART_DELTA"], segment_text)
        if heart_match:
            val = 1
            if heart_match.group(1):
                v_map = {"１": 1, "２": 2, "３": 3, "４": 4, "５": 5}
                val = int(v_map.get(heart_match.group(1), heart_match.group(1)))
            expectations.append({"tag": "HEART_DELTA", "value": val})

        # 8. Blade Buffs
        blade_match = re.search(self.PATTERNS["BLADE_BUFF"], segment_text)
        if blade_match:
            val = 1
            if blade_match.group(1):
                v_map = {"１": 1, "２": 2, "３": 3, "４": 4, "５": 5}
                val = int(v_map.get(blade_match.group(1), blade_match.group(1)))
            expectations.append({"tag": "BLADE_DELTA", "value": val})

        # 9. Deck Search / Reveal (Implicitly expects looked_cards change or pause)
        if re.search(self.PATTERNS["DECK_SEARCH"], segment_text):
            expectations.append({"tag": "DECK_SEARCH", "value": True})

        # 10. Stage Movement
        if re.search(self.PATTERNS["MOVE_TO_STAGE"], segment_text):
            expectations.append({"tag": "STAGE_DELTA", "value": 1})

        # 11. Live Recovery
    def map_expectations(self, segment_text):
        """Maps a text segment to a list of expected deltas."""
        expectations = []
        
        # 1. Energy Cost
        energy_icons = len(re.findall(self.PATTERNS["ENERGY_COST"], segment_text))
        if energy_icons > 0:
            expectations.append({"tag": "ENERGY_COST", "value": energy_icons})

        # 2. Hand Delta (Draw/Recover)
        if re.search(self.PATTERNS["HAND_DRAW"], segment_text):
            count = 1
            num_match = re.search(r'([0-9１２３４５])枚', segment_text)
            if num_match:
                v_map = {"１": 1, "２": 2, "３": 3, "４": 4, "５": 5}
                count_str = num_match.group(1)
                count = int(v_map.get(count_str, count_str))
            expectations.append({"tag": "HAND_DELTA", "value": count})

        # 3. Discard
        if re.search(self.PATTERNS["HAND_DISCARD"], segment_text):
             count = 1
             num_match = re.search(r'([0-9１２３４５])枚', segment_text)
             if num_match:
                v_map = {"１": 1, "２": 2, "３": 3, "４": 4, "５": 5}
                count_str = num_match.group(1)
                count = int(v_map.get(count_str, count_str))
             expectations.append({"tag": "HAND_DISCARD", "value": count})
             
        # 4. Sacrifice
        if re.search(self.PATTERNS["MEMBER_SACRIFICE"], segment_text):
             expectations.append({"tag": "MEMBER_SACRIFICE", "value": 1})

        # 5. Energy Activation
        if re.search(self.PATTERNS["ENERGY_ACTIVATE"], segment_text):
            expectations.append({"tag": "ENERGY_ACTIVATE", "value": 1})

        # 6. Score Deltas
        score_match = re.search(self.PATTERNS["SCORE_DELTA"], segment_text)
        if score_match:
            v_map = {"１": 1, "２": 2, "３": 3, "４": 4, "５": 5}
            count_str = score_match.group(1)
            val = int(v_map.get(count_str, count_str))
            expectations.append({"tag": "SCORE_DELTA", "value": val})

        # 7. Hearts
        if re.search(self.PATTERNS["HEART_DELTA"], segment_text):
            expectations.append({"tag": "HEART_DELTA", "value": 1})

        # 8. Tap Members
        if re.search(self.PATTERNS["MEMBER_TAP"], segment_text):
            expectations.append({"tag": "MEMBER_TAP_DELTA", "value": 1})

        # 9. Prevention
        if re.search(self.PATTERNS["PREVENT"], segment_text):
            expectations.append({"tag": "ACTION_PREVENTION", "value": 1})

        # 10. Live Recovery
        if re.search(self.PATTERNS["LIVE_RECOVER"], segment_text):
            expectations.append({"tag": "LIVE_RECOVER", "value": 1})

        # 11. Energy Addition
        if re.search(self.PATTERNS["ENERGY_ADD"], segment_text):
            expectations.append({"tag": "ENERGY_DELTA", "value": 1})
            
        return expectations

    def interpret_card(self, card_id):
        """Interprets a card's text or manual pseudocode into expectations."""
        # PRIORITIZE MANUAL PSEUDOCODE
        if card_id in self.manual_pseudocode:
            pc = self.manual_pseudocode[card_id].get("pseudocode", "")
            if pc:
                return self.interpret_pseudocode(card_id, pc)

        data = self.db.get(card_id, {})
        raw_text = data.get("ability", "")
        
        abilities = []
        # Split by main triggers
        parts = re.split(r'(\{\{.*?\}\}|ライブ開始時|ライブ成功時|登場時|起動|自動|常時)', raw_text)
        
        current_trigger = "UNKNOWN"
        current_text = ""
        
        for part in parts:
            if not part.strip(): continue
            is_trigger = False
            for jp, en in self.TRIGGERS.items():
                if jp in part:
                    if current_text:
                         abilities.append((current_trigger, current_text.strip()))
                    current_trigger = en
                    current_text = ""
                    is_trigger = True
                    break
            if not is_trigger:
                current_text += part
        
        if current_text:
            abilities.append((current_trigger, current_text.strip()))

        card_expectations = []
        for trigger, text in abilities:
            segments = self.extract_segments(text)
            seg_expects = []
            for seg in segments:
                expects = self.map_expectations(seg)
                if expects:
                    seg_expects.append({
                        "text": seg,
                        "deltas": expects
                    })
            
            if seg_expects:
                card_expectations.append({
                    "trigger": trigger,
                    "sequence": seg_expects
                })
        
        return {
            "id": card_id,
            "abilities": card_expectations
        }

    def interpret_pseudocode(self, card_id, pc):
        """Parses structured manual pseudocode into expectations."""
        card_expectations = []
        
        # Split by blocks (TRIGGER: ...)
        blocks = re.split(r'\n\s*\n', pc.strip())
        for block in blocks:
            trigger_match = re.search(r'TRIGGER:\s*(\w+)', block)
            if not trigger_match: continue
            trigger = trigger_match.group(1)
            
            sequence = []
            # Extract effects and costs
            for line in block.split('\n'):
                if "EFFECT:" in line or "COST:" in line:
                    tag_prefix = "COST_" if "COST:" in line else ""
                    # Simple parsers for common pseudocode verbs
                    if "DRAW(" in line:
                        v = re.search(r'DRAW\((\d+)\)', line)
                        if v: sequence.append({"text": line.strip(), "deltas": [{"tag": tag_prefix + "HAND_DELTA", "value": int(v.group(1))}]})
                    elif "DISCARD_HAND(" in line:
                        v = re.search(r'DISCARD_HAND\((\d+)\)', line)
                        if v: sequence.append({"text": line.strip(), "deltas": [{"tag": tag_prefix + "HAND_DISCARD", "value": int(v.group(1))}]})
                    elif "BOOST_SCORE(" in line:
                        v = re.search(r'BOOST_SCORE\((\d+)\)', line)
                        if v: sequence.append({"text": line.strip(), "deltas": [{"tag": tag_prefix + "SCORE_DELTA", "value": int(v.group(1))}]})
                    elif "RECOVER_LIVE(" in line:
                        sequence.append({"text": line.strip(), "deltas": [{"tag": "LIVE_RECOVER", "value": 1}]})
                    elif "RECOVER_MEMBER(1)" in line:
                        sequence.append({"text": line.strip(), "deltas": [{"tag": "HAND_DELTA", "value": 1}, {"tag": "DISCARD_DELTA", "value": -1}]})
                    elif "ADD_HEARTS(" in line:
                        v = re.search(r'ADD_HEARTS\((\d+)\)', line)
                        if v: sequence.append({"text": line.strip(), "deltas": [{"tag": "HEART_DELTA", "value": int(v.group(1))}]})
                    elif "ADD_BLADES(" in line:
                        v = re.search(r'ADD_BLADES\((\d+)\)', line)
                        if v: sequence.append({"text": line.strip(), "deltas": [{"tag": "BLADE_DELTA", "value": int(v.group(1))}]})
                    elif "ENERGY_CHARGE(" in line or "ACTIVATE_ENERGY(" in line:
                        v = re.search(r'(?:ENERGY_CHARGE|ACTIVATE_ENERGY)\((\d+)\)', line)
                        if v: sequence.append({"text": line.strip(), "deltas": [{"tag": "ENERGY_DELTA", "value": int(v.group(1))}]})
                    elif "PAY_ENERGY(" in line:
                        v = re.search(r'PAY_ENERGY\((\d+)\)', line)
                        if v: sequence.append({"text": line.strip(), "deltas": [{"tag": "ENERGY_COST", "value": int(v.group(1))}]})
                    elif "MOVE_TO_DISCARD" in line:
                        sequence.append({"text": line.strip(), "deltas": [{"tag": "STAGE_DELTA", "value": -1}, {"tag": "DISCARD_DELTA", "value": 1}]})
                    elif "TAP_MEMBER" in line:
                        # Handle optional or count-based tap
                        sequence.append({"text": line.strip(), "deltas": [{"tag": "MEMBER_TAP_DELTA", "value": 1}]})
                    elif "PREVENT_" in line or "PREVENT(" in line:
                        sequence.append({"text": line.strip(), "deltas": [{"tag": "ACTION_PREVENTION", "value": 1}]})
                    elif "LOOK_AND_CHOOSE" in line or "SEARCH_DECK" in line:
                        sequence.append({"text": line.strip(), "deltas": [{"tag": "DECK_SEARCH", "value": 1}]})

            if sequence:
                card_expectations.append({
                    "trigger": trigger,
                    "sequence": sequence
                })
                
        return {
            "id": card_id,
            "abilities": card_expectations
        }

if __name__ == "__main__":
    oracle = SemanticOracleV2()
    # Test with PL!N-bp1-007-R
    test_id = "PL!N-bp1-007-R"
    result = oracle.interpret_card(test_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Test with a multi-ability card
    test_id2 = "PL!HS-bp1-003-R＋"
    result2 = oracle.interpret_card(test_id2)
    print("\nProcessing Card: PL!HS-bp1-003-R＋")
    print(json.dumps(result2, indent=2, ensure_ascii=False))
