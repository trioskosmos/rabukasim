#!/usr/bin/env python3
"""
Pseudocode Oracle v3 - Generates semantic truth from structured pseudocode.

Improvements in v3:
- Handle multiple triggers on same ability
- Better dynamic value handling
- PER_CARD, HEART_TYPE modifiers
- Improved effect parsing with semicolons
- Better target extraction (-> PLAYER, -> SELF)

Usage:
    python tools/verify/pseudocode_oracle.py
    
Output:
    reports/semantic_truth_v3.json
"""

import json
import re
import os
import sys

# Force UTF-8 for Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


class PseudocodeOracle:
    """
    Parses structured pseudocode into semantic expectations.
    """
    
    # Trigger mapping - preserve underscores!
    TRIGGER_MAP = {
        "ON_PLAY": "ON_PLAY",
        "ON_LIVE_START": "ON_LIVE_START",
        "ON_LIVE_SUCCESS": "ON_LIVE_SUCCESS",
        "ON_REVEAL": "ON_REVEAL",
        "ON_MEMBER_DISCARD": "ON_MEMBER_DISCARD",
        "ACTIVATED": "ACTIVATED",
        "CONSTANT": "CONSTANT",
        "ON_LEAVES": "ON_LEAVES",
        "TURN_END": "TURN_END",
        "AUTO": "AUTO",
    }
    
    # Mapping from pseudocode effects to semantic delta tags
    EFFECT_TO_DELTA = {
        # Basic effects
        "DRAW": "HAND_DELTA",
        "DISCARD_HAND": "HAND_DISCARD",
        "TAP_OPPONENT": "MEMBER_TAP_DELTA",
        "ADD_BLADES": "BLADE_DELTA",
        "BOOST_SCORE": "SCORE_DELTA",
        
        # Recovery effects
        "RECOVER_MEMBER": "HAND_DELTA",
        "RECOVER_LIVE": "LIVE_RECOVER",
        
        # Energy effects
        "ACTIVATE_ENERGY": "ENERGY_ACTIVATE",
        "ACTIVATE_MEMBER": "ENERGY_ACTIVATE",
        "PAY_ENERGY": "ENERGY_COST",
        
        # Heart effects
        "ADD_HEARTS": "HEART_DELTA",
        "REDUCE_HEART_REQ": "HEART_REQ_REDUCTION",
        
        # Search/selection effects
        "LOOK_AND_CHOOSE": "DECK_SEARCH",
        "LOOK_AND_CHOOSE_REVEAL": "DECK_SEARCH",
        "LOOK_AND_CHOOSE_ORDER": "DECK_SEARCH",
        "SELECT_MODE": "MODAL_CHOICE",
        "REVEAL_UNTIL": "DECK_SEARCH",
        
        # Movement effects
        "MOVE_TO_DECK": "DISCARD_DELTA",
        "MOVE_TO_DISCARD": "DISCARD_DELTA",
        
        # Buff effects
        "BUFF_POWER": "POWER_DELTA",
        "CHEER_REVEAL": "CHEER_REVEAL",
        
        # Cost effects
        "REDUCE_COST": "COST_REDUCTION",
        
        # Prevention effects
        "PREVENT_ACTIVATE": "PREVENT_ACTIVATE",
        "PREVENT_BATON_TOUCH": "PREVENT_BATON_TOUCH",
        "PREVENT_SUCCESS_PILE_SET": "PREVENT_SUCCESS_PILE_SET",
        
        # Other effects
        "SWAP_AREA": "SWAP_AREA",
        "FORMATION_CHANGE": "FORMATION_CHANGE",
        "TRANSFORM_COLOR": "TRANSFORM_COLOR",
    }
    
    # Cost mapping
    COST_TO_DELTA = {
        "DISCARD_HAND": "HAND_DISCARD",
        "PAY_ENERGY": "ENERGY_COST",
        "TAP_MEMBER": "MEMBER_TAP_DELTA",
        "MOVE_TO_DECK": "DISCARD_DELTA",
        "MOVE_TO_DISCARD": "DISCARD_DELTA",
    }
    
    # Dynamic value handling
    DYNAMIC_VALUES = {
        "COUNT_STAGE": "DYNAMIC:stage_count",
        "COUNT_SUCCESS_LIVE": "DYNAMIC:success_live_count",
        "COUNT_HAND": "DYNAMIC:hand_count",
        "COUNT_DISCARD": "DYNAMIC:discard_count",
        "COUNT_OPPONENT_WAIT": "DYNAMIC:opponent_wait_count",
        "ALL": "ALL",
        "99": "ALL",
    }

    def __init__(self, pseudocode_path=None, cards_path=None):
        if pseudocode_path is None:
            pseudocode_path = "data/manual_pseudocode.json"
        
        self.pseudocode = {}
        if os.path.exists(pseudocode_path):
            with open(pseudocode_path, "r", encoding="utf-8") as f:
                self.pseudocode = json.load(f)
        
        if cards_path is None:
            cards_path = "data/cards.json"
        
        self.cards = {}
        if os.path.exists(cards_path):
            with open(cards_path, "r", encoding="utf-8") as f:
                cards_data = json.load(f)
                if isinstance(cards_data, dict):
                    self.cards = cards_data
                else:
                    for card in cards_data:
                        card_no = card.get("card_no", "")
                        if card_no:
                            self.cards[card_no] = card

    def parse_value(self, value_str: str):
        """Parse a value that could be dynamic or numeric."""
        if not value_str:
            return 1
        
        value_str = value_str.strip()
        
        if value_str in self.DYNAMIC_VALUES:
            return self.DYNAMIC_VALUES[value_str]
        
        try:
            return int(value_str)
        except ValueError:
            return value_str

    def parse_pseudocode(self, pseudocode_str: str) -> list:
        """Parse a pseudocode string into a list of abilities."""
        abilities = []
        
        # Split by TRIGGER: to get individual ability blocks
        trigger_blocks = re.split(r'(?=TRIGGER:)', pseudocode_str)
        
        for block in trigger_blocks:
            block = block.strip()
            if not block:
                continue
            
            # Handle multiple triggers on same block (e.g., "TRIGGER: ON_PLAY\nTRIGGER: ON_LIVE_START")
            multi_trigger_match = re.findall(r'TRIGGER:\s*(\w+(?:_\w+)*)', block)
            
            if len(multi_trigger_match) > 1:
                # Multiple triggers - create separate abilities for each
                for trigger in multi_trigger_match:
                    # Remove other TRIGGER lines for this iteration
                    single_block = re.sub(r'TRIGGER:\s*\w+(?:_\w+)*\n', '', block, count=0)
                    single_block = f"TRIGGER: {trigger}\n{single_block}"
                    ability = self.parse_ability_block(single_block)
                    if ability:
                        abilities.append(ability)
            else:
                ability = self.parse_ability_block(block)
                if ability:
                    abilities.append(ability)
        
        return abilities

    def parse_ability_block(self, block: str) -> dict:
        """Parse a single ability block."""
        trigger_match = re.match(r'TRIGGER:\s*(\w+(?:_\w+)*)', block)
        if not trigger_match:
            return None
        
        raw_trigger = trigger_match.group(1)
        trigger_type = self.TRIGGER_MAP.get(raw_trigger, raw_trigger)
        
        is_optional = "(Optional)" in block or "Optional" in block
        once_per_turn = "(Once per turn)" in block or "Once per turn" in block
        
        conditions = self.extract_conditions(block)
        costs = self.extract_costs(block)
        effects = self.extract_effects(block)
        modal_options = self.extract_modal_options(block)
        
        sequence = []
        
        for cost in costs:
            sequence.append({
                "text": f"COST: {cost['type']}({cost['value']})",
                "deltas": [{"tag": cost['delta_tag'], "value": cost['value']}]
            })
        
        for effect in effects:
            delta_entry = {
                "text": f"EFFECT: {effect['type']}({effect['value']})",
                "deltas": [{"tag": effect['delta_tag'], "value": effect['value']}]
            }
            if effect.get('filter'):
                delta_entry['filter'] = effect['filter']
            if effect.get('modifier'):
                delta_entry['modifier'] = effect['modifier']
            sequence.append(delta_entry)
        
        result = {
            "trigger": trigger_type,
            "sequence": sequence,
            "optional": is_optional,
            "once_per_turn": once_per_turn
        }
        
        if conditions:
            result['conditions'] = conditions
        
        if modal_options:
            result['modal_options'] = modal_options
        
        return result

    def extract_conditions(self, block: str) -> list:
        """Extract condition information from block."""
        conditions = []
        
        cond_match = re.search(r'CONDITION:\s*(.+?)(?=\nCOST:|\nEFFECT:|\nTRIGGER:|\Z)', block, re.DOTALL)
        if cond_match:
            cond_text = cond_match.group(1).strip()
            conditions.append({
                "type": "PRECONDITION",
                "expression": cond_text
            })
        
        return conditions

    def extract_costs(self, block: str) -> list:
        """Extract cost information from block."""
        costs = []
        
        cost_match = re.search(r'COST:\s*(.+?)(?=\nEFFECT:|\nTRIGGER:|\nCONDITION:|\Z)', block, re.DOTALL)
        if not cost_match:
            return costs
        
        cost_text = cost_match.group(1)
        
        for effect_name, delta_tag in self.COST_TO_DELTA.items():
            pattern = rf'{effect_name}\(([^)]+)\)'
            match = re.search(pattern, cost_text)
            if match:
                value = self.parse_value(match.group(1))
                costs.append({
                    "type": effect_name,
                    "value": value,
                    "delta_tag": delta_tag
                })
        
        energy_icons = cost_text.count("icon_energy")
        if energy_icons > 0:
            costs.append({
                "type": "PAY_ENERGY",
                "value": energy_icons,
                "delta_tag": "ENERGY_COST"
            })
        
        if "TAP_MEMBER" in cost_text and not re.search(r'TAP_MEMBER\([^)]+\)', cost_text):
            costs.append({
                "type": "TAP_MEMBER",
                "value": 1,
                "delta_tag": "MEMBER_TAP_DELTA"
            })
        
        if "MOVE_TO_DISCARD" in cost_text:
            costs.append({
                "type": "MOVE_TO_DISCARD",
                "value": 1,
                "delta_tag": "DISCARD_DELTA"
            })
        
        return costs

    def extract_effects(self, block: str) -> list:
        """Extract effect information from block."""
        effects = []
        
        # Remove OPTION blocks to avoid duplicate parsing
        clean_block = re.sub(r'OPTION:.*?(?=OPTION:|\Z)', '', block, flags=re.DOTALL)
        
        # Find all EFFECT: patterns
        # Handle semicolon-separated effects: EFFECT: DRAW(1); DISCARD_HAND(1)
        effect_section = re.search(r'EFFECT:\s*(.+?)(?=\nTRIGGER:|\nOPTION:|\Z)', clean_block, re.DOTALL)
        
        if effect_section:
            effect_text = effect_section.group(1)
            
            # Split by semicolons for multiple effects
            effect_parts = re.split(r';\s*', effect_text)
            
            for part in effect_parts:
                part = part.strip()
                if not part:
                    continue
                    
                # Match EFFECT_NAME(value) or just EFFECT_NAME
                match = re.match(r'([A-Z_]+)(?:\(([^)]+)\))?', part)
                if match:
                    effect_name = match.group(1)
                    if effect_name in ['EFFECT', 'FILTER', 'OPTION']:
                        continue
                    
                    value = self.parse_value(match.group(2)) if match.group(2) else 1
                    delta_tag = self.EFFECT_TO_DELTA.get(effect_name, effect_name)
                    
                    effect_entry = {
                        "type": effect_name,
                        "value": value,
                        "delta_tag": delta_tag
                    }
                    
                    # Extract filter
                    filter_match = re.search(r'\{FILTER="([^"]+)"\}', part)
                    if filter_match:
                        effect_entry['filter'] = filter_match.group(1)
                    
                    # Extract modifiers like PER_CARD, HEART_TYPE
                    per_card_match = re.search(r'\{PER_CARD="([^"]+)"\}', part)
                    if per_card_match:
                        effect_entry['modifier'] = {"PER_CARD": per_card_match.group(1)}
                    
                    heart_type_match = re.search(r'\{HEART_TYPE=(\d+)\}', part)
                    if heart_type_match:
                        effect_entry['modifier'] = {"HEART_TYPE": int(heart_type_match.group(1))}
                    
                    effects.append(effect_entry)
        
        return effects

    def extract_modal_options(self, block: str) -> list:
        """Extract modal options from SELECT_MODE blocks."""
        options = []
        
        if "SELECT_MODE" not in block:
            return options
        
        option_matches = re.finditer(r'OPTION:\s*([^|]+)\|\s*EFFECT:\s*(.+?)(?=\n\s*OPTION:|\n\s*EFFECT:|\nTRIGGER:|\Z)', block, re.DOTALL)
        
        for match in option_matches:
            option_name = match.group(1).strip()
            option_effects_text = match.group(2).strip()
            
            option_effects = []
            
            # Split by semicolons
            effect_parts = re.split(r';\s*', option_effects_text)
            
            for part in effect_parts:
                part = part.strip()
                if not part:
                    continue
                    
                eff_match = re.match(r'([A-Z_]+)(?:\(([^)]+)\))?', part)
                if eff_match:
                    effect_name = eff_match.group(1)
                    if effect_name in ['EFFECT', 'FILTER']:
                        continue
                    
                    value = self.parse_value(eff_match.group(2)) if eff_match.group(2) else 1
                    delta_tag = self.EFFECT_TO_DELTA.get(effect_name, effect_name)
                    
                    option_effects.append({
                        "type": effect_name,
                        "value": value,
                        "delta_tag": delta_tag
                    })
            
            if option_effects:
                options.append({
                    "name": option_name,
                    "effects": option_effects
                })
        
        return options

    def interpret_card(self, card_no: str) -> dict:
        """Interpret a card's pseudocode into semantic expectations."""
        if card_no not in self.pseudocode:
            return {"id": card_no, "abilities": []}
        
        pseudocode_str = self.pseudocode[card_no].get("pseudocode", "")
        if not pseudocode_str:
            return {"id": card_no, "abilities": []}
        
        abilities = self.parse_pseudocode(pseudocode_str)
        
        return {
            "id": card_no,
            "abilities": abilities
        }

    def generate_truth(self) -> dict:
        """Generate semantic truth for all cards with pseudocode."""
        truth_db = {}
        
        for card_no in self.pseudocode:
            try:
                interpretation = self.interpret_card(card_no)
                if interpretation["abilities"]:
                    truth_db[card_no] = interpretation
            except Exception as e:
                print(f"Error processing {card_no}: {e}")
        
        return truth_db


def main():
    print("🚀 Generating Semantic Truth from Pseudocode (v3)...")
    
    oracle = PseudocodeOracle()
    truth_db = oracle.generate_truth()
    
    print(f"📊 Generated truth for {len(truth_db)} cards")
    
    output_path = "reports/semantic_truth_v3.json"
    os.makedirs("reports", exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(truth_db, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_path}")
    
    if truth_db:
        sample_key = list(truth_db.keys())[0]
        print(f"\nSample ({sample_key}):")
        print(json.dumps(truth_db[sample_key], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
