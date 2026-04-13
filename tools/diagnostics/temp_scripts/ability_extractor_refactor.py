#!/usr/bin/env python3
"""Refactored ability extractor with clean hierarchical structure."""

import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum, auto

class OperationType(Enum):
    """Categorize operations for priority ordering."""
    CONDITION = auto()      # if, when, while, until
    COST = auto()           # pay, discard as cost
    CORE_ACTION = auto()    # draw, discard, add, move
    SELECTION = auto()      # select, choose, look at
    TARGETING = auto()      # tap, untap, activate
    RESOURCE = auto()      # hearts, blades, energy
    MODIFIER = auto()       # optional, reduce cost
    BRANCH = auto()         # choose one, options

@dataclass
class Operation:
    """Single extracted operation."""
    position: int
    text: str
    op_type: OperationType
    priority: int = 0  # Lower = higher priority

class AbilityExtractor:
    """Clean hierarchical ability extractor."""
    
    # Operation patterns organized by type
    PATTERNS = {
        OperationType.CONDITION: [
            # "～の場合" → if X
            (r"(.+?)の場合", lambda m: f"if {m.group(1)}"),
            # "～がいる場合" → if X exists
            (r"(.+?)がいる場合", lambda m: f"if {m.group(1)}"),
            # "～がある場合" → if X exists  
            (r"(.+?)がある場合", lambda m: f"if {m.group(1)}"),
            # "～枚以上ある場合" → if count >= N
            (r"(\d+)枚以上ある場合", lambda m: f"if count >= {m.group(1)}"),
        ],
        
        OperationType.CORE_ACTION: [
            # "カードをN枚引く" → draw N cards
            (r"カードを(\d+)枚引[くき]", 
             lambda m: f"draw {m.group(1)} card{'s' if m.group(1) != '1' else ''} from deck to hand"),
            
            # "デッキの上からカードをN枚控え室に置く" → discard N from deck
            (r"デッキの上からカードを(\d+)枚控え室に置く",
             lambda m: f"discard {m.group(1)} card{'s' if m.group(1) != '1' else ''} from deck to discard"),
            
            # Zone-specific discards
            (r"(手札|自分の手札)を(\d+)枚控え室に置く",
             lambda m: f"discard {m.group(2)} card{'s' if m.group(2) != '1' else ''} from hand to discard"),
            
            # "N枚手札に加える" → add N to hand
            (r"(\d+)枚手札に加え[るるか]",
             lambda m: f"add {m.group(1)} card{'s' if m.group(1) != '1' else ''} to hand"),
            
            # "手札をN枚デッキの一番下に置く" → move N from hand to bottom
            (r"手札を(\d+)枚デッキの一番下に置く",
             lambda m: f"move {m.group(1)} card{'s' if m.group(1) != '1' else ''} from hand to bottom of deck"),
        ],
        
        OperationType.SELECTION: [
            # "デッキの上からカードをN枚見る" → look at N from deck
            (r"デッキの上からカードを(\d+)枚見る",
             lambda m: f"look at {m.group(1)} cards from deck"),
        ],
        
        OperationType.TARGETING: [
            # "メンバーをウェイトにする" → tap member
            (r"メンバーをウェイトにする", lambda m: "tap member"),
            
            # "メンバーをアクティブにする" → untap member
            (r"メンバーをアクティブにする", lambda m: "untap member"),
        ],
        
        OperationType.RESOURCE: [
            # "ハートNを得る" → add N hearts
            (r"ハート(\d+)を得る", lambda m: f"add heart_{m.group(1).zfill(2)} to target"),
            
            # "ブレードNを得る" → add N blades
            (r"ブレード(\d+)を得る", lambda m: f"add {m.group(1)} blade{'s' if m.group(1) != '1' else ''} to target"),
        ],
        
        OperationType.BRANCH: [
            # "以下から1つを選ぶ。・option1・option2..."
            (r"以下から1つを選ぶ。((?:・[^・]+)+)", None),  # Complex, handled separately
        ],
    }
    
    def __init__(self, group_names: Dict[str, str], unit_names: Dict[str, str], 
                 character_names: Dict[str, str]):
        self.group_names = group_names
        self.unit_names = unit_names
        self.character_names = character_names
        
    def clean_text(self, text: str) -> str:
        """Pre-process JP text to remove encoding artifacts."""
        # Remove trigger icons
        text = re.sub(r'\{\{[^}]+\.png\|[^}]+\}\}', '', text)
        # Remove mojibake
        text = re.sub(r'[\u0300-\u036F]', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_operations(self, text: str) -> List[Operation]:
        """Extract all operations from text."""
        operations = []
        
        # Process each operation type
        for op_type, patterns in self.PATTERNS.items():
            for pattern, formatter in patterns:
                if formatter is None:
                    # Complex pattern, handle separately
                    continue
                    
                for match in re.finditer(pattern, text):
                    result = formatter(match)
                    # Clean the result (remove any JP that slipped through)
                    result = self._translate_fragments(result)
                    operations.append(Operation(
                        position=match.start(),
                        text=result,
                        op_type=op_type,
                        priority=self._get_priority(op_type)
                    ))
        
        # Sort by position then priority
        operations.sort(key=lambda x: (x.position, x.priority))
        return operations
    
    def _get_priority(self, op_type: OperationType) -> int:
        """Return priority for ordering. Lower = first."""
        priorities = {
            OperationType.CONDITION: 1,  # Conditions first
            OperationType.COST: 2,        # Costs second
            OperationType.CORE_ACTION: 3, # Actions third
            OperationType.SELECTION: 4,
            OperationType.TARGETING: 5,
            OperationType.RESOURCE: 6,
            OperationType.BRANCH: 7,
            OperationType.MODIFIER: 8,
        }
        return priorities.get(op_type, 99)
    
    def _translate_fragments(self, text: str) -> str:
        """Translate any remaining JP fragments in extracted text."""
        # Basic word translations
        translations = {
            '手札': 'hand',
            'デッキ': 'deck',
            '控え室': 'discard',
            'ステージ': 'stage',
            'メンバー': 'member',
            'カード': 'card',
        }
        for jp, en in translations.items():
            text = text.replace(jp, en)
        return text
    
    def to_logic(self, jp_text: str) -> str:
        """Convert JP text to logic string."""
        # Clean
        clean = self.clean_text(jp_text)
        
        # Extract
        operations = self.extract_operations(clean)
        
        # Format
        if not operations:
            return ""
        
        lines = [op.text for op in operations]
        return '\n'.join(lines)


# Example usage / test
if __name__ == "__main__":
    # Test data
    test_cases = [
        ("カードを2枚引く", "draw 2 cards from deck to hand"),
        ("手札を1枚控え室に置く", "discard 1 card from hand to discard"),
        ("メンバーをウェイトにする", "tap member"),
    ]
    
    extractor = AbilityExtractor({}, {}, {})
    
    for jp, expected in test_cases:
        result = extractor.to_logic(jp)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} JP: {jp[:40]}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        print()
