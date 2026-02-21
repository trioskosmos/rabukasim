"""
Ability Validator - Tests card abilities with AI/User parity checks.

Compares what the AI agent sees (raw legal action bitmask) with what
the User sees in the action bar (serialized legal_actions).
"""

import argparse
import json
import multiprocessing
import os
import sys
import time
import traceback

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
ENGINE_PATH = os.path.join(PROJECT_ROOT, "engine")
if ENGINE_PATH not in sys.path:
    sys.path.insert(0, ENGINE_PATH)

import engine_rust
from game.data_loader import CardDataLoader

from backend.rust_serializer import RustGameStateSerializer


def get_state_snapshot(gs, p_idx=0):
    """Captures a snapshot of the player's state for delta comparison."""
    p = gs.get_player(p_idx)
    return {
        "hand_size": len(p.hand),
        "discard_size": len(p.discard),
        "score": p.score,
        "energy_size": len(p.energy_zone),
        "tapped_count": sum(1 for t in p.tapped_energy if t),
        "stage": list(p.stage),
        "heart_buffs": [list(h) for h in p.heart_buffs],  # List of 7 colors
        "blade_buffs": list(p.blade_buffs),
    }


def validate_card_worker(args):
    """
    Worker function to validate a single card.
    Args:
        args: tuple containing (card_tuple, plinth_cid, energy_cid, m_ids, l_ids, compiled_json_str, member_db_data, live_db_data, energy_db_data)
    """
    (cid, card_obj_data, card_type), plinth_cid, energy_cid, m_ids, l_ids, compiled_json_str, m_db, l_db, e_db = args

    # Reconstruct card object data
    card_label = card_obj_data.card_no

    # Re-initialize Rust DB and Serializer in worker
    try:
        rust_db = engine_rust.PyCardDatabase(compiled_json_str)
        serializer = RustGameStateSerializer(m_db, l_db, e_db)
    except Exception as e:
        return {
            "card_no": card_label,
            "status": "CRASH",
            "error": f"Worker init failed: {e}",
            "traceback": traceback.format_exc(),
        }

    # Result container for this card
    card_result = {
        "card_no": card_label,
        "status": "UNKNOWN",
        "parity_gaps": [],
        "crashes": [],
        "hangs": [],
        "dormant": False,
        "skipped": False,
        "reason": "",  # For skips/dormant
    }

    # --- NEW CHECK: Lost Compiled Abilities ---
    # compiled_json_str is already available.
    try:
        comp_dict = json.loads(compiled_json_str)
        comp_card = comp_dict.get(str(cid))
        has_text = hasattr(card_obj_data, "ability") and card_obj_data.ability and card_obj_data.ability != "なし"
        if has_text and comp_card:
            if not comp_card.get("abilities", []):
                card_result["status"] = "CRASH"
                card_result["crashes"].append(
                    {
                        "card_no": card_label,
                        "action_id": -1,
                        "error": "Card has ability text but generated 0 compiled abilities (Missing TRIGGER / Parser failure)",
                        "traceback": "",
                    }
                )
                return card_result
    except Exception:
        pass

    try:
        # Create fresh game state
        gs = engine_rust.PyGameState(rust_db)

        # Dummy decks for initialization
        p0_deck = [plinth_cid] * 60
        p1_deck = [m_ids[0]] * 60 if m_ids else [plinth_cid] * 60
        p0_energy = [energy_cid] * 60
        p1_energy = [energy_cid] * 60
        p0_lives = l_ids[:3] if len(l_ids) >= 3 else l_ids
        p1_lives = l_ids[:3] if len(l_ids) >= 3 else l_ids

        # with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

        # === GOD MODE SETUP ===
        p0 = gs.get_player(0)
        p0.energy_zone = [energy_cid] * 12
        p0.tapped_energy = [False] * 12
        gs.set_player(0, p0)

        # Place plinth(s) on stage
        gs.set_stage_card(0, 0, plinth_cid)
        if card_type == "LIVE":
            gs.set_stage_card(0, 1, plinth_cid)
            gs.set_stage_card(0, 2, plinth_cid)

        # Set hand to target card only
        gs.set_hand_cards(0, [cid])

        # Set phase
        gs.turn = 1
        gs.current_player = 0
        if card_type == "MEMBER":
            gs.phase = 4  # Main
        else:
            gs.phase = 5  # LiveSet

        # Play the card
        # Action space: 1-180 for members (slot_idx + hand_idx*3), 400+ for live cards
        play_action = 1 if card_type == "MEMBER" else 400

        if card_type == "MEMBER":
            legal = gs.get_legal_actions()
            if not legal[play_action]:
                # Try other slots
                for slot in [1, 2]:
                    alt_action = 1 + slot
                    if legal[alt_action]:
                        play_action = alt_action
                        break
                else:
                    # Still not playable
                    p0 = gs.get_player(0)
                    untapped = sum(1 for t in p0.tapped_energy if not t)
                    card_cost = card_obj_data.cost if hasattr(card_obj_data, "cost") else 0
                    card_result["status"] = "SKIPPED"
                    card_result["skipped"] = True
                    card_result["reason"] = f"Energy: {untapped}/12, Cost: {card_cost}"
                    return card_result

        # Take snapshot before play
        pre_snap = get_state_snapshot(gs, 0)

        try:
            # with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            gs.step(play_action)
        except Exception as e:
            card_result["status"] = "CRASH"
            card_result["crashes"].append(
                {
                    "card_no": card_label,
                    "action_id": play_action,
                    "error": f"Play action failed: {e}",
                    "traceback": traceback.format_exc(),
                }
            )
            return card_result

        # Handle Response phase if triggered
        response_steps = 0
        while gs.phase == 10 and response_steps < 5:
            legal = gs.get_legal_actions()
            choices = [i for i, v in enumerate(legal) if v]
            if not choices:
                break
            choice = 0 if legal[0] else choices[0]
            try:
                # with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                gs.step(choice)
            except Exception as e:
                card_result["status"] = "CRASH"
                card_result["crashes"].append(
                    {
                        "card_no": card_label,
                        "action_id": choice,
                        "error": f"Response choice failed: {e}",
                        "traceback": traceback.format_exc(),
                    }
                )
                return card_result
            response_steps += 1

        # Get AI view (raw bitmask)
        raw_mask = gs.get_legal_actions()
        ai_action_ids = set(i for i, v in enumerate(raw_mask) if v)

        # Get User view (serialized for frontend)
        state_view = serializer.serialize_state(gs, viewer_idx=0)
        user_action_ids = set(a["id"] for a in state_view.get("legal_actions", []))

        # Parity check
        missing_from_user = ai_action_ids - user_action_ids
        if missing_from_user:
            for aid in missing_from_user:
                card_result["parity_gaps"].append(
                    {"card_no": card_label, "action_id": aid, "issue": "AI can see action but User cannot"}
                )

        # Execute ability actions (200-299)
        ability_actions = [a for a in ai_action_ids if 200 <= a <= 299]
        executed_ok = True

        for aid in ability_actions:
            try:
                start = time.time()
                # with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                gs.step(aid)
                elapsed = time.time() - start

                if elapsed > 2.0:
                    card_result["hangs"].append({"card_no": card_label, "action_id": aid, "time_sec": elapsed})
                    # We don't mark executed_ok = False for hangs, just log it.
            except Exception as e:
                card_result["crashes"].append({"card_no": card_label, "action_id": aid, "error": str(e)})
                executed_ok = False

        # Take snapshot after everything
        post_snap = get_state_snapshot(gs, 0)

        # Delta Verification
        has_ability = hasattr(card_obj_data, "ability") and card_obj_data.ability and card_obj_data.ability != "なし"
        if executed_ok and has_ability:
            deltas = []
            if post_snap["hand_size"] != pre_snap["hand_size"] - (1 if card_type == "MEMBER" else 0):
                deltas.append("hand")
            if post_snap["discard_size"] > pre_snap["discard_size"]:
                deltas.append("discard")
            if post_snap["score"] > pre_snap["score"]:
                deltas.append("score")

            buff_found = False
            for s_idx in range(3):
                if sum(post_snap["heart_buffs"][s_idx]) > sum(pre_snap["heart_buffs"][s_idx]):
                    buff_found = True
                if post_snap["blade_buffs"][s_idx] > pre_snap["blade_buffs"][s_idx]:
                    buff_found = True
            if buff_found:
                deltas.append("buffs")

            if not deltas:
                card_result["dormant"] = True
                card_result["reason"] = "No state change detected"

        if not card_result["crashes"] and not card_result["parity_gaps"]:
            card_result["status"] = "SUCCESS"
        else:
            card_result["status"] = "FAILED"

        return card_result

    except Exception as e:
        return {
            "card_no": card_label,
            "status": "CRASH",
            "error": f"Worker unhandled exception: {e}",
            "traceback": traceback.format_exc(),
        }


def validate_abilities(limit=None, card_filter=None, verbose=False, parallel=False):
    """Main validation function."""
    print("=" * 60)
    print("ABILITY VALIDATOR (God Mode + Baton Pass)")
    if parallel:
        print(f"Parallel Mode: {multiprocessing.cpu_count()} cores")
    print("=" * 60)

    # Load data
    print("Loading card data...")
    loader = CardDataLoader("data/cards.json")
    member_db, live_db, energy_db = loader.load()

    # Find Ultimate Plinth
    ULTIMATE_PLINTH = "PL!SP-bp4-004-R＋"
    plinth_cid = None
    for cid, m_card in member_db.items():
        if m_card.card_no == ULTIMATE_PLINTH:
            plinth_cid = cid
            break
    if not plinth_cid:
        plinth_cid = max(member_db.keys(), key=lambda c: member_db[c].cost)

    # Find energy card ID
    energy_cid = list(energy_db.keys())[0] if energy_db else 40000

    compiled_path = "data/cards_compiled.json"
    if not os.path.exists(compiled_path):
        print(f"ERROR: {compiled_path} not found. Run `uv run python -m compiler.main` first.")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        compiled_json_str = f.read()

    # Results
    results = {
        "timestamp": time.strftime("%Y%m%d_%H%M%S"),
        "plinth_used": ULTIMATE_PLINTH,
        "total_cards": 0,
        "tested": 0,
        "success": [],
        "parity_gaps": [],
        "crashes": [],
        "hangs": [],
        "dormant": [],
        "skipped": [],
    }

    # Prepare test list
    members_to_test = [(cid, m, "MEMBER") for cid, m in member_db.items()]
    lives_to_test = [(cid, l, "LIVE") for cid, l in live_db.items()]
    all_to_test = members_to_test + lives_to_test

    if card_filter:
        filters = [f.strip().lower() for f in card_filter.split(",")]
        all_to_test = [c for c in all_to_test if any(f in c[1].card_no.lower() for f in filters)]

    all_to_test.sort(key=lambda x: x[1].card_no)

    if limit:
        all_to_test = all_to_test[:limit]

    m_ids = list(member_db.keys())
    l_ids = list(live_db.keys())
    results["total_cards"] = len(all_to_test)

    print(f"Testing {len(all_to_test)} cards (Plinth: {ULTIMATE_PLINTH})...")
    print("-" * 60)

    start_time = time.time()

    # Prepare worker args
    worker_args = []
    for card_tuple in all_to_test:
        # (card_tuple, plinth_cid, energy_cid, m_ids, l_ids, compiled_json_str, m_db, l_db, e_db)
        worker_args.append(
            (card_tuple, plinth_cid, energy_cid, m_ids, l_ids, compiled_json_str, member_db, live_db, energy_db)
        )

    if parallel:
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            # imap_unordered used to yield results as they complete
            for i, res in enumerate(pool.imap_unordered(validate_card_worker, worker_args)):
                process_result(res, results, verbose)

                # Progress update every 10 items
                if (i + 1) % 10 == 0:
                    elapsed = time.time() - start_time
                    speed = (i + 1) / elapsed
                    print(f"Progress: {i + 1}/{len(worker_args)} ({speed:.1f} cards/sec)")
    else:
        # Sequential
        for i, args in enumerate(worker_args):
            res = validate_card_worker(args)
            process_result(res, results, verbose)
            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{len(worker_args)}")

    elapsed_total = time.time() - start_time
    print("-" * 60)
    print("RESULTS SUMMARY")
    print("-" * 60)
    print(f"Total cards:    {results['total_cards']}")
    print(f"Tested:         {results['tested']}")
    print(f"Success:        {len(results['success'])}")
    print(f"Parity Gaps:    {len(results['parity_gaps'])}")
    print(f"Crashes:        {len(results['crashes'])}")
    print(f"Hangs:          {len(results['hangs'])}")
    print(f"Dormant:        {len(results['dormant'])}")
    print(f"Skipped:        {len(results['skipped'])}")
    print(f"Total Time:     {elapsed_total:.2f}s")

    # Save report
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/ability_validation_{results['timestamp']}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Report saved to: {report_path}")
    print("=" * 60)

    return results


def process_result(res, results, verbose):
    """Aggregates a worker result into the main results dict."""
    card_label = res["card_no"]

    if res["status"] == "SKIPPED":
        results["skipped"].append({"card_no": card_label, "reason": res["reason"]})
        if verbose:
            print(f"SKIP {card_label}: {res['reason']}")
    elif res["status"] == "CRASH":
        results["crashes"].append(res)  # Res contains details
        if verbose:
            print(f"CRASH {card_label}: {res.get('error', '')}")
    else:
        results["tested"] += 1

        # Parity
        for gap in res["parity_gaps"]:
            results["parity_gaps"].append(gap)
            if verbose:
                print(f"PARITY GAP {card_label}: {gap['issue']}")

        # Hangs
        for hang in res["hangs"]:
            results["hangs"].append(hang)
            if verbose:
                print(f"HANG {card_label}: {hang['time_sec']}s")

        # Crashes (partial)
        for crash in res["crashes"]:
            results["crashes"].append(crash)
            if verbose:
                print(f"CRASH {card_label} (Action): {crash['error']}")

        # Dormant
        if res["dormant"]:
            results["dormant"].append(card_label)
            if verbose:
                print(f"DORMANT {card_label}")

        # Success
        if res["status"] == "SUCCESS":
            results["success"].append(card_label)

    if verbose and res["status"] == "SUCCESS":
        print(f"OK {card_label}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate card abilities for AI/User parity")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cards to test")
    parser.add_argument("--filter", type=str, default=None, help="Filter cards by card_no substring")
    parser.add_argument("--parallel", action="store_true", help="Run in parallel using all CPU cores")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    validate_abilities(limit=args.limit, card_filter=args.filter, verbose=args.verbose, parallel=args.parallel)
