use tiny_http::{Request, Response, Header};
use serde_json::{json, Value};
use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex, MutexGuard};
use std::thread;
use std::collections::{HashMap, VecDeque};
use uuid::Uuid;
use engine_rust::core::logic::{GameState, StandardizedState};
use engine_rust::core::logic::Phase;
use engine_rust::core::mcts::{MCTS, SearchHorizon};

// Removed SearchHorizon, EvalMode imports as they were unused
// Removed unused Request types from import
use crate::models::{AppState, Room, CreateRoomReq, JoinRoomReq, ActionReq, UploadDeckReq, SetDeckReq};
use crate::serialization::{serialize_state_rich, get_action_desc_rich};
use crate::utils::{parse_body, generate_room_code, get_header, resolve_deck, get_random_valid_deck, parse_deck_content, load_named_deck, normalize_card_code};
use crate::Decks;

const MAX_HISTORY_SNAPSHOTS: usize = 100;

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
struct EditablePlayerState {
    stage: Option<Vec<Value>>,
    live_zone: Option<Vec<Value>>,
    hand: Option<Vec<Value>>,
    energy: Option<Vec<Value>>,
    energy_zone: Option<Vec<Value>>,
    success_lives: Option<Vec<Value>>,
    success_zone: Option<Vec<Value>>,
    success_pile: Option<Vec<Value>>,
    discard: Option<Vec<Value>>,
    looked_cards: Option<Vec<Value>>,
    deck: Option<Vec<Value>>,
    energy_deck: Option<Vec<Value>>,
    score: Option<u32>,
    tapped_energy_mask: Option<u64>,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
struct EditableGameState {
    phase: Option<Value>,
    prev_phase: Option<Value>,
    turn: Option<u16>,
    current_player: Option<u8>,
    active_player: Option<u8>,
    first_player: Option<u8>,
    prev_card_id: Option<i32>,
    debug_mode: Option<bool>,
    players: Option<Vec<EditablePlayerState>>,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
struct GameImportPayload {
    state: Option<Value>,
    current_state: Option<Value>,
    history: Option<Vec<Value>>,
    history_index: Option<usize>,
    mode: Option<String>,
}

fn lock_recover<'a, T>(mutex: &'a Mutex<T>, label: &str) -> MutexGuard<'a, T> {
    match mutex.lock() {
        Ok(guard) => guard,
        Err(poisoned) => {
            eprintln!("[API] Recovering poisoned mutex: {}", label);
            poisoned.into_inner()
        }
    }
}

fn get_query_param(query: Option<&str>, key: &str) -> Option<String> {
    query.and_then(|query_string| {
        query_string.split('&').find_map(|entry| {
            let (entry_key, entry_value) = entry.split_once('=')?;
            if entry_key == key {
                Some(entry_value.to_string())
            } else {
                None
            }
        })
    })
}

fn resolve_viewer_idx(request: &Request, query: Option<&str>, room: &Room) -> usize {
    if let Some(session_token) = get_header(request, "X-Session-Token") {
        if let Some(&viewer_idx) = room.players.get(&session_token) {
            return viewer_idx;
        }
    }

    if let Some(raw_viewer) = get_query_param(query, "viewer")
        .or_else(|| get_header(request, "X-Player-Idx"))
    {
        if let Ok(viewer_idx) = raw_viewer.parse::<usize>() {
            return viewer_idx.min(1);
        }
    }

    0
}

fn ensure_history_initialized(room: &mut Room) {
    if room.history_timeline.is_empty() {
        room.history_timeline.push_back(room.state.clone());
        room.history_cursor = 0;
        return;
    }

    if room.history_cursor >= room.history_timeline.len() {
        room.history_cursor = room.history_timeline.len().saturating_sub(1);
    }
}

fn replace_history_with_single_state(room: &mut Room) {
    room.history_timeline.clear();
    room.history_timeline.push_back(room.state.clone());
    room.history_cursor = 0;
}

fn append_current_state_to_history(room: &mut Room) {
    ensure_history_initialized(room);

    while room.history_timeline.len() > room.history_cursor + 1 {
        room.history_timeline.pop_back();
    }

    let should_append = room
        .history_timeline
        .back()
        .map(|snapshot| snapshot != &room.state)
        .unwrap_or(true);

    if should_append {
        room.history_timeline.push_back(room.state.clone());
        if room.history_timeline.len() > MAX_HISTORY_SNAPSHOTS {
            room.history_timeline.pop_front();
            room.history_cursor = room.history_cursor.saturating_sub(1);
        }
    }

    room.history_cursor = room.history_timeline.len().saturating_sub(1);
}

fn move_history_cursor(room: &mut Room, new_cursor: usize) -> Result<(), String> {
    ensure_history_initialized(room);
    if new_cursor >= room.history_timeline.len() {
        return Err("History cursor out of range".to_string());
    }

    room.history_cursor = new_cursor;
    room.state = room.history_timeline[new_cursor].clone();
    Ok(())
}

fn parse_card_id(value: &Value) -> Result<i32, String> {
    match value {
        Value::Null => Ok(-1),
        Value::Number(number) => {
            let raw = number
                .as_i64()
                .ok_or_else(|| format!("Card id out of range: {number}"))?;
            i32::try_from(raw).map_err(|_| format!("Card id out of range: {raw}"))
        }
        Value::Object(map) => {
            if let Some(id) = map.get("id").or_else(|| map.get("card_id")) {
                parse_card_id(id)
            } else {
                Err("Card object is missing 'id' or 'card_id'".to_string())
            }
        }
        _ => Err(format!("Unsupported card entry: {value}")),
    }
}

fn parse_card_vec(value: &[Value]) -> Result<Vec<i32>, String> {
    value.iter().map(parse_card_id).collect()
}

fn parse_zone3(value: &[Value]) -> Result<[i32; 3], String> {
    let mut zone = [-1; 3];
    for (idx, entry) in value.iter().take(3).enumerate() {
        zone[idx] = parse_card_id(entry)?;
    }
    Ok(zone)
}

fn parse_phase_value(value: &Value) -> Result<Phase, String> {
    serde_json::from_value::<Phase>(value.clone())
        .map_err(|err| format!("Invalid phase value: {err}"))
}

fn apply_editable_state_patch(current: &GameState, payload: EditableGameState) -> Result<GameState, String> {
    let mut next = current.clone();

    if let Some(phase) = payload.phase.as_ref() {
        next.phase = parse_phase_value(phase)?;
    }
    if let Some(prev_phase) = payload.prev_phase.as_ref() {
        next.prev_phase = parse_phase_value(prev_phase)?;
    }
    if let Some(turn) = payload.turn {
        next.turn = turn;
    }
    if let Some(current_player) = payload.current_player.or(payload.active_player) {
        next.current_player = current_player.min(1);
    }
    if let Some(first_player) = payload.first_player {
        next.first_player = first_player.min(1);
    }
    if let Some(prev_card_id) = payload.prev_card_id {
        next.prev_card_id = prev_card_id;
    }
    if let Some(debug_mode) = payload.debug_mode {
        next.debug.debug_mode = debug_mode;
    }

    if let Some(players) = payload.players {
        for (idx, player_patch) in players.into_iter().enumerate().take(2) {
            let player = &mut next.players[idx];

            if let Some(stage) = player_patch.stage.as_ref() {
                player.stage = parse_zone3(stage)?;
                for slot in 0..3 {
                    if player.stage[slot] < 0 {
                        player.stage_energy[slot].clear();
                        player.stage_energy_count[slot] = 0;
                        player.set_tapped(slot, false);
                        player.set_moved(slot, false);
                    }
                }
            }
            if let Some(live_zone) = player_patch.live_zone.as_ref() {
                player.live_zone = parse_zone3(live_zone)?;
            }
            if let Some(hand) = player_patch.hand.as_ref() {
                player.hand = parse_card_vec(hand)?.into();
            }
            if let Some(discard) = player_patch.discard.as_ref() {
                player.discard = parse_card_vec(discard)?.into();
            }
            if let Some(looked_cards) = player_patch.looked_cards.as_ref() {
                player.looked_cards = parse_card_vec(looked_cards)?.into();
            }
            if let Some(deck) = player_patch.deck.as_ref() {
                player.deck = parse_card_vec(deck)?.into();
            }
            if let Some(energy_deck) = player_patch.energy_deck.as_ref() {
                player.energy_deck = parse_card_vec(energy_deck)?.into();
            }

            let energy_patch = player_patch.energy.as_ref().or(player_patch.energy_zone.as_ref());
            if let Some(energy) = energy_patch {
                player.energy_zone = parse_card_vec(energy)?.into();
                if player_patch.tapped_energy_mask.is_none() {
                    player.tapped_energy_mask = 0;
                }
            }
            if let Some(success_lives) = player_patch
                .success_lives
                .as_ref()
                .or(player_patch.success_zone.as_ref())
                .or(player_patch.success_pile.as_ref())
            {
                player.success_lives = parse_card_vec(success_lives)?.into();
            }
            if let Some(score) = player_patch.score {
                player.score = score;
            }
            if let Some(tapped_energy_mask) = player_patch.tapped_energy_mask {
                player.tapped_energy_mask = tapped_energy_mask;
            }
        }
    }

    Ok(next)
}

fn parse_debug_state_payload(current: &GameState, payload: Value) -> Result<GameState, String> {
    if let Some(export_state) = payload
        .get("current_state")
        .or_else(|| payload.get("state"))
        .cloned()
    {
        return parse_debug_state_payload(current, export_state);
    }

    match serde_json::from_value::<GameState>(payload.clone()) {
        Ok(mut state) => {
            state.debug = current.debug.clone();
            Ok(state)
        }
        Err(full_err) => match serde_json::from_value::<EditableGameState>(payload) {
            Ok(editable) => apply_editable_state_patch(current, editable),
            Err(edit_err) => Err(format!(
                "State payload did not match a raw GameState or editable checkpoint. Raw parse: {full_err}; editable parse: {edit_err}"
            )),
        },
    }
}

fn import_history_payload(room: &mut Room, payload: GameImportPayload) -> Result<(), String> {
    let base_state = room.state.clone();
    let history_values = payload.history.unwrap_or_default();

    let mut timeline = VecDeque::new();
    for entry in history_values {
        timeline.push_back(parse_debug_state_payload(&base_state, entry)?);
    }

    if timeline.is_empty() {
        let current_value = payload
            .current_state
            .or(payload.state)
            .ok_or_else(|| "Import payload is missing 'state' or 'current_state'".to_string())?;
        timeline.push_back(parse_debug_state_payload(&base_state, current_value)?);
    }

    let mut cursor = payload.history_index.unwrap_or_else(|| timeline.len().saturating_sub(1));
    if cursor >= timeline.len() {
        cursor = timeline.len().saturating_sub(1);
    }

    while timeline.len() > MAX_HISTORY_SNAPSHOTS {
        timeline.pop_front();
        cursor = cursor.saturating_sub(1);
    }

    room.history_timeline = timeline;
    room.history_cursor = cursor;
    room.state = room.history_timeline[cursor].clone();
    Ok(())
}

pub fn handle_api_request(mut request: Request, path: &str, query: Option<&str>, state: Arc<AppState>) {
    let mut response_json = String::new();
    let mut status = 200;

    println!("[API] Request: {}", path);
    match path {
        "api/status" => {
            let rooms = lock_recover(&state.rooms, "app_state.rooms");
            response_json = json!({
                "status": "rust_server",
                "instance_id": state.server_instance_id,
                "rooms": rooms.len(),
                "members": state.card_db.members.len(),
                "lives": state.card_db.lives.len()
            }).to_string();
        },
        "api/rooms/create" => {
            let body_res = parse_body::<CreateRoomReq>(&mut request);
            if let Ok(body) = body_res {
                let mut rooms = lock_recover(&state.rooms, "app_state.rooms");
                let room_id = generate_room_code();
                let token = Uuid::new_v4().to_string();

                let mut players = HashMap::new();
                players.insert(token.clone(), 0); // Creator is P0

                let mut username_to_token = HashMap::new();
                if let Some(user) = &body.username {
                    username_to_token.insert(user.clone(), token.clone());
                }

                let mut game_state = GameState::default();
                game_state.debug.debug_mode = state.debug_mode;
                let mut pending_decks = [None, None];

                let is_pve = body.mode.as_deref() == Some("pve");
                if let (Some(p0_main), Some(p0_energy)) = (&body.p0_deck, &body.p0_energy) {
                    let p0 = resolve_deck(p0_main, p0_energy, &state.card_db);

                    let p1 = if let (Some(p1_main), Some(p1_energy)) = (&body.p1_deck, &body.p1_energy) {
                        resolve_deck(p1_main, p1_energy, &state.card_db)
                    } else {
                         get_random_valid_deck(&state.card_db)
                    };

                    pending_decks[0] = Some(p0.clone());
                    if is_pve || body.p1_deck.is_some() {
                        pending_decks[1] = Some(p1.clone());
                    }

                    if is_pve || (pending_decks[0].is_some() && pending_decks[1].is_some()) {
                        let mut p0_main = p0.members.clone();
                        p0_main.extend(p0.lives.iter());
                        let mut p1_main = p1.members.clone();
                        p1_main.extend(p1.lives.iter());

                        game_state.initialize_game(
                            p0_main, p1_main,
                            p0.energy.clone(), p1.energy.clone(),
                            Vec::new(), Vec::new(),
                        );
                        pending_decks = [None, None];
                    }
                }

                let mode_str = body.mode.clone().unwrap_or_else(|| "pve".to_string());
                let is_vanilla = body.card_set.as_deref() == Some("vanilla");
                let mut initial_history = VecDeque::new();
                initial_history.push_back(game_state.clone());

                let new_room = Room {
                    _id: room_id.clone(),
                    state: game_state,
                    players,
                    username_to_token,
                    mode: mode_str.clone(),
                    is_vanilla,
                    last_update: std::time::SystemTime::now(),
                    created_at: std::time::SystemTime::now(),
                    is_public: body.public.unwrap_or(false),
                    pending_decks,
                    is_ai_thinking: false,
                    ai_status: String::new(),
                    history_timeline: initial_history,
                    history_cursor: 0,
                };

                let room_arc = Arc::new(Mutex::new(new_room));
                rooms.insert(room_id.clone(), room_arc);
                println!("[API] SUCCESS: Created room {} (mode: {}, vanilla: {}). Decks: P0={}, P1={}",
                    room_id, mode_str, is_vanilla,
                    body.p0_deck.as_ref().map(|d| d.len()).unwrap_or(0),
                    body.p1_deck.as_ref().map(|d| d.len()).unwrap_or(0)
                );
                let card_set_str = if is_vanilla { "vanilla" } else { "compiled" };
                response_json = json!({ "success": true, "room_id": room_id, "session": token, "player_idx": 0, "card_set": card_set_str }).to_string();
            } else {
                status = 400;
                let err_msg = body_res.err().unwrap_or_else(|| "Unknown error".to_string());
                response_json = json!({"error": "Invalid body"}).to_string();
                println!("[API] FAILED to create room: {}", err_msg);
            }
        },
        "api/rooms/list" => {
            let rooms = lock_recover(&state.rooms, "app_state.rooms");
            let public_rooms: Vec<Value> = rooms.values()
                .filter_map(|r_arc| {
                    let r = lock_recover(r_arc.as_ref(), "room");
                    if r.is_public {
                        Some(json!({ "id": r._id, "mode": r.mode, "players_count": r.players.len() }))
                    } else {
                        None
                    }
                })
                .collect();
            response_json = json!({ "rooms": public_rooms }).to_string();
        },
        "api/rooms/join" => {
            if let Ok(body) = parse_body::<JoinRoomReq>(&mut request) {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&body.room_id) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    if room.players.len() >= 2 {
                         status = 400; response_json = json!({"error": "Full"}).to_string();
                    } else {
                         let token = Uuid::new_v4().to_string();
                         room.players.insert(token.clone(), 1); // Joiner is P1
                         if let Some(user) = &body.username {
                             room.username_to_token.insert(user.clone(), token.clone());
                         }
                         let card_set_str = if room.is_vanilla { "vanilla" } else { "compiled" };
                         response_json = json!({ "success": true, "session": token, "player_idx": 1, "card_set": card_set_str }).to_string();
                    }
                } else { status = 404; response_json = json!({"error": "Not found"}).to_string(); }
            } else { status = 400; }
        },
        "api/state" | "state" => {
            let room_id = get_header(&request, "X-Room-Id");
            let lang = get_header(&request, "X-Language").unwrap_or("jp".to_string());

            if let Some(rid) = room_id {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let room = lock_recover(room_arc, "room");
                    let viewer_idx = resolve_viewer_idx(&request, query, &room);
                    let needs_deck = if viewer_idx < 2 && room.state.phase == Phase::Setup { room.pending_decks[viewer_idx].is_none() } else { false };

                    if needs_deck {
                        println!("[API] Room {}: Player {} needs deck selection (Phase: {:?})", rid, viewer_idx, room.state.phase);
                    }

                    let state_val = serialize_state_rich(
                        &room.state,
                        if room.is_vanilla { &state.vanilla_card_db } else { &state.card_db },
                        &room.mode,
                        viewer_idx,
                        0,
                        room.is_ai_thinking,
                        room.ai_status.clone(),
                        &lang,
                        needs_deck
                    );
                    response_json = json!({ "success": true, "state": state_val }).to_string();
                } else {
                    status = 404;
                    response_json = json!({"success": false, "error": "Room not found"}).to_string();
                    println!("[API] State request failed: Room {} not found in map (Existing: {:?})", rid, rooms.keys().collect::<Vec<_>>());
                }
            } else {
                status = 400;
                response_json = json!({"success": false, "error": "Missing X-Room-Id header"}).to_string();
            }
        },
        "api/action" => {
            let room_id = get_header(&request, "X-Room-Id");
            let session = get_header(&request, "X-Session-Token");

            if let (Some(rid), Some(s), Ok(body)) = (room_id, session, parse_body::<ActionReq>(&mut request)) {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc, "room");
                    if let Some(&p_idx) = room.players.get(&s) {
                        use engine_rust::core::logic::Phase;

                        let is_my_turn = match room.state.phase {
                            Phase::Response => room.state.interaction_stack.last().map_or(false, |p| p.ctx.player_id as usize == p_idx),
                            Phase::Rps => room.state.rps_choices[p_idx] == -1,
                            _ => room.state.current_player as usize == p_idx,
                        };

                        if is_my_turn {
                            let room_is_vanilla = room.is_vanilla;
                            let active_db = if room_is_vanilla { &state.vanilla_card_db } else { &state.card_db };
                            if let Err(e) = room.state.step(active_db, body.action_id) {
                                response_json = json!({"success": false, "error": e.to_string()}).to_string();
                            } else {
                                room.last_update = std::time::SystemTime::now();

                                // 1. Synchronous AI Reaction (snappy response)
                                if room.mode == "pve" && room.state.phase != Phase::Terminal {
                                    let mut steps = 0;

                                    loop {
                                        let ai_needed = match room.state.phase {
                                            Phase::Response => room.state.interaction_stack.last().map_or(false, |p| p.ctx.player_id == 1),
                                            Phase::Rps => room.state.rps_choices[1] == -1,
                                            _ => room.state.current_player == 1,
                                        };

                                        if ai_needed && room.state.phase != Phase::Terminal && steps < 5 {
                                            // Use TurnSequencer for vanilla mode AI (faster closeouts, no turn limit)
                                            if room.is_vanilla {
                                                room.state.step_opponent_turnseq(&state.vanilla_card_db);
                                            } else {
                                                // Use greedy heuristic for full game mode
                                                use engine_rust::core::heuristics::OriginalHeuristic;
                                                let heuristic = OriginalHeuristic::default();
                                                room.state.step_opponent_greedy(&state.card_db, &heuristic);
                                            }
                                            steps += 1;
                                        } else {
                                            break;
                                        }
                                    }
                                    room.last_update = std::time::SystemTime::now();
                                }

                                append_current_state_to_history(&mut room);

                                // 2. Determine if background thinking is needed
                                let ai_needed_after = match room.state.phase {
                                    Phase::Response => room.state.interaction_stack.last().map_or(false, |p| p.ctx.player_id == 1),
                                    Phase::Rps => room.state.rps_choices[1] == -1,
                                    _ => room.state.current_player == 1,
                                };

                                let will_think_in_background = room.mode == "pve" && room.state.phase != Phase::Terminal && !room.is_ai_thinking && ai_needed_after;
                                if will_think_in_background {
                                    room.is_ai_thinking = true;
                                    room.ai_status = "AI is thinking...".to_string();
                                }

                                let lang = get_header(&request, "X-Language").unwrap_or("jp".to_string());
                                let viewer_idx = p_idx;
                                let needs_deck = if viewer_idx < 2 && room.state.phase == Phase::Setup { room.pending_decks[viewer_idx].is_none() } else { false };

                                let state_val = serialize_state_rich(
                                    &room.state,
                                    if room.is_vanilla { &state.vanilla_card_db } else { &state.card_db },
                                    &room.mode,
                                    viewer_idx,
                                    0,
                                    room.is_ai_thinking,
                                    room.ai_status.clone(),
                                    &lang,
                                    needs_deck
                                );
                                response_json = json!({"success": true, "state": state_val}).to_string();

                                // 3. Start Background Processing if flagged
                                if will_think_in_background {
                                    let state_clone = state.clone();
                                    let room_arc_clone = room_arc.clone();
                                    let room_is_vanilla = room.is_vanilla;

                                    thread::spawn(move || {
                                        use engine_rust::core::logic::Phase;
                                        let mut steps = 0;
                                        loop {
                                            {
                                                let mut room = lock_recover(&room_arc_clone, "room");
                                                let ai_needed = match room.state.phase {
                                                    Phase::Response => room.state.interaction_stack.last().map_or(false, |p| p.ctx.player_id == 1),
                                                    Phase::Rps => room.state.rps_choices[1] == -1,
                                                    _ => room.state.current_player == 1,
                                                };

                                                if ai_needed && room.state.phase != Phase::Terminal && steps < 50 {
                                                    // Use TurnSequencer for vanilla mode AI
                                                    if room_is_vanilla {
                                                        room.state.step_opponent_turnseq(&state_clone.vanilla_card_db);
                                                    } else {
                                                        // Use greedy heuristic for full game mode
                                                        use engine_rust::core::heuristics::OriginalHeuristic;
                                                        let heuristic = OriginalHeuristic::default();
                                                        room.state.step_opponent_greedy(&state_clone.card_db, &heuristic);
                                                    }
                                                    steps += 1;
                                                    room.last_update = std::time::SystemTime::now();
                                                } else {
                                                    room.is_ai_thinking = false;
                                                    room.ai_status = String::new();
                                                    append_current_state_to_history(&mut room);
                                                    break;
                                                }
                                            }
                                        }
                                    });
                                }
                            }
                        } else { status = 403; response_json = json!({"error": "Not your turn"}).to_string(); }
                    } else {
                        status = 401;
                        response_json = json!({"success": false, "error": "Unauthorized"}).to_string();
                    }
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/set_deck" => {
            let room_id = get_header(&request, "X-Room-Id");
            let session = get_header(&request, "X-Session-Token");
            if let (Some(rid), Some(s), Ok(body)) = (room_id, session, parse_body::<SetDeckReq>(&mut request)) {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    if let Some(&p_idx) = room.players.get(&s) {
                        if p_idx == body.player {
                            let parsed = resolve_deck(&body.deck, &body.energy_deck.unwrap_or_default(), &state.card_db);
                            room.pending_decks[p_idx] = Some(parsed);
                            response_json = json!({"success": true}).to_string();

                            if room.pending_decks[0].is_some() && room.pending_decks[1].is_some() {
                                let p0 = room.pending_decks[0].clone().unwrap();
                                let p1 = room.pending_decks[1].clone().unwrap();

                                room.state.initialize_game(
                                    p0.members,
                                    p1.members,
                                    p0.energy,
                                    p1.energy,
                                    p0.lives,
                                    p1.lives,
                                );
                                room.pending_decks = [None, None];
                                replace_history_with_single_state(&mut room);
                            }
                        } else { status = 403; }
                    } else {
                        status = 401;
                        response_json = json!({"success": false, "error": "Unauthorized"}).to_string();
                    }
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/upload_deck" => {
            if let Ok(body) = parse_body::<UploadDeckReq>(&mut request) {
                let _ = parse_deck_content(&body.content, &state.card_db);
                // Implementation for global deck upload if needed, here we just return success
                response_json = json!({"success": true}).to_string();
            } else { status = 400; }
        },
        "api/get_decks" => {
            let available: Vec<String> = Decks::iter()
                .filter(|n| n.ends_with(".txt"))
                .map(|n| n.as_ref().trim_end_matches(".txt").to_string())
                .collect();

            let decks_enriched: Vec<Value> = available.into_iter().map(|n| {
                let (main, energy) = load_named_deck(&n).unwrap_or((vec![], vec![]));
                json!({
                    "id": n,
                    "name": n,
                    "card_count": main.len(),
                    "main": main,
                    "energy": energy
                })
            }).collect();

            response_json = json!({"success": true, "decks": decks_enriched}).to_string();
        },
        "api/get_random_deck" => {
            let deck = crate::utils::get_random_valid_deck(&state.card_db);
            let mut content = Vec::new();

            // Map Members
            for &mid in &deck.members {
                if let Some(m) = state.card_db.members.get(&mid) {
                    content.push(m.card_no.clone());
                }
            }
            // Map Lives
            for &lid in &deck.lives {
                if let Some(l) = state.card_db.lives.get(&lid) {
                    content.push(l.card_no.clone());
                }
            }
            // Map Energy
            let mut energy = Vec::new();
            for &eid in &deck.energy {
                if let Some(e) = state.card_db.energy_db.get(&eid) {
                    energy.push(e.card_no.clone());
                }
            }

            response_json = json!({
                "success": true,
                "content": content,
                "energy": energy
            }).to_string();
        },
        "api/rooms/assets" => {
            // Placeholder for asset preloader - returning empty list for now to satisfy frontend
            response_json = json!({ "success": true, "assets": [] }).to_string();
        },
        "api/get_test_deck" => {
            let name = query.and_then(|q| q.split('&').find(|p| p.starts_with("deck=")).map(|p| &p[5..])).unwrap_or("default");

            if let Some((main, energy)) = load_named_deck(name) {
                response_json = json!({"success": true, "main_deck": main, "energy_deck": energy}).to_string();
            } else {
                // Fallback to first available if named deck fails
                let fallback_name = Decks::iter()
                    .find(|n| n.ends_with(".txt"))
                    .map(|n| n.as_ref().trim_end_matches(".txt").to_string());

                if let Some(fb_name) = fallback_name {
                    if let Some((main, energy)) = load_named_deck(&fb_name) {
                        response_json = json!({"success": true, "main_deck": main, "energy_deck": energy, "fallback": true, "fallback_name": fb_name}).to_string();
                    } else {
                        status = 404;
                        response_json = json!({"success": false, "error": "Deck not found"}).to_string();
                    }
                } else {
                    status = 404;
                    response_json = json!({"success": false, "error": "No decks available"}).to_string();
                }
            }
        },
        "api/reset" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    room.state = GameState::default();
                    room.state.debug.debug_mode = state.debug_mode;
                    room.pending_decks = [None, None];
                    room.is_ai_thinking = false;
                    room.ai_status = String::new();
                    replace_history_with_single_state(&mut room);
                    println!("[API] Reset Room: {}", rid);
                    response_json = json!({"success": true}).to_string();
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/set_ai" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let (Some(rid), Ok(body)) = (room_id, parse_body::<Value>(&mut request)) {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    if let Some(mode) = body.get("mode").and_then(|v| v.as_str()) {
                        room.mode = mode.to_string();
                    }
                    response_json = json!({"success": true}).to_string();
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/force_turn_end" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    // Force skip current phase or advance turn
                    room.state.current_player = 1 - room.state.current_player;
                    room.last_update = std::time::SystemTime::now();
                    append_current_state_to_history(&mut room);
                    response_json = json!({"success": true}).to_string();
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/debug/apply_state" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    match parse_body::<Value>(&mut request) {
                        Ok(raw_payload) => match parse_debug_state_payload(&room.state, raw_payload) {
                            Ok(new_state) => {
                            room.state = new_state;
                            room.last_update = std::time::SystemTime::now();
                            append_current_state_to_history(&mut room);
                            response_json = json!({
                                "success": true,
                                "message": "State applied successfully.",
                                "history_index": room.history_cursor,
                                "history_length": room.history_timeline.len()
                            }).to_string();
                            println!("[DEBUG] Room {}: State applied via Warp.", rid);
                            }
                            Err(e) => {
                                status = 400;
                                response_json = json!({"success": false, "error": e}).to_string();
                                println!("[DEBUG] Room {}: Failed to apply state: {}", rid, e);
                            }
                        },
                        Err(e) => {
                            status = 400;
                            response_json = json!({"success": false, "error": e}).to_string();
                            println!("[DEBUG] Room {}: Failed to apply state: {}", rid, e);
                        }
                    }
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/debug/snapshot" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let room = lock_recover(room_arc.as_ref(), "room");
                    response_json = json!({
                        "success": true,
                        "raw_state": room.state.clone(),
                        "trace_log": room.state.debug.trace_log.clone(),
                        "semantic_log": room.state.ui.semantic_log.clone(),
                        "debug_mode": room.state.debug.debug_mode,
                        "history_index": room.history_cursor,
                        "history_length": room.history_timeline.len(),
                    }).to_string();
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/debug/board_override" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    match parse_body::<Value>(&mut request) {
                        Ok(raw_payload) => match parse_debug_state_payload(&room.state, raw_payload) {
                            Ok(new_state) => {
                            room.state = new_state;
                            room.last_update = std::time::SystemTime::now();
                            append_current_state_to_history(&mut room);
                            response_json = json!({
                                "success": true,
                                "message": "Board state updated successfully.",
                                "history_index": room.history_cursor,
                                "history_length": room.history_timeline.len()
                            }).to_string();
                            println!("[DEBUG] Room {}: Board state overridden via minimal JSON.", rid);
                            }
                            Err(e) => {
                                status = 400;
                                response_json = json!({"success": false, "error": e}).to_string();
                                println!("[DEBUG] Room {}: Failed to override board: {}", rid, e);
                            }
                        },
                        Err(e) => {
                            status = 400;
                            response_json = json!({"success": false, "error": e}).to_string();
                            println!("[DEBUG] Room {}: Failed to override board: {}", rid, e);
                        }
                    }
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/debug/toggle" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    room.state.debug.debug_mode = !room.state.debug.debug_mode;
                    response_json = json!({"success": true, "debug_mode": room.state.debug.debug_mode}).to_string();
                    println!("[DEBUG] Room {}: Debug Mode = {}", rid, room.state.debug.debug_mode);
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/debug/rewind" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    ensure_history_initialized(&mut room);
                    if room.history_cursor > 0 {
                        let new_cursor = room.history_cursor - 1;
                        if let Err(e) = move_history_cursor(&mut room, new_cursor) {
                            status = 400;
                            response_json = json!({"success": false, "error": e}).to_string();
                        } else {
                        room.last_update = std::time::SystemTime::now();
                        response_json = json!({
                            "success": true,
                            "history_index": room.history_cursor,
                            "history_length": room.history_timeline.len()
                        }).to_string();
                        println!("[DEBUG] Room {}: Rewound to history index {}/{}", rid, room.history_cursor, room.history_timeline.len());
                        }
                    } else {
                        status = 400;
                        response_json = json!({"success": false, "error": "No history available"}).to_string();
                    }
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/debug/redo" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    ensure_history_initialized(&mut room);
                    if room.history_cursor + 1 < room.history_timeline.len() {
                        let new_cursor = room.history_cursor + 1;
                        if let Err(e) = move_history_cursor(&mut room, new_cursor) {
                            status = 400;
                            response_json = json!({"success": false, "error": e}).to_string();
                        } else {
                        room.last_update = std::time::SystemTime::now();
                        response_json = json!({
                            "success": true,
                            "history_index": room.history_cursor,
                            "history_length": room.history_timeline.len()
                        }).to_string();
                        println!("[DEBUG] Room {}: Redone to history index {}/{}", rid, room.history_cursor, room.history_timeline.len());
                        }
                    } else {
                        status = 400;
                        response_json = json!({"success": false, "error": "No redo available"}).to_string();
                    }
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/debug/dump_state" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let room = lock_recover(room_arc.as_ref(), "room");
                    let mut room_info = HashMap::new();
                    room_info.insert("id".to_string(), rid.clone());
                    room_info.insert("mode".to_string(), room.mode.clone());

                    let history_vec: Vec<GameState> = room.history_timeline.iter().cloned().collect();

                    let std_state =
                        StandardizedState::new(room.state.clone(), room_info, Some(history_vec));

                    match serde_json::to_string(&std_state) {
                        Ok(json) => {
                            response_json = json;
                        },
                        Err(e) => {
                            status = 500;
                            response_json = json!({"error": format!("Serialization failed: {}", e)}).to_string();
                        }
                    }
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/export_game" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    ensure_history_initialized(&mut room);
                    response_json = json!({
                        "success": true,
                        "export_timestamp": std::time::SystemTime::now()
                            .duration_since(std::time::UNIX_EPOCH)
                            .map(|d| d.as_secs())
                            .unwrap_or_default(),
                        "game_mode": room.mode,
                        "current_state": room.state.clone(),
                        "history": room.history_timeline.iter().cloned().collect::<Vec<GameState>>(),
                        "history_index": room.history_cursor,
                    }).to_string();
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/import_game" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let (Some(rid), Ok(payload)) = (room_id, parse_body::<GameImportPayload>(&mut request)) {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = lock_recover(room_arc.as_ref(), "room");
                    match import_history_payload(&mut room, payload.clone()) {
                        Ok(()) => {
                            if let Some(mode) = payload.mode {
                                room.mode = mode;
                            }
                            room.last_update = std::time::SystemTime::now();
                            response_json = json!({
                                "success": true,
                                "history_index": room.history_cursor,
                                "history_length": room.history_timeline.len()
                            }).to_string();
                        }
                        Err(e) => {
                            status = 400;
                            response_json = json!({"success": false, "error": e}).to_string();
                        }
                    }
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/exec" => {
             // Stub for debug commands
             response_json = json!({"success": true, "message": "Command received"}).to_string();
        },
        "api/report" | "api/report_bug" => {
            if let Ok(body) = parse_body::<Value>(&mut request) {
                let explanation = body.get("explanation").and_then(|v| v.as_str()).unwrap_or("(none)");
                println!("[BUG REPORT] received: {}", explanation);
                let ts = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs();
                // Human-readable timestamp: YYYYMMDD_HHMMSS (UTC approximation from unix)
                let secs_in_day = 86400u64;
                let days = ts / secs_in_day;
                let time_of_day = ts % secs_in_day;
                let hours = time_of_day / 3600;
                let minutes = (time_of_day % 3600) / 60;
                let seconds = time_of_day % 60;
                // Simple date calc (accurate enough for filenames)
                let (year, month, day) = {
                    let mut y = 1970i64;
                    let mut remaining = days as i64;
                    loop {
                        let days_in_year = if y % 4 == 0 && (y % 100 != 0 || y % 400 == 0) { 366 } else { 365 };
                        if remaining < days_in_year { break; }
                        remaining -= days_in_year;
                        y += 1;
                    }
                    let leap = y % 4 == 0 && (y % 100 != 0 || y % 400 == 0);
                    let month_days = [31, if leap {29} else {28}, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
                    let mut m = 0u64;
                    for &md in &month_days {
                        if remaining < md { break; }
                        remaining -= md;
                        m += 1;
                    }
                    (y, m + 1, remaining + 1)
                };
                let filename = format!("reports/report_{:04}{:02}{:02}_{:02}{:02}{:02}.json", year, month, day, hours, minutes, seconds);
                let _ = std::fs::create_dir_all("reports");
                if let Ok(content) = serde_json::to_string_pretty(&body) {
                    // Check if this is already a standardized state (has "current_state" and "tensor")
                    // If not, we could wrap it, but for now we just save as is.
                    if let Err(e) = std::fs::write(&filename, content) {
                        println!("[API] Failed to save report: {}", e);
                    } else {
                        println!("[API] Saved report to {}", filename);
                    }
                }
                response_json = json!({"success": true}).to_string();
            } else { status = 400; }
        },
        "api/ai_suggest" => {
            let room_id = get_header(&request, "X-Room-Id");
            let lang = get_header(&request, "X-Language").unwrap_or("jp".to_string());
            if let (Some(rid), Ok(body)) = (room_id, parse_body::<Value>(&mut request)) {
                let rooms = lock_recover(&state.rooms, "app_state.rooms");
                if let Some(room_arc) = rooms.get(&rid) {
                    let room = lock_recover(room_arc.as_ref(), "room");
                    let sims = body.get("sims").and_then(|v| v.as_u64()).unwrap_or(10) as usize;

                    let mut mcts = MCTS::new();
                    use engine_rust::core::heuristics::OriginalHeuristic;
                    let heuristic = OriginalHeuristic::default();

                    let (results, _) = mcts.search(
                        &room.state,
                        &state.card_db,
                        sims,
                        1.0,
                        SearchHorizon::Limited(5),
                        &heuristic
                    );

                    let suggestions: Vec<Value> = results.into_iter().map(|(id, value, visits)| {
                        let (desc, _, _, _, _) = get_action_desc_rich(
                            id,
                            &room.state,
                            &state.card_db,
                            room.state.current_player as usize,
                            &lang
                        );
                        json!({
                            "id": id,
                            "desc": desc,
                            "value": value,
                            "visits": visits
                        })
                    }).collect();

                    response_json = json!({"success": true, "suggestions": suggestions}).to_string();
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/get_card_registry" => {
            let mut registry = HashMap::new();

            for m in state.card_db.members.values() {
                registry.insert(normalize_card_code(&m.card_no), json!({
                    "name": m.name,
                    "type": "member",
                    "img": m.img_path
                }));
            }
            for l in state.card_db.lives.values() {
                registry.insert(normalize_card_code(&l.card_no), json!({
                    "name": l.name,
                    "type": "live",
                    "img": l.img_path
                }));
            }
            for e in state.card_db.energy_db.values() {
                registry.insert(normalize_card_code(&e.card_no), json!({
                    "name": e.name,
                    "type": "energy",
                    "img": e.img_path
                }));
            }

            response_json = json!({
                "success": true,
                "registry": registry
            }).to_string();
        },
        _ => { status = 404; response_json = json!({"error": "Unknown API"}).to_string(); }
    }

    let response = Response::from_string(response_json)
        .with_status_code(status)
        .with_header(Header::from_bytes(&b"Content-Type"[..], &b"application/json"[..]).unwrap())
        .with_header(Header::from_bytes(&b"Access-Control-Allow-Origin"[..], &b"*"[..]).unwrap());
    let _ = request.respond(response);
}
