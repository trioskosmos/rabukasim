import random
from typing import Any, Dict, List, Optional

from engine.game.game_state import GameState
from engine.game.serializer import serialize_state

try:
    from engine.game.state_utils import create_uid
except ImportError:
    # Fallback if state_utils was deleted (it shouldn't have been, but just in case)
    # Reimplement create_uid if needed, or fix the file location
    BASE_ID_MASK = 0xFFFFF
    INSTANCE_SHIFT = 20

    def create_uid(base_id: int, instance_index: int) -> int:
        return (base_id & BASE_ID_MASK) | (instance_index << INSTANCE_SHIFT)


def optimize_history(
    history: List[Dict[str, Any]],
    member_db: Dict[int, Any],
    live_db: Dict[int, Any],
    energy_db: Dict[int, Any],
    exclude_db_cards: bool = True,
    seed: Optional[int] = None,
    action_log: Optional[List[int]] = None,
    deck_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Optimize replay history.
    Args:
        history: List of states
        member_db: Database of member cards
        live_db: Database of live cards
        energy_db: Database of energy cards
        exclude_db_cards: Use DB-backed optimization (Level 2)
        seed: Random seed (Level 3)
        action_log: List of action IDs (Level 3)
        deck_info: Dict with 'p0_deck', 'p1_deck', etc. (Level 3)
    """
    # Level 3: Action-Based Replay (Max Compression)
    if seed is not None and action_log is not None and deck_info is not None:
        return {
            "level": 3,
            "seed": seed,
            "decks": deck_info,
            "action_log": action_log,
            # We don't save 'states' or 'registry' at all!
        }

    # Level 2: State-Based DB-Backed
    registry = {}

    def extract_static_data(card_data):
        """Extract static fields that don't change during gameplay."""
        if not isinstance(card_data, dict):
            return {}

        # known static fields
        static_fields = [
            "name",
            "card_no",
            "type",
            "cost",
            "blade",
            "img",
            "hearts",
            "blade_hearts",
            "text",
            "score",
            "required_hearts",
        ]

        return {k: card_data[k] for k in static_fields if k in card_data}

    def optimize_object(obj):
        """recursively traverse and optimize payload."""
        if isinstance(obj, list):
            return [optimize_object(x) for x in obj]
        elif isinstance(obj, dict):
            # Check if this object looks like a serialized card
            if "id" in obj and ("name" in obj or "type" in obj):
                cid = obj["id"]
                # If it's a known card (positive ID), register it
                if isinstance(cid, int) and cid >= 0:
                    is_in_db = cid in member_db or cid in live_db or cid in energy_db

                    # Decide whether to add to registry
                    should_register = False
                    if not is_in_db:
                        should_register = True
                    elif not exclude_db_cards:
                        should_register = True

                    if should_register:
                        if cid not in registry:
                            registry[cid] = extract_static_data(obj)

                        # Return ONLY dynamic data + ID reference
                        dynamic_data = {"id": cid}
                        static_keys = registry[cid].keys()
                        for k, v in obj.items():
                            if k not in static_keys and k != "id":
                                dynamic_data[k] = optimize_object(v)
                        return dynamic_data

                    elif is_in_db:
                        # IT IS IN DB and we exclude it from registry
                        # We still strip static data, but we don't save it to file
                        # effectively assuming "registry[cid]" exists implicitly in DB

                        # We need to know which keys are static to strip them
                        # We can use a representative static extraction
                        static_keys = extract_static_data(obj).keys()

                        dynamic_data = {"id": cid}
                        for k, v in obj.items():
                            if k not in static_keys and k != "id":
                                dynamic_data[k] = optimize_object(v)
                        return dynamic_data

            # Regular dict recursion
            return {k: optimize_object(v) for k, v in obj.items()}
        else:
            return obj

    optimized_states = optimize_object(history)

    return {"registry": registry, "states": optimized_states}


def inflate_history(
    optimized_data: Dict[str, Any],
    member_db: Dict[int, Any],
    live_db: Dict[int, Any],
    energy_db: Dict[int, Any],
) -> List[Dict[str, Any]]:
    """
    Reconstruct full history state from optimized data using server DB.
    """
    # Level 3 Inflation (Action Log -> State History)
    if optimized_data.get("level") == 3 or "action_log" in optimized_data:
        print("Inflating Level 3 Action Log replay...")
        action_log = optimized_data.get("action_log", [])
        seed = optimized_data.get("seed", 0)
        deck_info = optimized_data.get("decks", {})

        # 1. Reset Game with Seed
        # Use local random instance to avoid messing with global random state if possible,
        # but GameState uses random module globally.
        # We must save and restore random state if we want to be clean, but python random is global.
        # Ideally GameState should use a random instance.
        # For now, we assume the caller handles global state implications or we just reset seed.

        # NOTE: This modifies global random state!
        random.seed(seed)

        # 2. Init Game State (Headless)
        GameState.member_db = member_db
        GameState.live_db = live_db
        # Energy DB is not static on GameState?
        GameState.energy_db = energy_db  # server.py sets this on instance or class?
        # server.py says: GameState.energy_db = energy_db

        # Create fresh state
        temp_gs = GameState()
        temp_gs.initialize_game()

        # Set decks if available
        if deck_info:
            p0_deck = deck_info.get("p0_deck")
            p1_deck = deck_info.get("p1_deck")

            if p0_deck and len(p0_deck) > 0:
                print(f"Loading custom deck for P0: {len(p0_deck)} cards")
                p0 = temp_gs.players[0]
                # Reset Deck & Hand
                p0.main_deck = [int(x) for x in p0_deck]
                p0.hand = []
                p0.discard = []
                # Draw initial hand (5 cards)
                draw_count = min(5, len(p0.main_deck))
                p0.hand = p0.main_deck[:draw_count]
                p0.hand_added_turn = [1] * draw_count
                p0.main_deck = p0.main_deck[draw_count:]

            if p1_deck and len(p1_deck) > 0:
                print(f"Loading custom deck for P1: {len(p1_deck)} cards")
                p1 = temp_gs.players[1]
                p1.main_deck = [int(x) for x in p1_deck]
                p1.hand = []
                p1.discard = []
                draw_count = min(5, len(p1.main_deck))
                p1.hand = p1.main_deck[:draw_count]
                p1.hand_added_turn = [1] * draw_count
                p1.main_deck = p1.main_deck[draw_count:]

        reconstructed_history = []

        # 3. Serialize Initial State
        reconstructed_history.append(serialize_state(temp_gs))

        # 4. Replay Actions
        for action_id in action_log:
            temp_gs.step(action_id)
            reconstructed_history.append(serialize_state(temp_gs))

        print(f"Reconstructed {len(reconstructed_history)} frames from {len(action_log)} actions.")
        return reconstructed_history

    # Level 2 Logic (State Inflation)
    registry = optimized_data.get("registry", {})
    states = optimized_data.get("states", [])

    def get_static_data(cid):
        """Get static data from Registry OR Database"""
        # 1. Registry (Custom cards / Legacy format)
        if str(cid) in registry:
            return registry[str(cid)]
        if cid in registry:
            return registry[cid]

        # 2. Database
        if cid in member_db:
            m = member_db[cid]
            # Reconstruct dictionary from object
            ability_text = getattr(m, "ability_text", "")
            if hasattr(m, "abilities") and m.abilities:
                # Use raw Japanese text
                # Clean wiki markup: {{icon.png|Text}} -> Text, [[Link|Text]] -> Text
                import re

                def clean_text(text):
                    text = re.sub(r"\{\{.*?\|(.*?)\}\}", r"\1", text)  # {{icon|Text}} -> Text
                    text = re.sub(r"\[\[.*?\|(.*?)\]\]", r"\1", text)  # [[Link|Text]] -> Text
                    return text

                ability_lines = [clean_text(ab.raw_text) for ab in m.abilities]
                ability_text = "\n".join(ability_lines)

            return {
                "name": m.name,
                "card_no": m.card_no,
                "type": "member",
                "cost": m.cost,
                "blade": m.blades,
                "img": m.img_path,
                "hearts": m.hearts.tolist(),
                "blade_hearts": m.blade_hearts.tolist(),
                "text": ability_text,
                "color": "Unknown",
            }
        elif cid in live_db:
            l = live_db[cid]
            ability_text = getattr(l, "ability_text", "")
            if hasattr(l, "abilities") and l.abilities:
                import re

                def clean_text(text):
                    text = re.sub(r"\{\{.*?\|(.*?)\}\}", r"\1", text)
                    text = re.sub(r"\[\[.*?\|(.*?)\]\]", r"\1", text)
                    return text

                ability_lines = [clean_text(ab.raw_text) for ab in l.abilities]
                ability_text = "\n".join(ability_lines)

            return {
                "name": l.name,
                "card_no": l.card_no,
                "type": "live",
                "score": l.score,
                "img": l.img_path,
                "required_hearts": l.required_hearts.tolist(),
                "text": ability_text,
            }
        elif cid in energy_db:
            # EnergyCard is simple (just ID), so we hardcode display info
            return {"name": "Energy", "type": "energy", "img": "assets/energy_card.png"}

        return None

    def inflate_object(obj):
        if isinstance(obj, list):
            return [inflate_object(x) for x in obj]
        elif isinstance(obj, dict):
            # Check for ID reference to inflate
            if "id" in obj:
                cid = obj["id"]
                static_data = get_static_data(cid)
                if static_data:
                    # Merge static data into this object (dynamic overrides static if conflict, though shouldn't happen)
                    # We create a new dict to Avoid mutating the source if it's reused
                    new_obj = static_data.copy()
                    for k, v in obj.items():
                        new_obj[k] = inflate_object(v)
                    return new_obj

            return {k: inflate_object(v) for k, v in obj.items()}
        else:
            return obj

    return inflate_object(states)
