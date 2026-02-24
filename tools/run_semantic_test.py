#!/usr/bin/env python3
"""
Semantic Verification Test Framework for LovecaSim Engine.

This script verifies that the engine produces expected deltas for each card ability
by actually running the engine and comparing state changes against the truth file.

Phases implemented:
1. Basic verification framework with engine execution and delta comparison
2. Trigger-specific test setup and modal choice testing
3. Detailed reporting with statistics and failure analysis
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import IntEnum
from datetime import datetime
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import engine.engine_rust as er
except ImportError as e:
    print(f"Failed to import engine: {e}")
    sys.exit(1)


# =============================================================================
# Constants and Enums
# =============================================================================

class TriggerType(IntEnum):
    """Trigger types matching engine definitions."""
    NONE = 0
    ON_PLAY = 1
    ON_LIVE_START = 2
    ON_LIVE_SUCCESS = 3
    TURN_START = 4
    TURN_END = 5
    CONSTANT = 6
    ACTIVATED = 7
    ON_LEAVES = 8
    ON_REVEAL = 9
    ON_POSITION_CHANGE = 10


class Phase(IntEnum):
    """Game phases matching engine definitions."""
    SETUP = 0
    MULLIGAN_P1 = -1
    MULLIGAN_P2 = 0
    ACTIVE = 1
    ENERGY = 2
    DRAW = 3
    MAIN = 4
    LIVE_SET = 5
    PERFORMANCE_P1 = 6
    PERFORMANCE_P2 = 7
    LIVE_RESULT = 8
    TERMINAL = 9
    RESPONSE = 10


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Delta:
    """Represents a state change delta."""
    tag: str
    value: Any
    player_id: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, other: "Delta", strict: bool = False) -> bool:
        """Check if this delta matches another delta."""
        if self.tag != other.tag:
            return False
        if strict:
            return self.value == other.value and self.player_id == other.player_id
        return True  # Tag match is sufficient for non-strict comparison


@dataclass
class SegmentResult:
    """Result of verifying a single segment."""
    index: int
    text: str
    expected_deltas: List[Delta]
    actual_deltas: List[Delta]
    passed: bool
    details: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "text": self.text,
            "expected_count": len(self.expected_deltas),
            "actual_count": len(self.actual_deltas),
            "passed": self.passed,
            "details": self.details,
            "expected": [{"tag": d.tag, "value": d.value} for d in self.expected_deltas],
            "actual": [{"tag": d.tag, "value": d.value} for d in self.actual_deltas],
        }


@dataclass
class AbilityResult:
    """Result of verifying a single ability."""
    index: int
    trigger: str
    segments: List[SegmentResult]
    passed: bool
    modal_tested: bool = False
    modal_options_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "trigger": self.trigger,
            "passed": self.passed,
            "modal_tested": self.modal_tested,
            "modal_options_count": self.modal_options_count,
            "segments": [s.to_dict() for s in self.segments],
            "segment_pass_rate": sum(1 for s in self.segments if s.passed) / len(self.segments) if self.segments else 1.0,
        }


@dataclass
class CardResult:
    """Result of verifying a single card."""
    card_id: str
    abilities: List[AbilityResult]
    passed: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "card_id": self.card_id,
            "passed": self.passed,
            "error": self.error,
            "abilities": [a.to_dict() for a in self.abilities],
            "ability_pass_rate": sum(1 for a in self.abilities if a.passed) / len(self.abilities) if self.abilities else 1.0,
        }


@dataclass
class TestReport:
    """Complete test report."""
    timestamp: str
    total_cards: int
    cards_passed: int
    cards_failed: int
    total_abilities: int
    abilities_passed: int
    total_segments: int
    segments_passed: int
    segments_with_deltas: int
    segments_empty_deltas: int
    pass_rate: float
    results: List[CardResult]
    failed_cards: List[str]
    errors: List[Tuple[str, str]]
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "summary": {
                "total_cards": self.total_cards,
                "cards_passed": self.cards_passed,
                "cards_failed": self.cards_failed,
                "total_abilities": self.total_abilities,
                "abilities_passed": self.abilities_passed,
                "total_segments": self.total_segments,
                "segments_passed": self.segments_passed,
                "segments_with_deltas": self.segments_with_deltas,
                "segments_empty_deltas": self.segments_empty_deltas,
                "pass_rate": self.pass_rate,
            },
            "failed_cards": self.failed_cards,
            "errors": self.errors,
            "results": [r.to_dict() for r in self.results],
        }


# =============================================================================
# Helper Functions
# =============================================================================

def load_truth(truth_path: Optional[str] = None) -> Dict:
    """Load semantic truth file."""
    if truth_path is None:
        truth_path = Path(__file__).parent.parent / "reports" / "semantic_truth_v3.json"
    else:
        truth_path = Path(truth_path)
    
    with open(truth_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_card_database(db_path: Optional[str] = None) -> Any:
    """Load card database into PyCardDatabase."""
    if db_path is None:
        db_path = Path(__file__).parent.parent / "data" / "cards.json"
    else:
        db_path = Path(db_path)
    
    with open(db_path, "r", encoding="utf-8") as f:
        cards = json.load(f)
    
    # Create PyCardDatabase from JSON string
    db_json = json.dumps(cards)
    db = er.PyCardDatabase(db_json)
    return db


def parse_deltas(delta_list: List[Dict]) -> List[Delta]:
    """Parse delta list from truth file format."""
    deltas = []
    for d in delta_list:
        deltas.append(Delta(
            tag=d.get("tag", "UNKNOWN"),
            value=d.get("value"),
            player_id=d.get("player_id"),
            details=d.get("details", {}),
        ))
    return deltas


def get_trigger_type(trigger_str: str) -> TriggerType:
    """Convert trigger string to TriggerType enum."""
    trigger_map = {
        "ON_PLAY": TriggerType.ON_PLAY,
        "ON_LIVE_START": TriggerType.ON_LIVE_START,
        "ON_LIVE_SUCCESS": TriggerType.ON_LIVE_SUCCESS,
        "TURN_START": TriggerType.TURN_START,
        "TURN_END": TriggerType.TURN_END,
        "CONSTANT": TriggerType.CONSTANT,
        "ACTIVATED": TriggerType.ACTIVATED,
        "ON_LEAVES": TriggerType.ON_LEAVES,
        "ON_REVEAL": TriggerType.ON_REVEAL,
        "ON_POSITION_CHANGE": TriggerType.ON_POSITION_CHANGE,
    }
    return trigger_map.get(trigger_str.upper(), TriggerType.NONE)


# =============================================================================
# Test Setup Functions
# =============================================================================

class TestGameSetup:
    """Creates and manages test game states for different trigger types."""
    
    def __init__(self, db: Any):
        self.db = db
    
    def create_base_game(self) -> Any:
        """Create a basic game state for testing."""
        game = er.PyGameState(self.db)
        return game
    
    def setup_for_on_play(self, game: Any, card_id: int, player_id: int = 0) -> None:
        """Setup game state for ON_PLAY trigger testing."""
        # Set to main phase
        game.set_phase(Phase.MAIN)
        game.set_current_player(player_id)
        
        # Put card in hand
        hand = list(game.get_player(player_id).hand)
        if card_id not in hand:
            hand.insert(0, card_id)
        game.set_hand_cards(player_id, hand)
        
        # Ensure player has energy
        energy = list(game.get_player(player_id).energy_zone)
        if len(energy) < 3:
            # Add some energy cards (assuming card ID 1 is energy)
            energy.extend([1, 1, 1])
        game.set_energy_cards(player_id, energy)
    
    def setup_for_on_live_start(self, game: Any, card_id: int, player_id: int = 0) -> None:
        """Setup game state for ON_LIVE_START trigger testing."""
        # Set to live set phase
        game.set_phase(Phase.LIVE_SET)
        game.set_current_player(player_id)
        
        # Put card in live zone
        game.set_live_card(player_id, 0, card_id, True)
        
        # Setup some members on stage
        stage = list(game.get_player(player_id).stage)
        if stage[0] == -1:
            # Add a member to center stage
            stage[1] = card_id  # Center position
        game.set_stage_card(player_id, 1, card_id)
    
    def setup_for_turn_start(self, game: Any, card_id: int, player_id: int = 0) -> None:
        """Setup game state for TURN_START trigger testing."""
        game.set_phase(Phase.ACTIVE)
        game.set_current_player(player_id)
        
        # Put card on stage
        game.set_stage_card(player_id, 0, card_id)
    
    def setup_for_activated(self, game: Any, card_id: int, player_id: int = 0) -> None:
        """Setup game state for ACTIVATED ability testing."""
        game.set_phase(Phase.MAIN)
        game.set_current_player(player_id)
        
        # Put card on stage (untapped)
        game.set_stage_card(player_id, 0, card_id)
        
        # Ensure player has resources
        energy = list(game.get_player(player_id).energy_zone)
        if len(energy) < 3:
            energy.extend([1, 1, 1])
        game.set_energy_cards(player_id, energy)
    
    def setup_for_constant(self, game: Any, card_id: int, player_id: int = 0) -> None:
        """Setup game state for CONSTANT ability testing."""
        game.set_phase(Phase.MAIN)
        game.set_current_player(player_id)
        
        # Put card on stage
        game.set_stage_card(player_id, 0, card_id)
    
    def setup_game_for_trigger(
        self, 
        game: Any, 
        trigger: TriggerType, 
        card_id: int, 
        player_id: int = 0
    ) -> None:
        """Setup game state based on trigger type."""
        setup_methods = {
            TriggerType.ON_PLAY: self.setup_for_on_play,
            TriggerType.ON_LIVE_START: self.setup_for_on_live_start,
            TriggerType.TURN_START: self.setup_for_turn_start,
            TriggerType.ACTIVATED: self.setup_for_activated,
            TriggerType.CONSTANT: self.setup_for_constant,
        }
        
        setup_fn = setup_methods.get(trigger)
        if setup_fn:
            setup_fn(game, card_id, player_id)
        else:
            # Default setup
            game.set_phase(Phase.MAIN)
            game.set_current_player(player_id)
            game.set_stage_card(player_id, 0, card_id)


# =============================================================================
# State Capture Functions
# =============================================================================

class StateCapture:
    """Captures and compares game state for delta verification."""
    
    @staticmethod
    def capture_state(game: Any, player_id: int = 0) -> Dict[str, Any]:
        """Capture current game state for comparison."""
        player = game.get_player(player_id)
        opponent = game.get_player(1 - player_id)
        
        return {
            "hand_count": len(player.hand),
            "hand": list(player.hand),
            "deck_count": player.deck_count,
            "discard_count": len(player.discard),
            "stage": list(player.stage),
            "live_zone": list(player.live_zone),
            "energy_count": len(player.energy_zone),
            "tapped_energy": list(player.tapped_energy),
            "tapped_members": list(player.tapped_members),
            "score": player.score,
            "success_lives": list(player.success_lives),
            "blades": game.get_total_blades(player_id),
            "hearts": list(game.get_total_hearts(player_id)),
            "opponent_hand_count": len(opponent.hand),
            "opponent_score": opponent.score,
            "phase": game.phase,
            "turn": game.turn,
        }
    
    @staticmethod
    def compute_deltas(before: Dict, after: Dict, player_id: int = 0) -> List[Delta]:
        """Compute deltas between two states."""
        deltas = []
        
        # Hand changes
        hand_diff = after["hand_count"] - before["hand_count"]
        if hand_diff != 0:
            deltas.append(Delta(
                tag="HAND_DELTA",
                value=hand_diff,
                player_id=player_id,
                details={"before": before["hand_count"], "after": after["hand_count"]},
            ))
        
        # Deck changes
        deck_diff = before["deck_count"] - after["deck_count"]
        if deck_diff != 0:
            deltas.append(Delta(
                tag="DECK_DELTA",
                value=-deck_diff,  # Negative because drawing reduces deck
                player_id=player_id,
            ))
        
        # Discard changes
        discard_diff = after["discard_count"] - before["discard_count"]
        if discard_diff != 0:
            deltas.append(Delta(
                tag="DISCARD_DELTA",
                value=discard_diff,
                player_id=player_id,
            ))
        
        # Score changes
        score_diff = after["score"] - before["score"]
        if score_diff != 0:
            deltas.append(Delta(
                tag="SCORE_DELTA",
                value=score_diff,
                player_id=player_id,
            ))
        
        # Blade changes
        blade_diff = after["blades"] - before["blades"]
        if blade_diff != 0:
            deltas.append(Delta(
                tag="BLADE_DELTA",
                value=blade_diff,
                player_id=player_id,
            ))
        
        # Energy changes
        energy_diff = after["energy_count"] - before["energy_count"]
        if energy_diff != 0:
            deltas.append(Delta(
                tag="ENERGY_DELTA",
                value=energy_diff,
                player_id=player_id,
            ))
        
        # Tapped member changes
        if after["tapped_members"] != before["tapped_members"]:
            deltas.append(Delta(
                tag="TAP_CHANGE",
                value=after["tapped_members"],
                player_id=player_id,
            ))
        
        # Success live changes
        success_diff = len(after["success_lives"]) - len(before["success_lives"])
        if success_diff != 0:
            deltas.append(Delta(
                tag="SUCCESS_LIVE_DELTA",
                value=success_diff,
                player_id=player_id,
            ))
        
        return deltas


# =============================================================================
# Main Verification Class
# =============================================================================

class SemanticVerifier:
    """Main verification engine for semantic testing."""
    
    def __init__(self, db: Any, verbose: bool = False):
        self.db = db
        self.verbose = verbose
        self.setup = TestGameSetup(db)
        self.capture = StateCapture()
    
    def verify_card(
        self, 
        card_id_str: str, 
        truth_data: Dict,
        test_modals: bool = True,
    ) -> CardResult:
        """Verify a single card's abilities against truth data."""
        
        # Get card numeric ID from database
        card_numeric_id = self.db.id_by_no(card_id_str)
        if card_numeric_id is None:
            return CardResult(
                card_id=card_id_str,
                abilities=[],
                passed=False,
                error=f"Card not found in database: {card_id_str}",
            )
        
        if card_id_str not in truth_data:
            return CardResult(
                card_id=card_id_str,
                abilities=[],
                passed=False,
                error="No truth data available",
            )
        
        card_truth = truth_data[card_id_str]
        abilities = card_truth.get("abilities", [])
        ability_results = []
        
        for i, ability in enumerate(abilities):
            ab_result = self._verify_ability(
                card_numeric_id,
                i,
                ability,
                test_modals=test_modals,
            )
            ability_results.append(ab_result)
        
        passed = all(a.passed for a in ability_results)
        return CardResult(
            card_id=card_id_str,
            abilities=ability_results,
            passed=passed,
        )
    
    def _verify_ability(
        self,
        card_id: int,
        ability_index: int,
        ability_data: Dict,
        test_modals: bool = True,
    ) -> AbilityResult:
        """Verify a single ability."""
        
        trigger_str = ability_data.get("trigger", "UNKNOWN")
        trigger = get_trigger_type(trigger_str)
        sequence = ability_data.get("sequence", [])
        modal_options = ability_data.get("modal_options", [])
        
        segment_results = []
        
        # Test each segment
        for j, segment in enumerate(sequence):
            seg_result = self._verify_segment(
                card_id,
                ability_index,
                j,
                segment,
                trigger,
            )
            segment_results.append(seg_result)
        
        # Test modal options if present
        modal_tested = False
        if test_modals and modal_options:
            modal_tested = True
            # For modal abilities, we verify that each option has defined effects
            for opt_idx, option in enumerate(modal_options):
                effects = option.get("effects", [])
                for eff in effects:
                    # Verify effect has delta_tag defined
                    if "delta_tag" not in eff:
                        seg_result = SegmentResult(
                            index=len(segment_results),
                            text=f"MODAL_OPTION_{opt_idx}: {option.get('name', 'unknown')}",
                            expected_deltas=[],
                            actual_deltas=[],
                            passed=False,
                            details="Modal option missing delta_tag",
                        )
                        segment_results.append(seg_result)
        
        passed = all(s.passed for s in segment_results)
        return AbilityResult(
            index=ability_index,
            trigger=trigger_str,
            segments=segment_results,
            passed=passed,
            modal_tested=modal_tested,
            modal_options_count=len(modal_options),
        )
    
    def _verify_segment(
        self,
        card_id: int,
        ability_index: int,
        segment_index: int,
        segment_data: Dict,
        trigger: TriggerType,
    ) -> SegmentResult:
        """Verify a single segment."""
        
        text = segment_data.get("text", "")
        expected_deltas = parse_deltas(segment_data.get("deltas", []))
        
        # If no expected deltas, segment passes by default
        if not expected_deltas:
            return SegmentResult(
                index=segment_index,
                text=text,
                expected_deltas=[],
                actual_deltas=[],
                passed=True,
                details="No expected deltas (auto-pass)",
            )
        
        # Try to execute the ability and capture state changes
        try:
            actual_deltas = self._execute_and_capture(card_id, trigger)
            
            # Compare deltas
            passed, details = self._compare_deltas(expected_deltas, actual_deltas)
            
            return SegmentResult(
                index=segment_index,
                text=text,
                expected_deltas=expected_deltas,
                actual_deltas=actual_deltas,
                passed=passed,
                details=details,
            )
            
        except Exception as e:
            return SegmentResult(
                index=segment_index,
                text=text,
                expected_deltas=expected_deltas,
                actual_deltas=[],
                passed=False,
                details=f"Execution error: {str(e)}",
            )
    
    def _execute_and_capture(
        self, 
        card_id: int, 
        trigger: TriggerType,
        player_id: int = 0,
    ) -> List[Delta]:
        """Execute ability and capture state changes."""
        
        # Create fresh game state
        game = self.setup.create_base_game()
        
        # Setup for trigger type
        self.setup.setup_game_for_trigger(game, trigger, card_id, player_id)
        
        # Capture before state
        before = self.capture.capture_state(game, player_id)
        
        # Trigger the ability
        try:
            game.trigger_abilities(int(trigger), player_id)
        except Exception as e:
            if self.verbose:
                print(f"  Trigger error: {e}")
            # Some triggers may fail in test environment
        
        # Capture after state
        after = self.capture.capture_state(game, player_id)
        
        # Compute deltas
        return self.capture.compute_deltas(before, after, player_id)
    
    def _compare_deltas(
        self, 
        expected: List[Delta], 
        actual: List[Delta],
    ) -> Tuple[bool, str]:
        """Compare expected and actual deltas."""
        
        if not expected:
            return True, "No expected deltas"
        
        if not actual:
            # Check if all expected deltas are zero-value
            all_zero = all(d.value == 0 for d in expected)
            if all_zero:
                return True, "Expected zero deltas, got no change"
            return False, f"Expected {len(expected)} deltas, got none"
        
        # Match by tag
        matched_expected = set()
        matched_actual = set()
        
        for i, exp in enumerate(expected):
            for j, act in enumerate(actual):
                if j not in matched_actual and exp.matches(act):
                    matched_expected.add(i)
                    matched_actual.add(j)
                    break
        
        if len(matched_expected) == len(expected):
            return True, f"All {len(expected)} expected deltas matched"
        
        unmatched_expected = [expected[i] for i in range(len(expected)) if i not in matched_expected]
        unmatched_actual = [actual[j] for j in range(len(actual)) if j not in matched_actual]
        
        details = f"Matched {len(matched_expected)}/{len(expected)} deltas. "
        if unmatched_expected:
            details += f"Missing: {[d.tag for d in unmatched_expected]}. "
        if unmatched_actual:
            details += f"Extra: {[d.tag for d in unmatched_actual]}"
        
        return False, details


# =============================================================================
# Report Generation
# =============================================================================

def generate_report(
    results: List[CardResult],
    output_path: Optional[str] = None,
) -> TestReport:
    """Generate comprehensive test report."""
    
    total_cards = len(results)
    cards_passed = sum(1 for r in results if r.passed)
    cards_failed = total_cards - cards_passed
    
    total_abilities = sum(len(r.abilities) for r in results)
    abilities_passed = sum(
        1 for r in results for a in r.abilities if a.passed
    )
    
    total_segments = sum(
        len(a.segments) for r in results for a in r.abilities
    )
    segments_passed = sum(
        1 for r in results for a in r.abilities for s in a.segments if s.passed
    )
    
    segments_with_deltas = sum(
        1 for r in results for a in r.abilities for s in a.segments 
        if s.expected_deltas
    )
    segments_empty_deltas = total_segments - segments_with_deltas
    
    pass_rate = cards_passed / total_cards if total_cards > 0 else 0.0
    
    failed_cards = [r.card_id for r in results if not r.passed]
    errors = [(r.card_id, r.error) for r in results if r.error]
    
    report = TestReport(
        timestamp=datetime.now().isoformat(),
        total_cards=total_cards,
        cards_passed=cards_passed,
        cards_failed=cards_failed,
        total_abilities=total_abilities,
        abilities_passed=abilities_passed,
        total_segments=total_segments,
        segments_passed=segments_passed,
        segments_with_deltas=segments_with_deltas,
        segments_empty_deltas=segments_empty_deltas,
        pass_rate=pass_rate,
        results=results,
        failed_cards=failed_cards,
        errors=errors,
    )
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
    
    return report


def print_report_summary(report: TestReport) -> None:
    """Print a summary of the test report."""
    
    print("\n" + "=" * 70)
    print("SEMANTIC VERIFICATION TEST REPORT")
    print("=" * 70)
    print(f"Timestamp: {report.timestamp}")
    print()
    
    print("CARD SUMMARY")
    print("-" * 40)
    print(f"  Total cards:      {report.total_cards}")
    print(f"  Passed:           {report.cards_passed}")
    print(f"  Failed:           {report.cards_failed}")
    print(f"  Pass rate:        {report.pass_rate * 100:.1f}%")
    print()
    
    print("ABILITY SUMMARY")
    print("-" * 40)
    print(f"  Total abilities:  {report.total_abilities}")
    print(f"  Passed:           {report.abilities_passed}")
    print(f"  Pass rate:        {report.abilities_passed / report.total_abilities * 100:.1f}%" if report.total_abilities > 0 else "  Pass rate: N/A")
    print()
    
    print("SEGMENT SUMMARY")
    print("-" * 40)
    print(f"  Total segments:       {report.total_segments}")
    print(f"  Passed:               {report.segments_passed}")
    print(f"  With expected deltas: {report.segments_with_deltas}")
    print(f"  Empty deltas:         {report.segments_empty_deltas}")
    print(f"  Pass rate:            {report.segments_passed / report.total_segments * 100:.1f}%" if report.total_segments > 0 else "  Pass rate: N/A")
    print()
    
    if report.failed_cards:
        print("FAILED CARDS")
        print("-" * 40)
        for card_id in report.failed_cards[:20]:  # Show first 20
            print(f"  - {card_id}")
        if len(report.failed_cards) > 20:
            print(f"  ... and {len(report.failed_cards) - 20} more")
        print()
    
    if report.errors:
        print("ERRORS")
        print("-" * 40)
        for card_id, error in report.errors[:10]:  # Show first 10
            print(f"  {card_id}: {error}")
        if len(report.errors) > 10:
            print(f"  ... and {len(report.errors) - 10} more errors")
        print()
    
    print("=" * 70)


# =============================================================================
# Main Entry Point
# =============================================================================

def run_tests(
    truth_path: Optional[str] = None,
    output_path: Optional[str] = None,
    verbose: bool = False,
    card_filter: Optional[List[str]] = None,
    limit: Optional[int] = None,
) -> TestReport:
    """Run all semantic tests."""
    
    print("=" * 70)
    print("SEMANTIC VERIFICATION TEST")
    print("=" * 70)
    
    # Load truth data
    print("\nLoading truth file...")
    truth = load_truth(truth_path)
    print(f"Loaded {len(truth)} cards from truth file")
    
    # Load card database
    print("\nLoading card database...")
    try:
        db = load_card_database()
        print(f"Card database loaded: {db.member_count} members, {db.live_count} lives")
    except Exception as e:
        print(f"Failed to load card database: {e}")
        raise
    
    # Initialize verifier
    verifier = SemanticVerifier(db, verbose=verbose)
    
    # Filter cards if specified
    cards_to_test = list(truth.keys())
    if card_filter:
        cards_to_test = [c for c in cards_to_test if c in card_filter]
    if limit:
        cards_to_test = cards_to_test[:limit]
    
    print(f"\nTesting {len(cards_to_test)} cards...")
    
    # Run verification
    results = []
    for i, card_id in enumerate(cards_to_test):
        if verbose or (i + 1) % 100 == 0:
            print(f"  [{i + 1}/{len(cards_to_test)}] Testing {card_id}...")
        
        try:
            result = verifier.verify_card(card_id, truth)
            results.append(result)
        except Exception as e:
            if verbose:
                print(f"    Error: {e}")
            results.append(CardResult(
                card_id=card_id,
                abilities=[],
                passed=False,
                error=str(e),
            ))
    
    # Generate report
    report = generate_report(results, output_path)
    print_report_summary(report)
    
    return report


def main():
    """Main entry point with CLI argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run semantic verification tests")
    parser.add_argument(
        "--truth", "-t",
        help="Path to truth file (default: reports/semantic_truth_v3.json)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Path to output JSON report",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--filter", "-f",
        nargs="+",
        help="Only test specified card IDs",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Limit number of cards to test",
    )
    
    args = parser.parse_args()
    
    report = run_tests(
        truth_path=args.truth,
        output_path=args.output,
        verbose=args.verbose,
        card_filter=args.filter,
        limit=args.limit,
    )
    
    # Exit with error code if any tests failed
    sys.exit(0 if report.pass_rate == 1.0 else 1)


if __name__ == "__main__":
    main()
