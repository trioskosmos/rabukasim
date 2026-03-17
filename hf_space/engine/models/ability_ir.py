from dataclasses import dataclass, field
from typing import Any, Dict, List

# ===== Bytecode Layout Versioning =====
# This section defines all supported bytecode layout versions.
# The current default is v1 (fixed 5-word chunks).
# Version gates allow safe expansion of bytecode layout.

# V1 Layout: Fixed 5-word chunks (32-bit each)
# - Word 0: Opcode (or negation flag + opcode)
# - Word 1: Value/count parameter
# - Word 2: Attribute low bits
# - Word 3: Attribute high bits
# - Word 4: Slot/zone encoding
BYTECODE_LAYOUT_VERSION = 1
BYTECODE_LAYOUT_NAME = "fixed5x32-v1"

# V2 Layout: Future-proof expansion (currently defined, not yet active)
# Reserve constants for v2 to allow gradual migration.
# When activated, v2 may expand certain fields or add inline metadata.
BYTECODE_LAYOUT_VERSION_V2 = 2
BYTECODE_LAYOUT_NAME_V2 = "fixed5x32-v2-extended"

# Semantic form version (independent of bytecode layout)
SEMANTIC_FORM_VERSION = 1

# Version gate: Support both v1 and v2 decoders
SUPPORTED_BYTECODE_VERSIONS = [BYTECODE_LAYOUT_VERSION, BYTECODE_LAYOUT_VERSION_V2]
SUPPORTED_SEMANTIC_VERSIONS = [SEMANTIC_FORM_VERSION]


@dataclass
class EffectIR:
    effect_type: str
    value: int = 0
    target: str = "SELF"
    params: Dict[str, Any] = field(default_factory=dict)
    conditions: List[str] = field(default_factory=list)
    is_optional: bool = False
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.effect_type,
            "value": self.value,
            "target": self.target,
            "params": self.params,
            "conditions": self.conditions,
            "optional": self.is_optional,
            "description": self.description,
        }


@dataclass
class ConditionIR:
    condition_type: str
    value: int = 0
    comparison: str = "GE"
    filter_summary: str = ""
    area: str = ""
    is_negated: bool = False
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.condition_type,
            "value": self.value,
            "comparison": self.comparison,
            "filter": self.filter_summary,
            "area": self.area,
            "negated": self.is_negated,
            "description": self.description,
        }


@dataclass
class CostIR:
    cost_type: str
    value: int = 0
    target: str = "SELF"
    filter_summary: str = ""
    is_optional: bool = False
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.cost_type,
            "value": self.value,
            "target": self.target,
            "filter": self.filter_summary,
            "optional": self.is_optional,
            "description": self.description,
        }


@dataclass
class AbilityIR:
    trigger: str
    effects: List[EffectIR] = field(default_factory=list)
    conditions: List[ConditionIR] = field(default_factory=list)
    costs: List[CostIR] = field(default_factory=list)
    is_once_per_turn: bool = False
    description: str = ""
    instructions_summary: str = ""
    semantic_version: int = SEMANTIC_FORM_VERSION
    bytecode_layout_version: int = BYTECODE_LAYOUT_VERSION
    bytecode_layout_name: str = BYTECODE_LAYOUT_NAME

    def to_dict(self) -> Dict[str, Any]:
        return {
            "semantic_version": self.semantic_version,
            "bytecode_layout_version": self.bytecode_layout_version,
            "bytecode_layout_name": self.bytecode_layout_name,
            "trigger": self.trigger,
            "effects": [e.to_dict() for e in self.effects],
            "conditions": [c.to_dict() for c in self.conditions],
            "costs": [c.to_dict() for c in self.costs],
            "once_per_turn": self.is_once_per_turn,
            "description": self.description,
            "instructions_summary": self.instructions_summary,
        }


SemanticEffect = EffectIR
SemanticCondition = ConditionIR
SemanticCost = CostIR
SemanticAbility = AbilityIR


# ===== Version Gate Functions =====
# These functions enable version-gated compilation and decoding.
# Use them when introducing new bytecode layouts or semantic form versions.

class VersionGate:
    """
    Version gate system for safe bytecode layout expansion.
    
    Allows compilation to use different bytecode versions while maintaining
    backward compatibility. Each version has its own decoder path.
    
    Example usage:
        # Use v2 layout for new compilations (v1 still default for now)
        gate = VersionGate(bytecode_version=2)
        if gate.should_use_v2_layout():
            # Compile with v2 layout
            ...
        
        # Always use v1 decoder for now
        if gate.should_decode_as_v1():
            # Use existing decoder logic
            ...
    """
    
    def __init__(self, bytecode_version: int = BYTECODE_LAYOUT_VERSION, 
                 semantic_version: int = SEMANTIC_FORM_VERSION):
        """
        Initialize version gate.
        
        Args:
            bytecode_version: Target bytecode layout version (default: v1)
            semantic_version: Target semantic form version (default: v1)
        """
        if bytecode_version not in SUPPORTED_BYTECODE_VERSIONS:
            raise ValueError(
                f"Unsupported bytecode version {bytecode_version}. "
                f"Supported: {SUPPORTED_BYTECODE_VERSIONS}"
            )
        if semantic_version not in SUPPORTED_SEMANTIC_VERSIONS:
            raise ValueError(
                f"Unsupported semantic version {semantic_version}. "
                f"Supported: {SUPPORTED_SEMANTIC_VERSIONS}"
            )
        
        self.bytecode_version = bytecode_version
        self.semantic_version = semantic_version
    
    def should_use_v1_layout(self) -> bool:
        """Check if this gate should use v1 bytecode layout."""
        return self.bytecode_version == BYTECODE_LAYOUT_VERSION
    
    def should_use_v2_layout(self) -> bool:
        """Check if this gate should use v2 bytecode layout (future extension)."""
        return self.bytecode_version == BYTECODE_LAYOUT_VERSION_V2
    
    def get_layout_name(self) -> str:
        """Get the bytecode layout name for this version."""
        if self.should_use_v2_layout():
            return BYTECODE_LAYOUT_NAME_V2
        return BYTECODE_LAYOUT_NAME
    
    def should_decode_as_v1(self) -> bool:
        """Check if decoder should use v1 logic."""
        return self.bytecode_version == BYTECODE_LAYOUT_VERSION
    
    def should_decode_as_v2(self) -> bool:
        """Check if decoder should use v2 logic (future extension)."""
        return self.bytecode_version == BYTECODE_LAYOUT_VERSION_V2


def create_ability_ir_with_version(
    trigger: str,
    effects: List[EffectIR] = None,
    conditions: List[ConditionIR] = None,
    costs: List[CostIR] = None,
    bytecode_version: int = BYTECODE_LAYOUT_VERSION,
    semantic_version: int = SEMANTIC_FORM_VERSION,
) -> AbilityIR:
    """
    Create an AbilityIR with explicit version specification.
    
    This factory function ensures version markers are set correctly when
    creating IR objects programmatically.
    
    Args:
        trigger: Ability trigger type (e.g., 'ON_PLAY', 'CONSTANT')
        effects: List of EffectIR objects (default: empty)
        conditions: List of ConditionIR objects (default: empty)
        costs: List of CostIR objects (default: empty)
        bytecode_version: Bytecode layout version (default: v1)
        semantic_version: Semantic form version (default: v1)
    
    Returns:
        AbilityIR with version markers set
    
    Raises:
        ValueError: If version is not supported
    """
    gate = VersionGate(bytecode_version, semantic_version)
    
    return AbilityIR(
        trigger=trigger,
        effects=effects or [],
        conditions=conditions or [],
        costs=costs or [],
        semantic_version=semantic_version,
        bytecode_layout_version=bytecode_version,
        bytecode_layout_name=gate.get_layout_name(),
    )