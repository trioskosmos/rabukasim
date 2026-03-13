"""
Flask Backend for Love Live Card Game Web UI
"""

import json
import os
import random
import sys
import threading
import uuid
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from flask import Flask, jsonify, request, send_from_directory
from flask.json.provider import DefaultJSONProvider

# Ensure project root is in sys.path for absolute imports
if getattr(sys, "frozen", False):
    PROJECT_ROOT = sys._MEIPASS  # type: ignore
    CURRENT_DIR = os.path.join(PROJECT_ROOT, "backend")
else:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Rust Engine
import engine_rust

try:
    from ai.headless_runner import RandomAgent, create_easy_cards
    from ai.headless_runner import SmartHeuristicAgent as SmartAgent

    AI_AVAILABLE = True
except ImportError:
    print("Warning: AI modules not found. AI features will be disabled.")
    AI_AVAILABLE = False

    class RandomAgent:
        pass

    class SmartAgent:
        pass

    def create_easy_cards():
        return None, None


from engine.game.data_loader import CardDataLoader
from engine.game.deck_utils import UnifiedDeckParser
from engine.game.desc_utils import get_action_desc
from engine.game.enums import Phase
from engine.game.game_state import GameState
from engine.game.replay_manager import inflate_history, optimize_history
from engine.game.serializer import serialize_state
from engine.game.state_utils import create_uid

try:
    from rust_serializer import RustCompatGameState, RustGameStateSerializer
except ImportError:
    from backend.rust_serializer import RustCompatGameState, RustGameStateSerializer

INSTANCE_SHIFT = 20
BASE_ID_MASK = 0xFFFFF

# --- MODULE DIRECTORIES ---
ENGINE_DIR = os.path.join(PROJECT_ROOT, "engine")
AI_DIR = os.path.join(PROJECT_ROOT, "ai")
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Tools imports (optional)
try:
    from tools.deck_extractor import extract_deck_data
except ImportError:
    print("Warning: Could not import deck_extractor from tools.")

    def extract_deck_data(content, db):
        return [], [], {}, ["Importer not found"]


# Static folder is now in frontend/web_ui
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

WEB_UI_DIR = os.path.join(FRONTEND_DIR, "web_ui")
IMG_DIR = os.path.join(FRONTEND_DIR, "img")  # Images seem to be in frontend/img
# Note: frontend/web_ui has its own js/css folders which index.html likely uses


app = Flask(__name__, static_folder=WEB_UI_DIR)


class NumpyJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


app.json = NumpyJSONProvider(app)


@app.route("/img/<path:filename>")
def serve_img(filename):
    # Sanitize and normalize the filename
    filename = filename.replace("\\", "/").lstrip("/")

    # Check if this is a card image request
    if filename.startswith("cards/") or filename.startswith("cards_webp/"):
        # Remove old nested 'cards/' prefix if it's there
        pure_filename = os.path.basename(filename)
        webp_path = os.path.join(IMG_DIR, "cards_webp", pure_filename)

        # Priority 1: Flat WebP folder
        if os.path.exists(webp_path) and os.path.isfile(webp_path):
            return send_from_directory(os.path.join(IMG_DIR, "cards_webp"), pure_filename)

        # Priority 2: Try falling back to original nested PNGs for backward compatibility/backup
        # (This is mostly for non-compiled access or manual links)
        pass

    # Define possible search directories relative to PROJECT_ROOT
    search_dirs = [
        os.path.join(IMG_DIR, "cards_webp"),  # Flattened WebP first
        IMG_DIR,  # frontend/img
        os.path.join(IMG_DIR, "texticon"),  # frontend/img/texticon
        os.path.join(WEB_UI_DIR, "img"),  # frontend/web_ui/img
        FRONTEND_DIR,  # Allow direct frontend access if needed
    ]

    for base_dir in search_dirs:
        full_path = os.path.join(base_dir, filename)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_from_directory(base_dir, filename)

        # Fallback for .webp requesting .png or vice-versa
        if filename.endswith(".webp"):
            png_fallback = filename[:-5] + ".png"
            full_png_path = os.path.join(base_dir, png_fallback)
            if os.path.exists(full_png_path) and os.path.isfile(full_png_path):
                return send_from_directory(base_dir, png_fallback)

    # Extra fallback for common icons if they are misplaced
    if filename == "icon_blade.png" or "icon_blade" in filename:
        # Try to find it anywhere in frontend/img
        for root, dirs, files in os.walk(IMG_DIR):
            if "icon_blade.png" in files:
                return send_from_directory(root, "icon_blade.png")

    print(f"DEBUG_IMG_404: Could not find {filename} in {search_dirs}")
    return "Image not found", 404


@app.route("/icon_blade.png")
def serve_icon_root():
    return serve_img("icon_blade.png")


# ai_agent = SmartHeuristicAgent()
ai_agent = SmartAgent()  # Use original heuristic AI

# Global game state
# Room Registry
ROOMS: dict[str, dict[str, Any]] = {}
game_lock = threading.Lock()

# Room cleanup configuration
ROOM_INACTIVE_TIMEOUT_MINUTES = 30  # Remove rooms inactive for 30 minutes
ROOM_CLEANUP_INTERVAL = 60  # Run cleanup every 60 seconds (loops)

# Rust Card DB (Global Singleton for performance)
RUST_DB = None
RUST_DB_VANILLA = None
try:
    compiled_data_path = os.path.join(DATA_DIR, "cards_compiled.json")
    with open(compiled_data_path, "r", encoding="utf-8") as f:
        RUST_DB = engine_rust.PyCardDatabase(f.read())
except Exception as e:
    print(f"Warning: Failed to load RUST_DB from {compiled_data_path}: {e}")

try:
    vanilla_data_path = os.path.join(DATA_DIR, "cards_vanilla.json")
    with open(vanilla_data_path, "r", encoding="utf-8") as f:
        RUST_DB_VANILLA = engine_rust.PyCardDatabase(f.read())
except Exception as e:
    print(f"Warning: Failed to load RUST_DB_VANILLA from {vanilla_data_path}: {e}")


# Python DBs (for metadata/serialization)
member_db: dict[int, Any] = {}
live_db: dict[int, Any] = {}
energy_db: dict[int, Any] = {}

rust_serializer = None  # Initialized after data load
game_history: list[dict] = []  # Global replay history (might need per-room later)

# Legacy custom deck globals (used by init_game)
custom_deck_p0: list[str] | None = None
custom_deck_p1: list[str] | None = None
custom_energy_deck_p0: list[str] | None = None
custom_energy_deck_p1: list[str] | None = None


def load_game_data():
    """Load card data into global databases."""
    global member_db, live_db, energy_db, rust_serializer
    try:
        cards_path = os.path.join(DATA_DIR, "cards.json")
        print(f"Loading card data from: {cards_path}")
        loader = CardDataLoader(cards_path)
        m, l, e = loader.load()
        member_db.update(m)
        live_db.update(l)
        energy_db.update(e)

        # Initialize rust_serializer
        rust_serializer = RustGameStateSerializer(member_db, live_db, energy_db)

        # Build mapping
        build_card_no_mapping()

        print(f"Data loaded: {len(member_db)} Members, {len(live_db)} Lives, {len(energy_db)} Energy")
        print(f"DEBUG PATHS: PROJECT_ROOT={PROJECT_ROOT}")
        print(f"DEBUG PATHS: FRONTEND_DIR={FRONTEND_DIR}")
        print(f"DEBUG PATHS: WEB_UI_DIR={WEB_UI_DIR}")
        print(f"DEBUG PATHS: IMG_DIR={IMG_DIR}")
    except Exception as ex:
        print(f"CRITICAL ERROR loading card data: {ex}")
        import sys

        sys.exit(1)


def get_local_ip():
    """Get the local IP address of this machine."""
    import socket

    try:
        # Create a temporary socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't even have to be reachable
        s.connect(("8.8.8.8", 1))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


# Load data immediately on import


def get_room_id() -> str:
    """Extract room_id from request header or query param."""
    # Priority: Header > Query Param > Default "SINGLE_PLAYER"
    rid = request.headers.get("X-Room-Id") or request.args.get("room_id")
    if not rid:
        # Debug why no ID found
        # print(f"DEBUG: No X-Room-Id or room_id param. Headers: {request.headers}", file=sys.stderr)
        rid = "SINGLE_PLAYER"
    return rid


def get_player_idx(room: dict = None):
    """
    Extract player perspective.
    Priority: X-Session-Token (via room) > viewer query param > X-Player-Idx header.
    """
    # 1. Try Session Token Lookup if room provided
    session_token = request.headers.get("X-Session-Token")
    if room and session_token:
        sessions = room.get("sessions", {})
        if session_token in sessions:
            pid = sessions[session_token]
            if pid != -1:
                return pid

    # 2. Try query param 'viewer' (fallback/legacy)
    viewer = request.args.get("viewer")
    if viewer is not None:
        try:
            return int(viewer)
        except (ValueError, TypeError):
            pass

    # 3. Fallback to header
    try:
        return int(request.headers.get("X-Player-Idx", 0))
    except (ValueError, TypeError):
        return 0


def get_lang():
    """Extract language preference from X-Lang header or lang query param."""
    lang = request.headers.get("X-Lang") or request.args.get("lang") or "jp"
    if lang.lower() in ("en", "english"):
        return "en"
    return "jp"


def get_room(room_id: str) -> dict[str, Any] | None:
    """Get room data safely."""
    with game_lock:
        room = ROOMS.get(room_id)
        if room:
            room["last_active"] = datetime.now()
        return room


PLANNER_ROOT_PHASES = (Phase.MAIN, Phase.LIVE_SET)
PLANNER_TRACKED_PHASES = (Phase.MAIN, Phase.LIVE_SET, Phase.RESPONSE)


def is_planner_root_phase(phase: Any) -> bool:
    try:
        return int(phase) in {int(p) for p in PLANNER_ROOT_PHASES}
    except (TypeError, ValueError):
        return False


def is_planner_tracked_phase(phase: Any) -> bool:
    try:
        return int(phase) in {int(p) for p in PLANNER_TRACKED_PHASES}
    except (TypeError, ValueError):
        return False


def get_planner_store(room: dict[str, Any]) -> dict[str, Any]:
    planner_store = room.setdefault("planner_lab", {})
    planner_store.setdefault("sessions", {})
    planner_store.setdefault("last_results", {})
    return planner_store


def get_planner_session_key(gs: engine_rust.PyGameState, player_idx: int) -> str:
    return f"{int(gs.turn)}:{player_idx}"


def clone_rust_state(gs: engine_rust.PyGameState) -> engine_rust.PyGameState:
    cloned = engine_rust.PyGameState(RUST_DB)
    cloned.apply_state_json(gs.to_json())
    return cloned


def get_score_breakdown_dict(gs: engine_rust.PyGameState, player_idx: int, rust_db: engine_rust.PyCardDatabase | None = None) -> dict[str, float]:
    if rust_db is None:
        rust_db = RUST_DB
    board, live, success, win, hand, cycling, total = gs.get_score_breakdown(rust_db, player_idx)
    return {
        "board": float(board),
        "live": float(live),
        "success": float(success),
        "win": float(win),
        "hand": float(hand),
        "cycling": float(cycling),
        "total": float(total),
    }


def describe_action_for_state(gs: engine_rust.PyGameState, action_id: int, lang: str) -> str:
    compat_gs = RustCompatGameState(gs, member_db, live_db, energy_db)
    return get_action_desc(action_id, compat_gs, lang=lang, text=gs.pending_choice_text)


def apply_sequence_with_descriptions(
    root_state_json: str,
    action_ids: list[int],
    player_idx: int,
    lang: str,
    rust_db: engine_rust.PyCardDatabase | None = None,
) -> dict[str, Any]:
    if rust_db is None:
        rust_db = RUST_DB
    sim_state = engine_rust.PyGameState(rust_db)
    sim_state.apply_state_json(root_state_json)
    entries: list[dict[str, Any]] = []
    invalid_step = None

    for seq_index, action_id in enumerate(action_ids, start=1):
        legal_ids = set(sim_state.get_legal_action_ids())
        desc = describe_action_for_state(sim_state, action_id, lang)
        entry = {
            "index": seq_index,
            "action_id": int(action_id),
            "desc": desc,
            "legal": action_id in legal_ids,
        }
        entries.append(entry)

        if action_id not in legal_ids:
            invalid_step = seq_index
            entry["error"] = "Illegal from recreated state"
            break

        sim_state.step(action_id)

    return {
        "action_ids": [int(action_id) for action_id in action_ids],
        "sequence": entries,
        "invalid_step": invalid_step,
        "is_valid": invalid_step is None,
        "breakdown": get_score_breakdown_dict(sim_state, player_idx, rust_db),
        "phase_after": int(sim_state.phase),
        "turn_after": int(sim_state.turn),
        "current_player_after": int(sim_state.current_player),
        "is_terminal": bool(sim_state.is_terminal()),
    }


def build_optimal_sequence_payload(root_state_json: str, player_idx: int, lang: str, rust_db: engine_rust.PyCardDatabase | None = None) -> dict[str, Any]:
    if rust_db is None:
        rust_db = RUST_DB
    root_state = engine_rust.PyGameState(rust_db)
    root_state.apply_state_json(root_state_json)

    liveset_nodes = 0
    if int(root_state.phase) == int(Phase.LIVE_SET):
        optimal_ids, liveset_nodes, _ = root_state.find_best_liveset_selection(rust_db)
        planner_breakdown = {"board": 0.0, "live": 0.0, "total": 0.0}
    else:
        _, optimal_ids, planner_nodes, planner_breakdown_raw = root_state.plan_full_turn(rust_db)
        optimal_ids = list(optimal_ids)
        planner_breakdown = {
            "board": float(planner_breakdown_raw[0]),
            "live": float(planner_breakdown_raw[1]),
            "total": float(planner_breakdown_raw[0] + planner_breakdown_raw[1]),
        }
        liveset_nodes = int(planner_nodes)

    full_ids = list(optimal_ids)
    main_state = engine_rust.PyGameState(rust_db)
    main_state.apply_state_json(root_state_json)
    for action_id in optimal_ids:
        main_state.step(action_id)

    appended_liveset = []
    if int(main_state.phase) == int(Phase.LIVE_SET):
        liveset_ids, extra_nodes, _ = main_state.find_best_liveset_selection(rust_db)
        appended_liveset = list(liveset_ids)
        full_ids.extend(appended_liveset)
        liveset_nodes += int(extra_nodes)

    applied = apply_sequence_with_descriptions(root_state_json, full_ids, player_idx, lang, rust_db)
    applied["nodes"] = int(liveset_nodes)
    applied["planner_breakdown"] = planner_breakdown
    applied["main_action_ids"] = [int(action_id) for action_id in optimal_ids]
    applied["liveset_action_ids"] = [int(action_id) for action_id in appended_liveset]
    return applied


def build_planner_analysis_from_session(session: dict[str, Any], lang: str, rust_db: engine_rust.PyCardDatabase | None = None) -> dict[str, Any]:
    if rust_db is None:
        rust_db = RUST_DB
    player_idx = int(session["player_idx"])
    optimal = build_optimal_sequence_payload(session["root_state_json"], player_idx, lang, rust_db)
    your_sequence = apply_sequence_with_descriptions(
        session["root_state_json"],
        session.get("actions", []),
        player_idx,
        lang,
        rust_db,
    )

    matched_prefix = 0
    for own_action, optimal_action in zip(your_sequence["action_ids"], optimal["action_ids"]):
        if own_action != optimal_action:
            break
        matched_prefix += 1

    your_sequence["matched_prefix"] = matched_prefix
    your_sequence["optimal_length"] = len(optimal["action_ids"])
    your_sequence["status"] = "completed" if session.get("completed") else "in_progress"
    your_sequence["root_turn"] = int(session["root_turn"])
    your_sequence["root_phase"] = int(session["root_phase"])

    return {
        "session_key": session["session_key"],
        "player_id": player_idx,
        "root_turn": int(session["root_turn"]),
        "root_phase": int(session["root_phase"]),
        "optimal": optimal,
        "your_sequence": your_sequence,
    }


def ensure_planner_session(room: dict[str, Any], gs: engine_rust.PyGameState, player_idx: int) -> dict[str, Any] | None:
    if not is_planner_root_phase(gs.phase):
        return None

    planner_store = get_planner_store(room)
    session_key = get_planner_session_key(gs, player_idx)
    session_id = str(player_idx)
    existing = planner_store["sessions"].get(session_id)
    if existing and existing.get("session_key") == session_key:
        return existing

    session = {
        "session_key": session_key,
        "player_idx": int(player_idx),
        "root_turn": int(gs.turn),
        "root_phase": int(gs.phase),
        "root_state_json": gs.to_json(),
        "actions": [],
        "completed": False,
    }
    planner_store["sessions"][session_id] = session
    return session


def append_planner_action(room: dict[str, Any], player_idx: int, action_id: int) -> None:
    planner_store = get_planner_store(room)
    session = planner_store["sessions"].get(str(player_idx))
    if not session:
        return
    session.setdefault("actions", []).append(int(action_id))


def finalize_planner_session(room: dict[str, Any], player_idx: int, lang: str) -> None:
    planner_store = get_planner_store(room)
    session = planner_store["sessions"].pop(str(player_idx), None)
    if not session:
        return

    session["completed"] = True
    result = build_planner_analysis_from_session(session, lang)
    result["your_sequence"]["status"] = "completed"
    planner_store["last_results"][str(player_idx)] = result


def maybe_finalize_planner_session(
    room: dict[str, Any],
    gs: engine_rust.PyGameState,
    player_idx: int,
    lang: str,
) -> None:
    planner_store = get_planner_store(room)
    session = planner_store["sessions"].get(str(player_idx))
    if not session:
        return

    if (
        int(gs.turn) == int(session["root_turn"])
        and int(gs.current_player) == int(player_idx)
        and is_planner_tracked_phase(gs.phase)
        and not gs.is_terminal()
    ):
        return

    finalize_planner_session(room, player_idx, lang)


def build_planner_payload(room: dict[str, Any], gs: engine_rust.PyGameState, player_idx: int, lang: str) -> dict[str, Any]:
    planner_store = get_planner_store(room)
    active = False
    session = planner_store["sessions"].get(str(player_idx))
    rust_db = get_rust_db_for_card_set(room.get("card_set", "compiled"))

    if not session and int(gs.current_player) == int(player_idx) and is_planner_root_phase(gs.phase) and not gs.is_terminal():
        session = ensure_planner_session(room, gs, player_idx)

    if session:
        active = True
        analysis = build_planner_analysis_from_session(session, lang, rust_db)
        analysis["active"] = True
        analysis["available"] = True
        return analysis

    last_result = planner_store["last_results"].get(str(player_idx))
    if last_result:
        payload = dict(last_result)
        payload["active"] = False
        payload["available"] = True
        payload["message"] = "Showing your last completed scored sequence."
        return payload

    return {
        "available": bool(int(gs.current_player) == int(player_idx) and is_planner_root_phase(gs.phase) and not gs.is_terminal()),
        "active": False,
        "message": "Turn planner becomes available on your Main or Live Set turn.",
        "player_id": int(player_idx),
        "root_turn": int(gs.turn),
        "root_phase": int(gs.phase),
        "optimal": None,
        "your_sequence": None,
    }


# Reverse mapping: card_no string -> internal integer ID
card_no_to_id: dict[str, int] = {}


def build_card_no_mapping():
    """Build reverse lookup from card_no string to internal ID using compiled data.
    Ensures consistency with the Rust engine's internal ID assignments.
    """
    global card_no_to_id
    card_no_to_id = {}

    try:
        compiled_path = os.path.join(DATA_DIR, "cards_compiled.json")
        if not os.path.exists(compiled_path):
            print(f"Warning: {compiled_path} not found. Mapping will be empty.")
            return

        with open(compiled_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Build mapping from dbs
        count = 0
        for db_name in ["member_db", "live_db", "energy_db"]:
            db = data.get(db_name, {})
            for internal_id, card_data in db.items():
                card_no = card_data.get("card_no")
                if card_no:
                    # Convert string key to integer ID
                    # USE NORMALIZED KEY
                    norm_key = UnifiedDeckParser.normalize_code(card_no)
                    card_no_to_id[norm_key] = int(internal_id)
                    count += 1

        print(f"Built card_no_to_id mapping from compiled data: {count} entries")
    except Exception as e:
        print(f"Error building mapping from compiled data: {e}")


# Load data immediately on import
load_game_data()


# Initialize mapping on startup
build_card_no_mapping()


def convert_deck_strings_to_ids(deck_strings):
    """Convert list of card_no strings to internal IDs (Unique Instance IDs)."""
    ids = []
    counts = {}
    for card_no in deck_strings:
        norm_code = UnifiedDeckParser.normalize_code(card_no)
        if norm_code in card_no_to_id:
            base_id = card_no_to_id[norm_code]
            count = counts.get(base_id, 0)
            uid = create_uid(base_id, count)
            counts[base_id] = count + 1
            ids.append(uid)
        else:
            print(f"Warning: Unknown card_no '{card_no}' (norm: '{norm_code}'), skipping.")
    return ids


def save_replay(gs: GameState | None = None):
    """Save the provided game state's history to a file."""
    if gs is None or not gs.rule_log:
        return

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("replays", exist_ok=True)
        filename = f"replays/replay_{timestamp}.json"
        filename_opt = f"replays/replay_{timestamp}_opt.json"

        # Use historical states from rule_log or history if we maintain one
        # For now, we assume GS has what we need or we pass history
        history = []  # In this engine, standard replays are often built from logs or incremental states

        # 1. Save Standard Replay (Compatible)
        data = {
            "game_id": 0,
            "timestamp": timestamp,
            "winner": gs.winner if gs else -1,
            "states": history,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"Replay saved to {filename}")

        # 2. Save Optimized Replay (Dict Encoded)
        try:
            print("Optimizing replay...")

            # Gather Level 3 Context
            deck_info = None
            if gs:
                deck_info = {
                    "p0_deck": list(getattr(gs.players[0], "initial_deck_indices", [])),
                    "p1_deck": list(getattr(gs.players[1], "initial_deck_indices", [])),
                }

            opt_data = optimize_history(
                history,
                member_db,
                live_db,
                energy_db,
                exclude_db_cards=True,
                # seed=current_seed,
                # action_log=action_log,
                deck_info=deck_info,
            )

            final_opt = {
                "game_id": 0,
                "timestamp": timestamp,
                "winner": gs.winner if gs else -1,
            }

            # Merge optimization data
            if "level" in opt_data and opt_data["level"] == 3:
                final_opt.update(opt_data)  # seed, decks, action_log
                print("Level 3 Optimization Active (Action Log)")
            else:
                final_opt["states"] = opt_data["states"]

            with open(filename_opt, "w", encoding="utf-8") as f:
                json.dump(final_opt, f, ensure_ascii=False)

            # Calculate savings
            size_std = os.path.getsize(filename)
            size_opt = os.path.getsize(filename_opt)
            savings = (1 - size_opt / size_std) * 100
            print(f"Optimized replay saved to {filename_opt}")
            print(f"Compression: {size_std / 1024:.1f}KB -> {size_opt / 1024:.1f}KB ({savings:.1f}% savings)")

        except Exception as e:
            print(f"Failed to save optimized replay: {e}")
            import traceback

            traceback.print_exc()

    except Exception as e:
        print(f"Failed to save replay: {e}")


game_history = []  # For replay recording
action_log = []  # For action-based replay
current_seed = 0  # For deterministic replay


def init_game(deck_type="normal"):
    global game_state, member_db, live_db, energy_db, game_history, current_seed, action_log

    # Ensure true randomness for each game
    import time

    real_seed = int(time.time() * 1000) % (2**31)
    current_seed = real_seed
    random.seed(real_seed)

    # Store action history separately for Level 3 Replay
    global action_log
    action_log = []

    # DATA PATH: data/cards.json
    cards_path = os.path.join(DATA_DIR, "cards.json")
    loader = CardDataLoader(cards_path)
    member_db, live_db, energy_db = loader.load()

    # CRITICAL: Populate GameState static DBs so validations work
    # Use initialize_class_db to ensure proper wrapping with MaskedDB
    GameState.initialize_class_db(member_db, live_db)
    GameState.energy_db = energy_db

    # Initialize JIT arrays for performance
    GameState._init_jit_arrays()

    # Build reverse mapping for custom deck support
    build_card_no_mapping()

    # Pre-calculate Start Deck card IDs

    # Load raw JSON to check product field for filtering
    cards_path = os.path.join(DATA_DIR, "cards.json")
    with open(cards_path, "r", encoding="utf-8") as f:
        json.load(f)

    for _cid, _m in member_db.items():
        # Find raw key by matching name/cost/type? Or better, DataLoader should store product.
        # Since DataLoader doesn't verify product yet, we'll try to guess or just use ALL valid cards
        # that are from Start Deck (usually ID < 100 for this mock loader or by string ID).
        # Actually, let's just use ALL loaded members/lives for 'normal' and specific ones for 'starter'.
        # For 'start_deck', we can filter by card string ID prefix 'PL!-sd1' or 'LL-E'.

        # But 'member_db' keys are integers 0..N. We need a way to link back.
        # The loader assigns IDs sequentially.
        # Let's just build a random valid deck from ALL cards for now,
        # unless 'easy' mode.
        pass

    # If deck_type is 'easy', we use the simple mock cards for logic testing.
    # If deck_type is 'normal' or 'starter', we use REAL cards.

    if deck_type == "easy":
        easy_m, easy_l = create_easy_cards()
        member_db[easy_m.card_id] = easy_m
        live_db[easy_l.card_id] = easy_l

    game_state = GameState()

    # Setup players
    for pidx, p in enumerate(game_state.players):
        # Check for custom deck first
        custom_deck = custom_deck_p0 if pidx == 0 else custom_deck_p1

        if custom_deck:
            # Use custom deck
            p.main_deck = convert_deck_strings_to_ids(custom_deck)
            random.shuffle(p.main_deck)  # Shuffle custom deck for variety
            print(f"Player {pidx}: Using custom deck ({len(p.main_deck)} cards, shuffled)")
        elif deck_type == "easy":
            # Use Easy Cards (888/999) but mapped to real images
            p.main_deck = [888] * 48 + [999] * 12
        else:
            # NORMAL / STARTER MODE: Build a valid deck
            # Rule: Max 4 copies of same card number.
            # Total: 48 Members + 12 Lives (Total 60 in main deck per game_state spec)

            p.main_deck = []

            # 1. Select Members (48)
            available_members = list(member_db.keys())
            if available_members:
                # Shuffle availability to vary decks
                random.shuffle(available_members)

                member_bucket = []
                for mid in available_members:
                    # Add 4 copies of each until we have enough
                    # Use create_uid for unique instance IDs
                    for i in range(4):
                        uid = create_uid(mid, i)
                        member_bucket.append(uid)

                    if len(member_bucket) >= 150:  # Optimization: Don't build massive list
                        break

                # Pick 48 from the bucket
                if len(member_bucket) < 48:
                    # Fallback if DB too small
                    while len(member_bucket) < 48:
                        member_bucket.extend(available_members)

                # Ensure we don't accidentally pick >4 if we just slice
                # Actually, simply taking the first 48 from our constructed bucket (which has 4 of each distinct card)
                # guarantees validity if we shuffle the CARDS/TYPES, not the final list.
                # Steps:
                # 1. Shuffle types.
                # 2. Add 4 of Type A, 4 of Type B...
                # 3. Take first 48 cards.

                p.main_deck.extend(member_bucket[:48])

            # 2. Select Lives (12)
            available_lives = list(live_db.keys())
            if available_lives:
                random.shuffle(available_lives)
                live_bucket = []
                for lid in available_lives:
                    # live_bucket.extend([lid] * 4)
                    for i in range(4):
                        uid = create_uid(lid, i)
                        live_bucket.append(uid)

                    if len(live_bucket) >= 50:
                        break

                if len(live_bucket) < 12:
                    while len(live_bucket) < 12:
                        live_bucket.extend(available_lives)

                p.main_deck.extend(live_bucket[:12])

            random.shuffle(p.main_deck)

        # Energy Deck (12 cards)
        # Use actual Energy Card ID if available (2000+)
        if energy_db:
            eid = list(energy_db.keys())[0]  # Take first energy card type found
            p.energy_deck = [eid] * 12
        else:
            p.energy_deck = [40000] * 12  # Fallback

        # Custom Energy Deck Override
        custom_energy = custom_energy_deck_p0 if pidx == 0 else custom_energy_deck_p1
        if custom_energy:
            p.energy_deck = convert_deck_strings_to_ids(custom_energy)
            print(f"Player {pidx}: Using custom energy deck ({len(p.energy_deck)} cards)")

        # Explicit shuffle before drawing
        random.shuffle(p.main_deck)
        if game_state.players.index(p) == 0:
            print(f"DEBUG: P0 Deck Shuffled. Top 5: {p.main_deck[-5:]}")

        # Initial draw (6 cards - standard Mulligan start)
        for _ in range(6):
            if p.main_deck:
                p.hand.append(p.main_deck.pop())
                p.hand_added_turn.append(game_state.turn_number)

        # Initial energy: 3 cards (Rule 6.2.1.7)
        for _ in range(3):
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))

    # Randomly determine first player
    game_state.first_player = random.randint(0, 1)

    # For Mulligan Phase (P1/Index 0), Current Player MUST be 0
    # The 'first_player' variable determines who acts first in ACTIVE phase (Round 1)
    game_state.current_player = 0

    # Start in MULLIGAN phase
    game_state.phase = Phase.MULLIGAN_P1


def get_rust_db_for_card_set(card_set: str = "compiled"):
    """Get the appropriate Rust database based on card_set selection."""
    if card_set == "vanilla":
        if RUST_DB_VANILLA is None:
            raise Exception("RUST_DB_VANILLA not initialized")
        return RUST_DB_VANILLA
    else:
        if RUST_DB is None:
            raise Exception("RUST_DB not initialized")
        return RUST_DB


def create_room_internal(
    room_id: str,
    mode: str = "pve",
    deck_type: str = "normal",
    public: bool = False,
    custom_decks: dict = None,
    card_set: str = "compiled",
) -> dict[str, Any]:
    """Helper to initialize a room using the RUST engine."""
    print(
        f"DEBUG: Creating Rust Room {room_id} (Mode: {mode}, Deck: {deck_type}, Public: {public}, CustomDecks: {bool(custom_decks)}, CardSet: {card_set})"
    )

    rust_db = get_rust_db_for_card_set(card_set)
    gs = engine_rust.PyGameState(rust_db)

    # helper for deck generation
    # helper for deck generation
    def get_random_decks():
        m_ids = list(member_db.keys())
        l_ids = list(live_db.keys())
        random.shuffle(m_ids)
        random.shuffle(l_ids)

        # 1. Select 48 Members (12 types * 4 copies)
        member_deck = []
        # Use available members, cycling if needed
        needed_types = 12
        selected_m_types = []

        if len(m_ids) < needed_types:
            # Fallback if DB small
            selected_m_types = m_ids * (needed_types // len(m_ids) + 1)
        else:
            selected_m_types = m_ids

        for mid in selected_m_types[:needed_types]:
            member_deck.extend([mid] * 4)

        # 2. Select 12 Lives (3 types * 4 copies)
        live_deck = []
        needed_lives = 3
        selected_l_types = []

        if len(l_ids) < needed_lives:
            selected_l_types = l_ids * (needed_lives // len(l_ids) + 1)
        else:
            selected_l_types = l_ids

        for lid in selected_l_types[:needed_lives]:
            live_deck.extend([lid] * 4)

        # Shuffle main deck parts?
        # Actually initialize_game expects specific vectors.
        # Logic.rs: d0.extend(p0_lives); self.players[0].deck = SmallVec::from_vec(d0);
        # So we should pass them separately.
        # But wait, logic.rs `initialize_game_with_seed`:
        # let mut d0 = p0_deck; d0.extend(p0_lives);
        # So p0_deck should be ONLY members (48), and p0_lives should be ONLY lives (12).

        # Energy
        e_deck = [list(energy_db.keys())[0]] * 12 if energy_db else [40000] * 12

        # Return strict separated vectors
        return member_deck, e_deck, live_deck

    # Defaults
    p0_m, p0_e, p0_l = get_random_decks()
    p1_m, p1_e, p1_l = get_random_decks()

    # Override with custom decks if provided
    final_custom_decks = {0: {"main": [], "energy": []}, 1: {"main": [], "energy": []}}
    if custom_decks:
        final_custom_decks.update(custom_decks)
        for pid in [0, 1]:
            cdeck = custom_decks.get(str(pid)) or custom_decks.get(pid)
            if cdeck and cdeck.get("main"):
                # Convert strings to IDs
                all_main_ids = convert_deck_strings_to_ids(cdeck["main"])
                random.shuffle(all_main_ids)

                # Partition into Members and Lives
                members = []
                lives = []
                for uid in all_main_ids:
                    base_id = uid & BASE_ID_MASK
                    if base_id in member_db:
                        members.append(uid)
                    elif base_id in live_db:
                        lives.append(uid)

                # Truncate to standard limits (48 members, 12 lives)
                # This ensures the engine receives exactly what it expects
                if len(members) > 48:
                    members = members[:48]
                if len(lives) > 12:
                    lives = lives[:12]

                if pid == 0:
                    p0_m = members
                    p0_l = lives
                else:
                    p1_m = members
                    p1_l = lives

                # Energy (Strictly 12)
                if cdeck.get("energy"):
                    e_ids = convert_deck_strings_to_ids(cdeck["energy"])
                    if len(e_ids) > 12:
                        e_ids = e_ids[:12]

                    if pid == 0:
                        p0_e = e_ids
                    else:
                        p1_e = e_ids

    # Warning: We are not extracting initial lives from main deck for p0_l/p1_l if custom.
    # The engine probably draws them?
    # If `p0_l` is required, we should pick random 3 from lives in deck or DB?
    # For now, let's keep random lives for the Live Zone if not specified, or just reuse random ones.

    gs.initialize_game(p0_m, p1_m, p0_e, p1_e, p0_l, p1_l)

    return {
        "state": gs,
        "mode": mode,
        "card_set": card_set,
        "public": public,
        "created_at": datetime.now(),
        "last_active": datetime.now(),
        "ai_agent": None,  # MCTS is built-in
        "custom_decks": final_custom_decks,
        "sessions": {},
        "usernames": {},  # PID -> username
        "engine": "rust",
        "planner_lab": {"sessions": {}, "last_results": {}},
        # History tracking for undo/redo
        "history_stack": [gs], # Store raw state for on-demand localization
        "history_index": 0,
    }


def join_room_logic(room_id: str, username: str = None) -> dict[str, Any]:
    """
    Logic to add a user session to a room.
    Returns {"session_id": str, "player_id": int}
    """
    if room_id not in ROOMS:
        return {"error": "Room not found"}

    room = ROOMS[room_id]
    sessions = room["sessions"]
    usernames = room.get("usernames", {})

    new_pid = -1
    session_id = str(uuid.uuid4())

    # 1. Recovery Logic: Check if username already exists in this room
    if username:
        username = username.strip()
        for pid, existing_user in usernames.items():
            if existing_user == username:
                print(f"DEBUG: Recovering session for '{username}' as Player {pid}")
                sessions[session_id] = pid
                return {"session_id": session_id, "player_id": pid, "recovered": True}

    # 2. Assignment Logic: Check current players
    taken_pids = set(sessions.values())

    if 0 not in taken_pids:
        new_pid = 0
    elif 1 not in taken_pids:
        new_pid = 1
    else:
        # Both full. Spectator?
        new_pid = -1

    # 3. Store identity
    sessions[session_id] = new_pid
    if username and new_pid != -1:
        usernames[new_pid] = username
        room["usernames"] = usernames

    return {"session_id": session_id, "player_id": new_pid}


# --- ROOM MANAGEMENT API ---


@app.route("/api/rooms/create", methods=["POST"])
def create_new_room():
    print("DEBUG: Entered create_new_room endpoint", file=sys.stderr)
    try:
        data = request.json or {}
    except Exception as e:
        print(f"DEBUG: Failed to parse JSON: {e}", file=sys.stderr)
        data = {}

    # Extract parameters
    room_id = get_room_id()
    mode = data.get("mode", "pve")
    is_public = data.get("public", False)
    card_set = data.get("card_set", "compiled")
    custom_decks = None

    print(f"DEBUG: Generated room_id {room_id}, acquiring lock...", file=sys.stderr)

    # Handle frontend parameters if 'decks' is not present
    if not custom_decks:
        p0_main = data.get("p0_deck")
        p0_energy = data.get("p0_energy", [])
        p1_main = data.get("p1_deck")
        p1_energy = data.get("p1_energy", [])

        if p0_main or p1_main:
            custom_decks = {}
            if p0_main:
                custom_decks["0"] = {"main": p0_main, "energy": p0_energy}
            if p1_main:
                custom_decks["1"] = {"main": p1_main, "energy": p1_energy}

    res = {}
    res = {}
    with game_lock:
        print("DEBUG: Lock acquired. Creating room internal...", file=sys.stderr)
        ROOMS[room_id] = create_room_internal(room_id, mode, public=is_public, custom_decks=custom_decks, card_set=card_set)
        print("DEBUG: Room created internally. Joining creator...", file=sys.stderr)

        # Auto-join creator with username if provided
        username = data.get("username")
        join_res = join_room_logic(room_id, username=username)

    print("DEBUG: Returning response.", file=sys.stderr)
    return jsonify({"success": True, "room_id": room_id, "mode": mode, "card_set": card_set, "session": join_res})


@app.route("/api/rooms/list", methods=["GET"])
def list_public_rooms():
    """Return a list of public rooms."""
    public_rooms = []
    with game_lock:
        for rid, room in ROOMS.items():
            if room.get("public", False):
                # Calculate player count
                sessions = room.get("sessions", {})
                player_count = len(set(sessions.values()))  # Approximate, might need better logic if spectators exist
                # Or just count occupied slots (0 and 1)
                occupied_slots = 0
                taken_pids = set(sessions.values())
                if 0 in taken_pids:
                    occupied_slots += 1
                if 1 in taken_pids:
                    occupied_slots += 1

                # Basic Info
                gs = room.get("state")
                # Handle both Rust (turn) and Python (turn_number) attributes
                turn = getattr(gs, "turn_number", getattr(gs, "turn", 0))
                phase = str(gs.phase) if gs else "?"

                public_rooms.append(
                    {
                        "room_id": rid,
                        "mode": room.get("mode", "pve"),
                        "players": occupied_slots,
                        "turn": turn,
                        "phase": phase,
                        "created_at": room.get("created_at", datetime.now()).isoformat(),
                    }
                )

    # Sort by creation time desc
    public_rooms.sort(key=lambda x: x["created_at"], reverse=True)
    return jsonify({"success": True, "rooms": public_rooms})


@app.route("/api/rooms/join", methods=["POST"])
def join_room():
    print("DEBUG: Entered join_room", file=sys.stderr)
    data = request.json or {}
    room_id = data.get("room_id", "").upper().strip()
    print(f"DEBUG: Entered join_room for ID: '{room_id}'", file=sys.stderr)

    with game_lock:
        if room_id in ROOMS:
            mode = ROOMS[room_id]["mode"]
            card_set = ROOMS[room_id].get("card_set", "compiled")
            print(f"DEBUG: Found room {room_id}, mode={mode}, card_set={card_set}", file=sys.stderr)

            # Assign a session/seat to the joining player
            username = data.get("username")
            join_res = join_room_logic(room_id, username=username)
            if "error" in join_res:
                return jsonify({"success": False, "error": join_res["error"]}), 400

            # CRITICAL: Use the "session" key to match frontend expectations
            return jsonify(
                {
                    "success": True,
                    "room_id": room_id,
                    "mode": mode,
                    "card_set": card_set,
                    "session": join_res,
                    "recovered": join_res.get("recovered", False),
                }
            )

    return jsonify({"success": False, "error": "Room not found"}), 404


@app.route("/api/rooms/leave", methods=["POST"])
def leave_room():
    """Allow a player to leave a room."""
    room_id = get_room_id()
    session_token = request.headers.get("X-Session-Token")

    if not room_id or room_id not in ROOMS:
        return jsonify({"success": False, "error": "Room not found"}), 404

    with game_lock:
        room = ROOMS.get(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found"}), 404

        sessions = room.get("sessions", {})

        # Remove the session
        if session_token and session_token in sessions:
            del sessions[session_token]
            print(f"DEBUG: Session {session_token} left room {room_id}", file=sys.stderr)

        # Don't immediately delete room - let cleanup handle it
        # But update last_active so it doesn't get cleaned up immediately
        room["last_active"] = datetime.now()

        return jsonify({"success": True})


@app.route("/")
def index():
    return send_from_directory(WEB_UI_DIR, "index.html")


@app.route("/board")
def game_board():
    return send_from_directory(WEB_UI_DIR, "game_board.html")  # Assuming it exists there


@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(os.path.join(WEB_UI_DIR, "js"), filename)


@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(os.path.join(WEB_UI_DIR, "css"), filename)


@app.route("/icon_blade.png")
def serve_icon():
    # If icon is in root or img, adjust. Assuming img for now or checking existence.
    # Fallback to IMG_DIR or WEB_UI_DIR
    return send_from_directory(IMG_DIR, "icon_blade.png")


@app.route("/deck_builder.html")
def serve_deck_builder():
    return send_from_directory(WEB_UI_DIR, "deck_builder.html")


@app.route("/data/<path:filename>")
def serve_data(filename):
    return send_from_directory(DATA_DIR, filename)


import threading
import time

# Threading setup
game_lock = threading.RLock()  # Re-entrant lock to prevent self-deadlock
game_thread = None
_cleanup_counter = 0  # Counter for cleanup interval


def cleanup_inactive_rooms():
    """
    Remove rooms that have been inactive for too long or have no active sessions.
    Called periodically from background_game_loop.
    """
    global _cleanup_counter
    _cleanup_counter += 1

    # Only run cleanup every ROOM_CLEANUP_INTERVAL seconds (based on 0.1s sleep = 600 loops)
    if _cleanup_counter < ROOM_CLEANUP_INTERVAL:
        return

    _cleanup_counter = 0

    now = datetime.now()
    timeout = timedelta(minutes=ROOM_INACTIVE_TIMEOUT_MINUTES)

    rooms_to_remove = []

    for rid, room in ROOMS.items():
        # Skip SINGLE_PLAYER room - it's special
        if rid == "SINGLE_PLAYER":
            continue

        last_active = room.get("last_active")
        sessions = room.get("sessions", {})

        # Check if room has any active sessions
        active_sessions = [sid for sid, pid in sessions.items() if pid != -1]

        # Remove if:
        # 1. No active sessions (all players left)
        # 2. Inactive for too long
        should_remove = False
        reason = ""

        if not active_sessions:
            should_remove = True
            reason = "no active sessions"
        elif last_active and (now - last_active) > timeout:
            should_remove = True
            reason = f"inactive for {(now - last_active).total_seconds() / 60:.1f} minutes"

        if should_remove:
            rooms_to_remove.append((rid, reason))

    # Remove the rooms
    for rid, reason in rooms_to_remove:
        print(f"DEBUG: Cleaning up room {rid}: {reason}", file=sys.stderr)
        del ROOMS[rid]

    if rooms_to_remove:
        print(f"DEBUG: Cleaned up {len(rooms_to_remove)} inactive rooms", file=sys.stderr)


def background_game_loop():
    """
    Runs the game logic (AI and auto-phases) for ALL active rooms.
    """
    print("Background Game Loop Started (Multi-Room)", file=sys.stderr)

    while True:
        try:
            # print("DEBUG: Background Loop acquiring lock...", file=sys.stderr)

            # Run room cleanup periodically
            cleanup_inactive_rooms()

            with game_lock:
                # Iterate over a copy of keys to avoid modification issues if needed
                active_room_ids = list(ROOMS.keys())

                for rid in active_room_ids:
                    # print(f"DEBUG: Processing room {rid}...", file=sys.stderr)
                    room = ROOMS.get(rid)
                    if not room:
                        continue

                    # Skip rooms with no active sessions (except SINGLE_PLAYER)
                    if rid != "SINGLE_PLAYER":
                        sessions = room.get("sessions", {})
                        active_sessions = [sid for sid, pid in sessions.items() if pid != -1]
                        if not active_sessions:
                            continue

                    gs = room["state"]
                    game_mode = room["mode"]
                    ai_agent = room["ai_agent"]

                    if not gs.is_terminal():
                        # 1. Auto-Advance Phases
                        if gs.phase in (
                            Phase.ACTIVE,
                            Phase.ENERGY,
                            Phase.DRAW,
                            Phase.PERFORMANCE_P1,
                            Phase.PERFORMANCE_P2,
                        ):
                            # Safe attribute access for Rust engine compatibility
                            p_choices = getattr(gs, "pending_choices", [])
                            p_effects = getattr(gs, "pending_effects", [])
                            if not (p_choices or p_effects):
                                res = gs.step(0)
                                if res is not None:
                                    room["state"] = res
                                    gs = res

                        elif gs.current_player == 1 and game_mode == "pve":
                            is_continue_choice = False
                            if gs.pending_choices and gs.pending_choices[0][0].startswith("CONTINUE"):
                                is_continue_choice = True

                            if gs.phase == Phase.LIVE_RESULT and is_continue_choice:
                                # Wait for Human
                                pass
                            else:
                                if gs.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
                                    aid = 0
                                    res = gs.step(aid)
                                    if res is not None:
                                        room["state"] = res
                                else:
                                    if room.get("engine") == "rust":
                                        # Use Greedy (1-ply) AI for Rust engine in PVE to maximize responsiveness
                                        gs.step_opponent_greedy()
                                    else:
                                        aid = ai_agent.choose_action(gs, 1)
                                        res = gs.step(aid)
                                        if res is not None:
                                            room["state"] = res

            time.sleep(0.1)

        except Exception as e:
            print(f"Error in game loop: {e}")
            import traceback

            traceback.print_exc()
            time.sleep(1.0)


@app.route("/api/state")
def get_state():
    room_id = get_room_id()
    session_token = request.headers.get("X-Session-Token")

    with game_lock:
        # Development convenience: Auto-create room if missing IF it's "SINGLE_PLAYER"
        if room_id == "SINGLE_PLAYER" and room_id not in ROOMS:
            ROOMS[room_id] = create_room_internal(room_id)

        room = get_room(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found or expired"}), 404

        # Check if we're in history navigation mode (rewind/redo)
        history_stack = room.get("history_stack", [])
        history_index = room.get("history_index", 0)
        
        if history_stack and history_index < len(history_stack):
            # Return state from history
            gs_history = history_stack[history_index]
            mode = room["mode"]
            lang = get_lang()
            
            # Serialize on-demand with correct language
            if room.get("engine") == "rust":
                 s_state = rust_serializer.serialize_state(gs_history, viewer_idx=0, mode=mode, is_pvp=False, lang=lang)
            else:
                 s_state = serialize_state(gs_history, viewer_idx=0, is_pvp=False, mode=mode, lang=lang)

            cdecks = room.get("custom_decks", {})
            meta = {
                "p0_deck_set": bool(cdecks.get(0, {}).get("main") or cdecks.get("0", {}).get("main")),
                "p1_deck_set": bool(cdecks.get(1, {}).get("main") or cdecks.get("1", {}).get("main")),
                "mode": mode,
                "history_mode": True,
                "history_index": history_index,
                "history_length": len(history_stack),
            }
            
            return jsonify({"success": True, "state": s_state, "meta": meta})

        gs = room["state"]
        mode = room["mode"]
        viewer_idx = get_player_idx(room)

        lang = get_lang()
        if room.get("engine") == "rust":
            s_state = rust_serializer.serialize_state(gs, viewer_idx=viewer_idx, mode=mode, is_pvp=False, lang=lang)
        else:
            s_state = serialize_state(
                gs,
                viewer_idx=viewer_idx,
                is_pvp=False,
                mode=mode,
                lang=lang,
            )

        # Meta info about decks
        cdecks = room.get("custom_decks", {})
        meta = {
            "p0_deck_set": bool(cdecks.get(0, {}).get("main") or cdecks.get("0", {}).get("main")),
            "p1_deck_set": bool(cdecks.get(1, {}).get("main") or cdecks.get("1", {}).get("main")),
            "mode": mode,
        }

        return jsonify({"success": True, "state": s_state, "meta": meta})


@app.route("/api/set_deck", methods=["POST"])
def set_deck():
    """Accept a custom deck for a player in a specific room."""
    data = request.json
    player_id = data.get("player", 0)
    deck_ids = data.get("deck", [])  # List of card_no strings
    energy_ids = data.get("energy_deck", [])

    room_id = get_room_id()

    with game_lock:
        room = get_room(room_id)
        # For setting deck, we might want to allow it even if room doesn't exist yet?
        # But conceptually, you create a room, then set deck, then reset/start.
        if not room:
            # Auto-create for dev workflow
            ROOMS[room_id] = create_room_internal(room_id)
            room = ROOMS[room_id]

        room["custom_decks"][player_id] = {"main": deck_ids, "energy": energy_ids}

    return jsonify(
        {
            "status": "ok",
            "player": player_id,
            "deck_size": len(deck_ids),
            "message": f"Deck set for Player {player_id + 1} in Room {room_id}. Reset game to apply.",
        }
    )


@app.route("/api/rooms/assets")
def get_room_assets():
    """Return a unique list of image paths for all cards used in the current room."""
    room_id = get_room_id()
    room = get_room(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    assets = set()

    def add_card_assets(cid):
        if cid is None or cid < 0:
            return
        base_id = int(cid) & BASE_ID_MASK
        bid_str = str(base_id)
        if bid_str in member_db:
            assets.add(member_db[bid_str].img_path)
        elif bid_str in live_db:
            assets.add(live_db[bid_str].img_path)
        elif bid_str in energy_db:
            assets.add(energy_db[bid_str].img_path)

    # 1. From Custom Decks (Pending)
    custom_decks = room.get("custom_decks", {})
    for _pid, deck_info in custom_decks.items():
        # 'main' and 'energy' contain card_no strings
        for card_no in deck_info.get("main", []):
            if card_no in card_no_to_id:
                add_card_assets(card_no_to_id[card_no])
        for card_no in deck_info.get("energy", []):
            if card_no in card_no_to_id:
                add_card_assets(card_no_to_id[card_no])

    # 2. From Current Game State (Active)
    if room.get("state"):
        gs = room["state"]
        for p_idx in [0, 1]:
            try:
                p = gs.get_player(p_idx)
                # Check all zones
                zones = [p.hand, p.stage, p.live_zone, p.energy_zone, p.discard, p.success_lives]
                for zone in zones:
                    for cid in zone:
                        add_card_assets(cid)
            except Exception as e:
                print(f"DEBUG: Error extracting assets from player {p_idx}: {e}")

    # Convert to list and filter out None
    final_assets = sorted([a for a in assets if a])
    return jsonify({"success": True, "assets": final_assets})


@app.route("/api/upload_deck", methods=["POST"])
def upload_deck():
    """Accept a raw deck file content (decktest.txt style) and load it."""
    data = request.json
    content = data.get("content", "")
    player_id = data.get("player", 0)

    room_id = get_room_id()

    # Parse content
    try:
        if content.strip().startswith("{") or content.strip().startswith("["):
            # JSON format
            deck_data = json.loads(content)
            # Support both simple list and object
            if isinstance(deck_data, list):
                main_deck = deck_data
                energy_deck = []  # JSON list implies only main deck usually?
            elif "main" in deck_data:
                main_deck = deck_data["main"]
                energy_deck = deck_data.get("energy", [])
            else:
                return jsonify(
                    {"success": False, "error": "Invalid JSON deck format. Expected list or object with 'main' key."}
                )
        else:
            # HTML/Text format
            card_db = {}
            try:
                cards_path = os.path.join(DATA_DIR, "cards.json")
                with open(cards_path, "r", encoding="utf-8") as f:
                    card_db = json.load(f)
            except Exception as e:
                return jsonify({"success": False, "error": f"Failed to load card DB for validation: {e}"})

            main_deck, energy_deck, _, errors = extract_deck_data(content, card_db)  # Pass DB for validation
            if errors:
                return jsonify({"success": False, "error": "Validation Errors:\n" + "\n".join(errors)})

    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Invalid JSON format."})
    except Exception as e:
        print(f"Deck parsing error: {e}")
        return jsonify({"success": False, "error": str(e)})

    if not main_deck and not energy_deck:
        return jsonify({"success": False, "error": "No cards found in file."})

    with game_lock:
        room = get_room(room_id)
        if not room:
            ROOMS[room_id] = create_room_internal(room_id)
            room = ROOMS[room_id]

        room["custom_decks"][player_id] = {"main": main_deck, "energy": energy_deck}

        # Auto-apply?
        # Re-init room with "custom" logic?
        # For now, let's just create a new room state using these decks immediately for convenience
        # But we need to respect the loop.
        # Actually existing logic calls init_game(deck_type="custom").

        # We'll just trigger a reset logic manually
        # This duplicates logic in reset() but scoped to this room + custom deck applied.

        # For simplicity, we just store it. User must click "Reset" or we call reset internal?
        # The frontend usually expects upload to just work.
        pass

    # Trigger Reset via API logic simulation or just return success and let caller Reset?
    # Existing behavior: calls init_game("custom").
    # So we should probably do the same: reset the room's state using these custom decks.
    # We can reuse the create_room_internal logic if we modify it to accept custom decks directly?
    # Or just rely on the room["custom_decks"] being set.

    # Let's call reset internal logic here?
    # Better: Update endpoints first, then we can verify flow.
    # For now, we assume user clicks Reset or we simulate it.

    # Actually, let's just return success. The frontend typically reloads or resets.

    return jsonify(
        {
            "success": True,
            "main_count": len(main_deck),
            "energy_count": len(energy_deck),
            "room_id": room_id,
            "message": f"Deck Loaded! ({len(main_deck)} Main, {len(energy_deck)} Energy). Please Reset.",
        }
    )


@app.route("/api/get_test_deck", methods=["GET"])
def get_test_deck_api():
    """Read deck files from ai/decks/ directory and return card list."""
    from engine.game.deck_utils import extract_deck_data

    deck_name = request.args.get("deck", "")  # Optional deck name parameter

    # Path to ai/decks directory
    # Use PROJECT_ROOT for reliability
    ai_decks_dir = os.path.join(PROJECT_ROOT, "ai", "decks")

    if not os.path.exists(ai_decks_dir):
        # Fallback: try CWD relative
        ai_decks_dir = os.path.abspath(os.path.join("ai", "decks"))

    if not os.path.exists(ai_decks_dir):
        return jsonify({"success": False, "error": "ai/decks directory not found"})

    # List available decks (excluding verify script)
    available_decks = []
    for f in os.listdir(ai_decks_dir):
        if f.endswith(".txt") and not f.startswith("verify"):
            available_decks.append(f.replace(".txt", ""))

    # If no deck specified, return list of available decks
    if not deck_name:
        # Default to aqours_cup for "Load Test Deck" button compatibility
        deck_name = "aqours_cup"
        message = "Defaulting to 'aqours_cup'. Specify ?deck=NAME to load a specific deck."
    else:
        message = f"Loaded '{deck_name}'"

    # Find matching deck file
    deck_file = os.path.join(ai_decks_dir, f"{deck_name}.txt")
    if not os.path.exists(deck_file):
        return jsonify({"success": False, "error": f"Deck '{deck_name}' not found", "available_decks": available_decks})

    try:
        with open(deck_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Load card DB for parsing
        card_db_path = os.path.join(CURRENT_DIR, "..", "data", "cards.json")
        card_db = {}
        if os.path.exists(card_db_path):
            with open(card_db_path, "r", encoding="utf-8") as f_db:
                card_db = json.load(f_db)

        # Use the unified parser
        main_deck, energy_deck, type_counts, errors = extract_deck_data(content, card_db)

        return jsonify(
            {
                "success": True,
                "deck_name": deck_name,
                "content": main_deck,  # For compatibility with older frontend
                "main_deck": main_deck,
                "energy_deck": energy_deck,
                "available_decks": available_decks,
                "message": f"{message} ({len(main_deck)} Main, {len(energy_deck)} Energy)",
                "errors": errors,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/validate_cards", methods=["POST"])
def validate_cards():
    """Validate card IDs against the database and provide type breakdown."""
    data = request.json
    card_ids = data.get("card_ids", [])
    card_counts = data.get("card_counts", {})  # Optional: {card_id: quantity}

    # Ensure mapping is built
    if not card_no_to_id:
        print("DEBUG: validation - mapping empty, rebuilding...", flush=True)
        build_card_no_mapping()

    print(f"DEBUG: validation - map size: {len(card_no_to_id)}", flush=True)
    test_key = "PL!SP-bp1-004-R"
    if test_key in card_no_to_id:
        print(f"DEBUG: validation - found {test_key}: {card_no_to_id[test_key]}", flush=True)
    else:
        print(f"DEBUG: validation - {test_key} NOT FOUND in map!", flush=True)

    known = []
    unknown = []
    card_info = {}  # card_id -> {type, name, internal_id}

    # Type counters
    member_count = 0
    live_count = 0
    energy_count = 0

    for card_id in card_ids:
        # print(f"DEBUG: Checking {card_id}", flush=True)
        qty = card_counts.get(card_id, 1)
        norm_id = UnifiedDeckParser.normalize_code(card_id)
        if norm_id in card_no_to_id:
            internal_id = card_no_to_id[norm_id]
            known.append(card_id)

            # Determine type and get name
            if internal_id in member_db:
                card_info[card_id] = {"type": "Member", "name": member_db[internal_id].name}
                member_count += qty
            elif internal_id in live_db:
                card_info[card_id] = {"type": "Live", "name": live_db[internal_id].name}
                live_count += qty
            elif internal_id in energy_db:
                card_info[card_id] = {"type": "Energy", "name": energy_db[internal_id].name}
                energy_count += qty
        else:
            unknown.append(card_id)

    debug_info = {
        "map_size": len(card_no_to_id),
        "test_key_exists": "PL!SP-bp1-004-R" in card_no_to_id,
        "test_key_val": card_no_to_id.get("PL!SP-bp1-004-R", "N/A"),
        "first_5_keys": list(card_no_to_id.keys())[:5],
    }

    return jsonify(
        {
            "known": known,
            "unknown": unknown,
            "known_count": len(known),
            "unknown_count": len(unknown),
            "card_info": card_info,
            "breakdown": {"member": member_count, "live": live_count, "energy": energy_count},
            "_debug": debug_info,
        }
    )


@app.route("/api/clear_performance", methods=["POST"])
def clear_performance():
    room_id = get_room_id()
    with game_lock:
        room = get_room(room_id)
        if room:
            gs = room["state"]
            # Clear the results dictionary
            gs.performance_results.clear()
    return jsonify({"status": "ok"})


def record_game_state_to_history(room):
    """Save the current game state to the history stack, truncating any redo states."""
    if not room:
        return
    
    try:
        gs = room["state"]
        # In Rust engine, gs is typically a new object from gs.step().
        # We store the object itself to allow on-demand localization later.
        state_to_store = gs
        
        # Initialize history if not present (for backward compatibility)
        if "history_stack" not in room:
            room["history_stack"] = [state_to_store]
            room["history_index"] = 0
            return
        
        # Truncate redo states (if we're not at the end of history)
        history = room["history_stack"]
        idx = room["history_index"]
        if idx < len(history) - 1:
            room["history_stack"] = history[:idx + 1]
        
        # Add new state
        room["history_stack"].append(state_to_store)
        room["history_index"] = len(room["history_stack"]) - 1
        
        # Limit history size to prevent memory bloat (keep last 100 states)
        if len(room["history_stack"]) > 100:
            # Trim from the beginning
            excess = len(room["history_stack"]) - 100
            room["history_stack"] = room["history_stack"][excess:]
            room["history_index"] = max(0, room["history_index"] - excess)
    except Exception as e:
        print(f"Error recording game state to history: {e}")


@app.route("/api/action", methods=["POST"])
def do_action():
    room_id = get_room_id()
    session_token = request.headers.get("X-Session-Token")

    with game_lock:
        start_time = time.time()
        try:
            room = get_room(room_id)
            if not room:
                return jsonify({"success": False, "error": "Room not found"}), 404

            # Exit history mode if actively in it (history_index < end of history)
            history_stack = room.get("history_stack", [])
            history_index = room.get("history_index", 0)
            if history_stack and history_index < len(history_stack) - 1:
                # We're rewound/redone, truncate future history and continue from here
                room["history_stack"] = history_stack[:history_index + 1]
                room["history_index"] = history_index

            gs = room["state"]
            game_mode = room["mode"]
            ai_agent = room["ai_agent"]
            sessions = room.get("sessions", {})

            # Session Validation (Enforce Turn)
            if session_token and session_token in sessions:
                pid = sessions[session_token]
                if pid != -1:
                    # Check Pending Choice Turn
                    p_choices = getattr(gs, "pending_choices", [])
                    if p_choices:
                        # Handle both Rust (str, str) and Python (str, dict) formats
                        params = p_choices[0][1]
                        if isinstance(params, str):
                            # Rust format: parse JSON
                            try:
                                params = json.loads(params)
                            except:
                                params = {}
                        choice_pid = params.get("player_id", gs.current_player)
                        if choice_pid != pid:
                            return jsonify(
                                {"success": False, "error": f"Not your turn to choose (Waiting for P{choice_pid})"}
                            ), 403
                    # Check Main Turn
                    elif gs.current_player != pid:
                        return jsonify(
                            {"success": False, "error": f"Not your turn (Waiting for P{gs.current_player})"}
                        ), 403

            data = request.json
            action_id = data.get("action_id", 0)
            force = data.get("force", False)
            requester_idx = get_player_idx(room)

            if room.get("engine") == "rust" and requester_idx == gs.current_player and is_planner_root_phase(gs.phase):
                ensure_planner_session(room, gs, requester_idx)

            legal_mask = gs.get_legal_actions()

            # Validate Action
            if not (0 <= action_id < len(legal_mask)):
                return jsonify({"success": False, "error": "Invalid action ID"}), 400

            # Enforce Perspective/Active Player consistency in PvP
            if game_mode == "pvp":
                if requester_idx != gs.current_player:
                    # Special check for RPS phase: both players can act independently
                    # but if current_player is fixed on one, we may need to allow the other.
                    # In Rust engine, RPS actions usually don't care about current_player if they are valid.
                    # But if the backend blocks it, we have a lock.

                    # Logic: If phase is RPS or TurnChoice, allow both or ensure transition is smooth
                    is_special = (gs.phase in (Phase.RPS, Phase.TurnChoice)) or (
                        hasattr(gs.phase, "name") and gs.phase.name in ("RPS", "TurnChoice")
                    )
                    if not is_special:
                        return jsonify(
                            {"success": False, "error": f"Not your turn! It's P{gs.current_player + 1}'s turn."}
                        ), 403
            elif game_mode == "pve":
                # In PvE, normally block manual actions when it's the AI player's turn (P1).
                # However, special setup phases like RPS and TurnChoice allow both players
                # to submit choices independently — permit those here.
                is_special = (gs.phase in (Phase.RPS, Phase.TurnChoice)) or (
                    hasattr(gs.phase, "name") and gs.phase.name in ("RPS", "TurnChoice")
                )
                if gs.current_player == 1 and not is_special:
                    return jsonify({"success": False, "error": "AI is playing, please wait."}), 403

            is_legal = legal_mask[action_id]

            if force or is_legal:
                print(f"[DEBUG] Executing action {action_id} in phase {gs.phase} for player {gs.current_player}")
                # Step 1: Execute User Action
                res = gs.step(action_id)
                if room.get("engine") == "rust":
                    append_planner_action(room, requester_idx, action_id)
                if res is not None:
                    room["state"] = res
                    gs = res

                # Step 2: Auto-Advance & AI Handling
                max_safety = 50
                while not gs.is_terminal() and max_safety > 0:
                    max_safety -= 1
                    print(f"[DEBUG] Loop: phase={gs.phase} current_player={gs.current_player}")

                    # A. Automatic Phases (SETUP, 1=Active, 2=Energy, 3=Draw, 6=Perf1, 7=Perf2, 8=LiveResult)
                    if gs.phase == Phase.SETUP or gs.phase in (1, 2, 3, 6, 7, 8):
                        print(f"[DEBUG] Auto-advancing phase {gs.phase}")
                        res = gs.step(0)
                        if res is not None:
                            room["state"] = res
                            gs = res
                        continue

                    # B. AI Turn (P1) - ONLY if PVE
                    if gs.current_player == 1 and game_mode == "pve":
                        print(f"[DEBUG] AI taking turn in phase {gs.phase}")
                        if room.get("engine") == "rust":
                            gs.step_opponent_mcts(10)
                        else:
                            # Python AI
                            aid = ai_agent.choose_action(gs, 1)
                            res = gs.step(aid)
                            if res is not None:
                                room["state"] = res
                                gs = res
                        continue

                    print(f"[DEBUG] Breaking loop at phase {gs.phase}")
                    break

                viewer_idx = get_player_idx()
                lang = get_lang()
                duration = time.time() - start_time
                print(f"[PERF] /api/action took {duration:.3f}s (Action: {action_id})")
                if room.get("engine") == "rust":
                    maybe_finalize_planner_session(room, gs, requester_idx, lang)
                
                # Record state to history stack after successful action
                record_game_state_to_history(room)
                
                return jsonify(
                    {
                        "success": True,
                        "state": rust_serializer.serialize_state(gs, viewer_idx=viewer_idx, mode=game_mode, lang=lang),
                    }
                )
            else:
                return jsonify({"success": False, "error": f"Illegal action {action_id}"}), 400

        except Exception as e:
            import traceback

            traceback.print_exc()

            # Auto-report issue on crash
            try:
                report_dir = os.path.join(CURRENT_DIR, "reports")
                os.makedirs(report_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                crash_file = os.path.join(report_dir, f"crash_{timestamp}.json")

                try:
                    lang = get_lang()
                    if room is not None and room.get("engine") == "rust":
                        serialized_state = rust_serializer.serialize_state(
                            gs, viewer_idx=get_player_idx(), mode=game_mode, lang=lang
                        )
                    else:
                        serialized_state = serialize_state(
                            gs, viewer_idx=get_player_idx(), is_pvp=(game_mode == "pvp"), mode=game_mode, lang=lang
                        )

                    with open(crash_file, "w", encoding="utf-8") as f:
                        # Use app.json.dumps to handle Numpy types
                        f.write(
                            app.json.dumps(
                                {
                                    "error": str(e),
                                    "trace": traceback.format_exc(),
                                    "state": serialized_state,
                                }
                            )
                        )
                except Exception as inner_e:
                    # Fallback if serialization fails
                    with open(crash_file, "w", encoding="utf-8") as f:
                        f.write(
                            app.json.dumps(
                                {"error": str(e), "trace": traceback.format_exc(), "serialization_error": str(inner_e)}
                            )
                        )
            except:
                pass

            return jsonify({"success": False, "error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/")
def index_route():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(app.static_folder, path)


@app.route("/api/exec", methods=["POST"])
def god_mode():
    room_id = get_room_id()
    code = request.json.get("code", "")

    with game_lock:
        room = get_room(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found"})

        gs = room["state"]
        try:
            p = gs.active_player
            exec(code, {"state": gs, "p": p, "np": np})
            return jsonify(
                {"success": True, "state": serialize_state(gs, is_pvp=(room["mode"] == "pvp"), lang=get_lang())}
            )
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})


@app.route("/api/reset", methods=["POST"])
def reset():
    room_id = get_room_id()

    with game_lock:
        data = request.json or {}
        deck_type = data.get("deck_type", "normal")
        # Allow changing mode on reset
        new_mode = data.get("mode")  # Optional

        # Check if room exists to preserve existing params if not specified
        old_room = ROOMS.get(room_id)
        mode = new_mode if new_mode else (old_room["mode"] if old_room else "pve")

        ROOMS[room_id] = create_room_internal(room_id, mode, deck_type)
        room = ROOMS[room_id]

        # Check for custom decks and apply them if they exist for this room
        if old_room and "custom_decks" in old_room:
            room["custom_decks"] = old_room["custom_decks"]

        # Preserve sessions
        if old_room and "sessions" in old_room:
            room["sessions"] = old_room["sessions"]

        if deck_type == "custom":
            # Apply custom decks to the fresh state
            gs = room["state"]
            for pid in [0, 1]:
                cdeck = room["custom_decks"].get(pid)
                if cdeck and cdeck["main"]:
                    gs.players[pid].main_deck = convert_deck_strings_to_ids(cdeck["main"])
                    random.shuffle(gs.players[pid].main_deck)
                    # Re-draw hand?
                    gs.players[pid].hand = []
                    gs.players[pid].hand_added_turn = []
                    for _ in range(6):
                        if gs.players[pid].main_deck:
                            gs.players[pid].hand.append(gs.players[pid].main_deck.pop())
                            gs.players[pid].hand_added_turn.append(0)
                if cdeck and cdeck["energy"]:
                    # Re-fill energy
                    gs.players[pid].energy_deck = convert_deck_strings_to_ids(cdeck["energy"])
                    gs.players[pid].energy_zone = []
                    for _ in range(3):
                        if gs.players[pid].energy_deck:
                            gs.players[pid].energy_zone.append(gs.players[pid].energy_deck.pop(0))

        gs = room["state"]
        game_mode = room["mode"]

        # Auto-advance (AI goes first or Init steps)
        max_safety = 100
        while not gs.is_terminal() and max_safety > 0:
            max_safety -= 1
            # Automatic phases
            if gs.phase in (-2, 1, 2, 3, 6, 7, 8):
                gs.step(0)
                continue

            # AI Turn (P1)
            if gs.current_player == 1 and game_mode == "pve":
                gs.step_opponent_mcts(10)
                continue

            break  # P0 turn or user input needed

        return jsonify({"success": True, "state": rust_serializer.serialize_state(gs, mode=game_mode, lang=get_lang())})


@app.route("/api/ai_suggest", methods=["POST"])
def ai_suggest():
    room_id = get_room_id()
    data = request.json or {}
    sims = data.get("sims", 10)

    with game_lock:
        room = get_room(room_id)
        if not room:
            return jsonify({"error": "Room not found"}), 404

        gs = room["state"]
        # Only run if not terminal
        if gs.is_terminal():
            return jsonify({"suggestions": []})

        stats = gs.get_mcts_suggestions(sims)

        # Shim for get_action_desc
        class RustShim:
            def __init__(self, gs):
                self.phase = gs.phase
                self.current_player = gs.current_player
                self.active_player = gs.get_player(gs.current_player)
                self.member_db = member_db
                self.live_db = live_db
                self.pending_choices = []  # TODO: expose from rust if needed

        shim = RustShim(gs)

        # Enrich stats with descriptions
        enriched = []
        lang = get_lang()
        for action, value, visits in stats:
            desc = get_action_desc(action, shim, lang=lang)
            enriched.append({"action_id": action, "value": float(value), "visits": int(visits), "desc": desc})

        return jsonify({"success": True, "suggestions": enriched})


@app.route("/api/planner", methods=["GET"])
def get_turn_planner():
    room_id = get_room_id()

    with game_lock:
        room = ROOMS.get(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found"}), 404

        if room.get("engine") != "rust":
            return jsonify({"success": False, "error": "Turn planner is only available with the Rust engine."}), 400

        gs = room["state"]
        player_idx = get_player_idx(room)
        planner = build_planner_payload(room, gs, player_idx, get_lang())
        return jsonify({"success": True, "planner": planner})


@app.route("/api/planner/score", methods=["POST"])
def score_turn_planner_sequence():
    room_id = get_room_id()

    with game_lock:
        room = ROOMS.get(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found"}), 404

        if room.get("engine") != "rust":
            return jsonify({"success": False, "error": "Turn planner is only available with the Rust engine."}), 400

        gs = room["state"]
        player_idx = get_player_idx(room)
        planner_store = get_planner_store(room)
        session = planner_store["sessions"].get(str(player_idx))
        if not session:
            return jsonify({"success": False, "error": "No tracked player sequence is available to score."}), 400

        planner = build_planner_analysis_from_session(session, get_lang())
        planner["active"] = True
        planner["available"] = True
        return jsonify({"success": True, "planner": planner})


@app.route("/api/replays", methods=["GET"])
def list_replays():
    # 1. Root replays
    try:
        if os.path.exists("replays"):
            for f in os.listdir("replays"):
                if f.endswith(".json") and os.path.isfile(os.path.join("replays", f)):
                    replays.append({"filename": f, "folder": ""})

            # 2. Tournament subfolder
            tourney_dir = os.path.join("replays", "tournament")
            if os.path.exists(tourney_dir):
                for f in os.listdir(tourney_dir):
                    if f.endswith(".json"):
                        # We need to handle pathing. The frontend might expect just filename.
                        # But get_replay takes "filename".
                        # We should probably update get_replay to handle subpaths or encode it.
                        # For now let's just use the relative path as the filename
                        replays.append({"filename": f"tournament/{f}", "folder": "tournament"})

    except Exception as e:
        print(f"Error listing replays: {e}")
        return jsonify({"success": False, "error": str(e)})

    # Sort by filename desc (usually timestamp)
    replays.sort(key=lambda x: x["filename"], reverse=True)
    return jsonify({"success": True, "replays": replays})


def get_replay(filename):
    """Serve replay JSON files"""
    replay_path = f"replays/{filename}"
    if os.path.exists(replay_path):
        with open(replay_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Auto-inflate if it's an optimized replay
            if "registry" in data and "states" in data:
                print(f"Inflating optimized replay: {filename}")
                inflated_states = inflate_history(data, member_db, live_db, energy_db)
                # Reconstruct standard format
                data["states"] = inflated_states
                # Remove registry to avoid confusing frontend if it doesn't expect it
                del data["registry"]

            return jsonify(data)
    return jsonify({"error": "Replay not found"}), 404


@app.route("/api/advance", methods=["POST"])
def advance():
    room_id = get_room_id()
    with game_lock:
        room = get_room(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found"}), 404

        gs = room["state"]
        ai_agent = room["ai_agent"]

        # Run auto-advance loop
        max_safety = 50
        while not gs.is_terminal() and max_safety > 0:
            max_safety -= 1
            # Advance if in an automatic phase (AND no choices pending)
            if not gs.pending_choices and gs.phase in (
                Phase.ACTIVE,
                Phase.ENERGY,
                Phase.DRAW,
                Phase.PERFORMANCE_P1,
                Phase.PERFORMANCE_P2,
            ):
                gs = gs.step(0)
                room["state"] = gs
                continue

            # Determine who should act (Check pending choices first)
            next_actor = gs.current_player
            if gs.pending_choices:
                # Handle both Rust (str, str) and Python (str, dict) formats
                params = gs.pending_choices[0][1]
                if isinstance(params, str):
                    try:
                        params = json.loads(params)
                    except:
                        params = {}
                next_actor = params.get("player_id", gs.current_player)

            # If it's the AI's turn (P1) or the AI has a pending choice, let it act immediately
            if next_actor == 1 and not gs.is_terminal():
                aid = ai_agent.choose_action(gs, 1)
                gs = gs.step(aid)
                room["state"] = gs
                continue

            break

        return jsonify(
            {
                "success": True,
                "state": serialize_state(gs, is_pvp=(room["mode"] == "pvp"), mode=room["mode"], lang=get_lang()),
            }
        )


@app.route("/api/full_log", methods=["GET"])
def get_full_log():
    """Return the complete rule log without truncation."""
    room_id = get_room_id()
    with game_lock:
        room = get_room(room_id)
        if not room:
            return jsonify({"log": [], "total_entries": 0})
        gs = room["state"]
        return jsonify({"log": gs.rule_log, "total_entries": len(gs.rule_log)})


@app.route("/api/set_ai", methods=["POST"])
def set_ai():
    room_id = get_room_id()
    data = request.json
    mode = data.get("ai_mode", "smart")

    with game_lock:
        room = get_room(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found"})

        if mode == "random":
            room["ai_agent"] = RandomAgent()
        elif mode == "smart":
            room["ai_agent"] = SmartAgent()
        else:
            return jsonify({"success": False, "error": f"Unknown AI mode: {mode}"})

        return jsonify({"success": True, "mode": mode})


@app.route("/api/report_issue", methods=["POST"])
def report_issue():
    """Save the current game state and user explanation to a report file."""
    try:
        room_id = get_room_id()
        room = get_room(room_id)
        gs = room["state"] if room else None

        data = request.json
        explanation = data.get("explanation", "")
        # We can take the current state from the request or just use our global game_state
        # Providing it in the request is safer if the user is looking at a specific frame (e.g. in replay mode)
        # But for now, let's use the provided state if it exists, otherwise capture the current one.
        if room and room.get("engine") == "rust":
            serialized = rust_serializer.serialize_state(gs, viewer_idx=0, mode=room.get("mode", "pve"))
        else:
            serialized = serialize_state(gs, is_pvp=(room["mode"] == "pvp" if room else False))

        state_to_save = data.get("state") or serialized
        history = data.get("history", [])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("reports", exist_ok=True)

        filename = f"reports/report_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": timestamp,
                    "explanation": explanation,
                    "state": state_to_save,
                    "history": history,
                    "performance_history": state_to_save.get("performance_history", []),
                    "performance_results": state_to_save.get("performance_results", {}),
                    "action_desc": get_action_desc(state_to_save.get("last_action", 0), gs, lang=get_lang())
                    if gs and "last_action" in state_to_save
                    else "N/A",
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        return jsonify({"success": True, "filename": filename})
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/debug/rewind", methods=["POST"])
def debug_rewind():
    """Undo the last action by moving back in history."""
    room_id = get_room_id()
    
    with game_lock:
        room = get_room(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found"}), 404
        
        if "history_stack" not in room or not room["history_stack"]:
            return jsonify({"success": False, "error": "No history to rewind"}), 400
        
        # Move back one step if possible
        idx = room.get("history_index", 0)
        if idx > 0:
            room["history_index"] = idx - 1
            # Restore the previous state from history
            serialized_state = room["history_stack"][room["history_index"]]
            
            # We need to reconstruct the GameState from the serialized state
            # For now, we'll just return success and let the frontend fetch the new state
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Already at start of history"}), 400


@app.route("/api/debug/redo", methods=["POST"])
def debug_redo():
    """Redo the last undone action by moving forward in history."""
    room_id = get_room_id()
    
    with game_lock:
        room = get_room(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found"}), 404
        
        if "history_stack" not in room or not room["history_stack"]:
            return jsonify({"success": False, "error": "No history to redo"}), 400
        
        # Move forward one step if possible
        idx = room.get("history_index", 0)
        max_idx = len(room["history_stack"]) - 1
        if idx < max_idx:
            room["history_index"] = idx + 1
            # Restore the next state from history
            serialized_state = room["history_stack"][room["history_index"]]
            
            # We need to reconstruct the GameState from the serialized state
            # For now, we'll just return success and let the frontend fetch the new state
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Already at end of history"}), 400


@app.route("/api/export_game", methods=["GET"])
def export_game():
    """Export the current game state with history as minimal JSON."""
    room_id = get_room_id()
    
    with game_lock:
        room = get_room(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found"}), 404
        
        # Get current state
        gs = room["state"]
        game_mode = room["mode"]
        history_stack = room.get("history_stack", [])
        history_index = room.get("history_index", 0)
        
        # Serialize current state
        serialized = rust_serializer.serialize_state(gs, viewer_idx=0, mode=game_mode, lang=get_lang())
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "game_mode": game_mode,
            "current_state": serialized,
            "history": history_stack,
            "history_index": history_index,
            "custom_decks": room.get("custom_decks", {}),
        }
        
        return jsonify(export_data)


@app.route("/api/import_game", methods=["POST"])
def import_game():
    """Import a previously exported game state with full history."""
    room_id = get_room_id()
    data = request.json
    
    if not data or "current_state" not in data:
        return jsonify({"success": False, "error": "Invalid import data"}), 400
    
    with game_lock:
        room = get_room(room_id)
        if not room:
            return jsonify({"success": False, "error": "Room not found"}), 404
        
        try:
            # Restore history
            room["history_stack"] = data.get("history", [data.get("current_state")])
            room["history_index"] = data.get("history_index", 0)
            
            # The frontend should fetch the state after import to reconstruct GameState
            # For now, we'll store the import data and let the next fetchState reconstruct it
            room["pending_import_state"] = data.get("current_state")
            
            return jsonify({"success": True, "message": "Game imported successfully"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "error": str(e)}), 500


def generate_random_deck_list(member_db, live_db) -> list[str]:
    "Generate a valid random deck list (card_no strings)."
    deck = []

    # 1. Select Members (48)
    available_members = [c.card_no for c in member_db.values()]
    if available_members:
        member_bucket = []
        for m_no in available_members:
            member_bucket.extend([m_no] * 4)
        random.shuffle(member_bucket)
        while len(member_bucket) < 48:
            member_bucket.extend(available_members)
        deck.extend(member_bucket[:48])

    # 2. Select Lives (12)
    available_lives = [c.card_no for c in live_db.values()]
    if available_lives:
        live_bucket = []
        for l_no in available_lives:
            live_bucket.extend([l_no] * 4)
        random.shuffle(live_bucket)
        while len(live_bucket) < 12:
            live_bucket.extend(available_lives)
        deck.extend(live_bucket[:12])

    return deck


@app.route("/api/get_random_deck", methods=["GET"])
def get_random_deck_api():
    global member_db, live_db
    deck_list = generate_random_deck_list(member_db, live_db)
    return jsonify(
        {"success": True, "content": deck_list, "message": f"Generated Random Deck ({len(deck_list)} cards)"}
    )


@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Return list of preset decks from tests/presets.json."""
    try:
        preset_path = os.path.join(CURRENT_DIR, "..", "tests", "presets.json")
        if os.path.exists(preset_path):
            with open(preset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return jsonify({"success": True, "presets": data})
        return jsonify({"success": False, "error": "presets.json not found", "presets": []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    # PyInstaller Bundle Check
    if getattr(sys, "frozen", False):
        # If frozen, we might need to adjust static folder or templates folder depending on how flask finds them.
        # However, we added paths with --add-data, so they should be in sys._MEIPASS.
        # Flask's root_path defaults to __main__ directory, which in onefile mode is temporary.
        # We need to explicitly point static_folder to the MEIPASS location.
        bundle_dir = getattr(sys, "_MEIPASS", ".")  # type: ignore
        app.static_folder = os.path.join(bundle_dir, "web_ui")
        # app.template_folder = os.path.join(bundle_dir, 'templates') # if we used templates

        # Also need to make sure data loader finds 'data/cards.json'
        # CardDataLoader expects relative path. We might need to chdir or patch it.
        # Easiest is to chdir to the bundle dir so relative paths work?
        # BUT 'replays' need to be written to writable cwd, not temp dir.
        # So we should NOT chdir globally.
        # Instead, we should update filenames to be absolute paths based on bundle_dir if read-only.

        # Monkey patch the loader path just for this instance if needed,
        # but CardDataLoader takes a path arg.
        # We need to ensure 'init_game' calls it with the correct absolute path.
        pass

    # Patched init_game for Frozen state to find data
    original_init_game = init_game

    def frozen_init_game(deck_type="normal"):
        if getattr(sys, "frozen", False):
            bundle_dir = getattr(sys, "_MEIPASS", ".")  # type: ignore
            os.path.join(bundle_dir, "data", "cards.json")

            # We need to temporarily force the loader to use this path
            # But init_game hardcodes "data/cards.json" in correct logic?
            # actually checking init_game source:
            #   loader = CardDataLoader("data/cards.json")
            # We need to change that line or intercept.

            # Use os.chdir to temp dir for READS? No, we need writes to real dir.
            # Best way: Just ensure data/cards.json exists in CWD? No, user won't have it.

            # HACK: We can't easily change the hardcoded string inside init_game without rewriting it.
            # However, we can patch CardDataLoader class to fix the path!
            # Assuming CardDataLoader is imported from engine.game.data_loader
            from engine.game.data_loader import CardDataLoader

            ops_init = CardDataLoader.__init__

            def new_init(self, filepath):
                if not os.path.exists(filepath) and getattr(sys, "frozen", False):
                    # Try bundle path
                    bundle_path = os.path.join(sys._MEIPASS, filepath)  # type: ignore
                    if os.path.exists(bundle_path):
                        filepath = bundle_path
                ops_init(self, filepath)

            CardDataLoader.__init__ = new_init  # type: ignore[method-assign]

        original_init_game(deck_type)

    init_game = frozen_init_game

    # Run Server
    # use_reloader=False is crucial for PyInstaller to implicit avoid spawning subprocesses incorrectly
    port = int(os.environ.get("PORT", 8000))

    # Auto-open browser
    import webbrowser
    from threading import Timer

    def open_browser():
        webbrowser.open_new(f"http://localhost:{port}/")

    if not getattr(sys, "frozen", False) or os.environ.get("OPEN_BROWSER", "true").lower() == "true":
        Timer(1.5, open_browser).start()

    # Start Background Game Loop
    if game_thread is None:
        game_thread = threading.Thread(target=background_game_loop, daemon=True)
        game_thread.start()

if __name__ == "__main__":
    load_game_data()  # Ensure data is loaded

    port = int(os.environ.get("PORT", 7860))
    local_ip = get_local_ip()

    print("\n" + "=" * 50)
    print("Love Live Card Game Server Running!")
    print(f"Local:   http://localhost:{port}")
    print(f"Network: http://{local_ip}:{port}")
    print("=" * 50 + "\n")

    # In production/container, usually don't want debug mode
    debug_mode = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
