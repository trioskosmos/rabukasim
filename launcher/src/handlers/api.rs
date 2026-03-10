use tiny_http::{Request, Response, Header};
use serde_json::{json, Value};
use std::sync::{Arc, Mutex};
use std::thread;
use std::collections::{HashMap, VecDeque};
use uuid::Uuid;
use engine_rust::core::logic::{GameState, StandardizedState};
#[cfg(feature = "nn")]
use engine_rust::core::alphazero_encoding::AlphaZeroEncoding;
use engine_rust::core::logic::Phase;
use engine_rust::core::mcts::{MCTS, SearchHorizon};

// Removed SearchHorizon, EvalMode imports as they were unused
// Removed unused Request types from import
use crate::models::{AppState, Room, CreateRoomReq, JoinRoomReq, ActionReq, UploadDeckReq, SetDeckReq, BoardOverrideReq};
use crate::serialization::{serialize_state_rich, get_action_desc_rich};
use crate::utils::{parse_body, generate_room_code, get_header, resolve_deck, get_random_valid_deck, parse_deck_content, load_named_deck, normalize_code};
use crate::Decks;

pub fn handle_api_request(mut request: Request, path: &str, query: Option<&str>, state: Arc<AppState>) {
    let mut response_json = String::new();
    let mut status = 200;

    println!("[API] Request: {}", path);
    match path {
        "api/status" => {
            let rooms = state.rooms.lock().unwrap();
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
                let mut rooms = state.rooms.lock().unwrap();
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
                let new_room = Room {
                    _id: room_id.clone(),
                    state: game_state,
                    players,
                    username_to_token,
                    mode: mode_str.clone(),
                    last_update: std::time::SystemTime::now(),
                    created_at: std::time::SystemTime::now(),
                    is_public: body.public.unwrap_or(false),
                    pending_decks,
                    is_ai_thinking: false,
                    ai_status: String::new(),
                    history: VecDeque::new(),
                    redo_history: VecDeque::new(),
                };

                let room_arc = Arc::new(Mutex::new(new_room));
                rooms.insert(room_id.clone(), room_arc);
                println!("[API] SUCCESS: Created room {} (mode: {}). Decks: P0={}, P1={}",
                    room_id, mode_str,
                    body.p0_deck.as_ref().map(|d| d.len()).unwrap_or(0),
                    body.p1_deck.as_ref().map(|d| d.len()).unwrap_or(0)
                );
                response_json = json!({ "success": true, "room_id": room_id, "session": token, "player_idx": 0 }).to_string();
            } else {
                status = 400;
                let err_msg = body_res.err().unwrap_or_else(|| "Unknown error".to_string());
                response_json = json!({"error": "Invalid body"}).to_string();
                println!("[API] FAILED to create room: {}", err_msg);
            }
        },
        "api/rooms/list" => {
            let rooms = state.rooms.lock().unwrap();
            let public_rooms: Vec<Value> = rooms.values()
                .filter_map(|r_arc| {
                    let r = r_arc.lock().unwrap();
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
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&body.room_id) {
                    let mut room = room_arc.lock().unwrap();
                    if room.players.len() >= 2 {
                         status = 400; response_json = json!({"error": "Full"}).to_string();
                    } else {
                         let token = Uuid::new_v4().to_string();
                         room.players.insert(token.clone(), 1); // Joiner is P1
                         if let Some(user) = &body.username {
                             room.username_to_token.insert(user.clone(), token.clone());
                         }
                         response_json = json!({ "success": true, "session": token, "player_idx": 1 }).to_string();
                    }
                } else { status = 404; response_json = json!({"error": "Not found"}).to_string(); }
            } else { status = 400; }
        },
        "api/state" | "state" => {
            let room_id = get_header(&request, "X-Room-Id");
            let session = get_header(&request, "X-Session-Token");
            let lang = get_header(&request, "X-Language").unwrap_or("jp".to_string());

            if let Some(rid) = room_id {
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let room = room_arc.lock().unwrap();
                    let viewer_idx = session.as_ref().and_then(|s| room.players.get(s)).cloned().unwrap_or(2);
                    let needs_deck = if viewer_idx < 2 && room.state.phase == Phase::Setup { room.pending_decks[viewer_idx].is_none() } else { false };

                    if needs_deck {
                        println!("[API] Room {}: Player {} needs deck selection (Phase: {:?})", rid, viewer_idx, room.state.phase);
                    }

                    let state_val = serialize_state_rich(
                        &room.state,
                        &state.card_db,
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
                    println!("[API] State request failed: Room {} not found in map (Existing: {:?})", rid, rooms.keys().collect::<Vec<_>>());
                }
            } else { status = 400; }
        },
        "api/action" => {
            let room_id = get_header(&request, "X-Room-Id");
            let session = get_header(&request, "X-Session-Token");

            if let (Some(rid), Some(s), Ok(body)) = (room_id, session, parse_body::<ActionReq>(&mut request)) {
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = room_arc.lock().unwrap();
                    if let Some(&p_idx) = room.players.get(&s) {
                        use engine_rust::core::logic::Phase;

                        let is_my_turn = match room.state.phase {
                            Phase::Response => room.state.interaction_stack.last().map_or(false, |p| p.ctx.player_id as usize == p_idx),
                            Phase::Rps => room.state.rps_choices[p_idx] == -1,
                            _ => room.state.current_player as usize == p_idx,
                        };

                        if is_my_turn {
                            // Save state to history before action
                            let snapshot = room.state.clone();
                            room.history.push_back(snapshot);
                            if room.history.len() > 50 { room.history.pop_front(); }
                            room.redo_history.clear(); // Clear redo on action

                            if let Err(e) = room.state.step(&state.card_db, body.action_id) {
                                response_json = json!({"success": false, "error": e.to_string()}).to_string();
                            } else {
                                room.last_update = std::time::SystemTime::now();

                                // 1. Synchronous AI Reaction (snappy response)
                                if room.mode == "pve" && room.state.phase != Phase::Terminal {
                                    use engine_rust::core::heuristics::OriginalHeuristic;
                                    let heuristic = OriginalHeuristic::default();
                                    let mut steps = 0;

                                    loop {
                                        let ai_needed = match room.state.phase {
                                            Phase::Response => room.state.interaction_stack.last().map_or(false, |p| p.ctx.player_id == 1),
                                            Phase::Rps => room.state.rps_choices[1] == -1,
                                            _ => room.state.current_player == 1,
                                        };

                                        if ai_needed && room.state.phase != Phase::Terminal && steps < 5 {
                                            room.state.step_opponent_greedy(&state.card_db, &heuristic);
                                            steps += 1;
                                        } else {
                                            break;
                                        }
                                    }
                                    room.last_update = std::time::SystemTime::now();
                                }

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
                                    &state.card_db,
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

                                    thread::spawn(move || {
                                        use engine_rust::core::logic::Phase;
                                        use engine_rust::core::heuristics::OriginalHeuristic;
                                        let heuristic = OriginalHeuristic::default();
                                        let mut steps = 0;
                                        loop {
                                            {
                                                let mut room = room_arc_clone.lock().unwrap();
                                                let ai_needed = match room.state.phase {
                                                    Phase::Response => room.state.interaction_stack.last().map_or(false, |p| p.ctx.player_id == 1),
                                                    Phase::Rps => room.state.rps_choices[1] == -1,
                                                    _ => room.state.current_player == 1,
                                                };

                                                if ai_needed && room.state.phase != Phase::Terminal && steps < 50 {
                                                    room.state.step_opponent_greedy(&state_clone.card_db, &heuristic);
                                                    steps += 1;
                                                    room.last_update = std::time::SystemTime::now();
                                                } else {
                                                    room.is_ai_thinking = false;
                                                    room.ai_status = String::new();
                                                    break;
                                                }
                                            }
                                        }
                                    });
                                }
                            }
                        } else { status = 403; response_json = json!({"error": "Not your turn"}).to_string(); }
                    } else { status = 401; }
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/set_deck" => {
            let room_id = get_header(&request, "X-Room-Id");
            let session = get_header(&request, "X-Session-Token");
            if let (Some(rid), Some(s), Ok(body)) = (room_id, session, parse_body::<SetDeckReq>(&mut request)) {
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = room_arc.lock().unwrap();
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
                            }
                        } else { status = 403; }
                    } else { status = 401; }
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
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = room_arc.lock().unwrap();
                    room.state = GameState::default();
                    room.state.debug.debug_mode = state.debug_mode;
                    room.pending_decks = [None, None];
                    room.is_ai_thinking = false;
                    room.ai_status = String::new();
                    println!("[API] Reset Room: {}", rid);
                    response_json = json!({"success": true}).to_string();
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/set_ai" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let (Some(rid), Ok(body)) = (room_id, parse_body::<Value>(&mut request)) {
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = room_arc.lock().unwrap();
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
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = room_arc.lock().unwrap();
                    // Force skip current phase or advance turn
                    room.state.current_player = 1 - room.state.current_player;
                    room.last_update = std::time::SystemTime::now();
                    response_json = json!({"success": true}).to_string();
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/debug/apply_state" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = room_arc.lock().unwrap();
                    match parse_body::<GameState>(&mut request) {
                        Ok(new_state) => {
                            // Save state to history before warp
                            let snapshot = room.state.clone();
                            room.history.push_back(snapshot);
                            if room.history.len() > 50 { room.history.pop_front(); }
                            room.redo_history.clear(); // Clear redo on warp

                            room.state = new_state;
                            room.last_update = std::time::SystemTime::now();
                            response_json = json!({"success": true}).to_string();
                            println!("[DEBUG] Room {}: State applied via Warp.", rid);
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
        "api/debug/board_override" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = room_arc.lock().unwrap();
                    match parse_body::<BoardOverrideReq>(&mut request) {
                        Ok(req) => {
                            // Save state to history before warp
                            let snapshot = room.state.clone();
                            room.history.push_back(snapshot);
                            if room.history.len() > 50 { room.history.pop_front(); }
                            room.redo_history.clear();

                            if let Some(ph) = req.phase {
                                room.state.phase = unsafe { std::mem::transmute(ph) };
                            }
                            if let Some(t) = req.turn { room.state.turn = t; }

                            for (i, p_ov) in req.players.iter().enumerate() {
                                if i >= 2 { break; }
                                let p = &mut room.state.players[i];
                                if let Some(ref st) = p_ov.stage {
                                    for (si, cid_ref) in st.iter().enumerate() {
                                        let cid = *cid_ref;
                                        if si < 3 { p.stage[si] = cid; }
                                    }
                                }
                                if let Some(ref lz) = p_ov.live_zone {
                                    for (li, cid_ref) in lz.iter().enumerate() {
                                        let cid = *cid_ref;
                                        if li < 3 { p.live_zone[li] = cid; }
                                    }
                                }
                                if let Some(ref h) = p_ov.hand {
                                    p.hand.clear();
                                    for &cid in h { p.hand.push(cid); }
                                }
                                if let Some(ref e) = p_ov.energy {
                                    p.energy_zone.clear();
                                    for &cid in e { p.energy_zone.push(cid); }
                                }
                                if let Some(ref s) = p_ov.success_lives {
                                    p.success_lives.clear();
                                    for &cid in s { p.success_lives.push(cid); }
                                }
                                if let Some(ref d) = p_ov.discard {
                                    p.discard.clear();
                                    for &cid in d { p.discard.push(cid); }
                                }
                            }
                            room.last_update = std::time::SystemTime::now();
                            response_json = json!({"success": true}).to_string();
                            println!("[DEBUG] Room {}: Board state overridden via minimal JSON.", rid);
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
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = room_arc.lock().unwrap();
                    room.state.debug.debug_mode = !room.state.debug.debug_mode;
                    response_json = json!({"success": true, "debug_mode": room.state.debug.debug_mode}).to_string();
                    println!("[DEBUG] Room {}: Debug Mode = {}", rid, room.state.debug.debug_mode);
                } else { status = 404; }
            } else { status = 400; }
        },
        "api/debug/rewind" => {
            let room_id = get_header(&request, "X-Room-Id");
            if let Some(rid) = room_id {
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = room_arc.lock().unwrap();
                    if let Some(old_state) = room.history.pop_back() {
                        // Push current state to REDO before restoring
                        let current_snapshot = room.state.clone();
                        room.redo_history.push_back(current_snapshot);
                        if room.redo_history.len() > 50 { room.redo_history.pop_front(); }

                        room.state = old_state;
                        room.last_update = std::time::SystemTime::now();
                        response_json = json!({"success": true}).to_string();
                        println!("[DEBUG] Room {}: Rewound to previous state. Remaining history: {}, Redo: {}", rid, room.history.len(), room.redo_history.len());
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
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let mut room = room_arc.lock().unwrap();
                    if let Some(newer_state) = room.redo_history.pop_back() {
                        // Push current state to HISTORY before restoring
                        let snapshot = room.state.clone();
                        room.history.push_back(snapshot);
                        if room.history.len() > 50 { room.history.pop_front(); }

                        room.state = newer_state;
                        room.last_update = std::time::SystemTime::now();
                        response_json = json!({"success": true}).to_string();
                        println!("[DEBUG] Room {}: Redone state. History: {}, Redo left: {}", rid, room.history.len(), room.redo_history.len());
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
                    let room = room_arc.lock().unwrap();
                    let mut room_info = HashMap::new();
                    room_info.insert("id".to_string(), rid.clone());
                    room_info.insert("mode".to_string(), room.mode.clone());

                    let history_vec: Vec<GameState> = room.history.iter().cloned().collect();

                    let std_state = StandardizedState::new(
                        room.state.clone(),
                        &state.card_db,
                        room_info,
                        true,
                        Some(history_vec),
                    );

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
        "api/v1/analyze_model" => {
            #[cfg(feature = "nn")]
            {
                if let Some(session_arc) = &state.model_session {
                    match parse_body::<GameState>(&mut request) {
                        Ok(new_state) => {
                            let input_vec = new_state.to_alphazero_tensor(&state.card_db);
                            let legal_mask = new_state.get_legal_actions(&state.card_db);
                            let mut action_ids = Vec::new();
                            let mut nn_mask = vec![0.0f32; 22000];

                            for (id, &is_legal) in legal_mask.iter().enumerate() {
                                if is_legal {
                                    action_ids.push(id as i32);
                                    if id < 22000 {
                                        nn_mask[id] = 1.0;
                                    }
                                }
                            }

                            let input_shape = [1, 20500];
                            let mask_shape = [1, 22000];

                            let mut session = session_arc.lock().unwrap();
                            let input_tensor = ort::value::Value::from_array((input_shape, input_vec)).unwrap();
                            let mask_tensor = ort::value::Value::from_array((mask_shape, nn_mask)).unwrap();

                            let run_result = session.run(ort::inputs![input_tensor, mask_tensor]);
                            if let Ok(outputs) = run_result {
                                let policy_val = outputs.get("policy").expect("Missing policy output");
                                let value_val = outputs.get("value").expect("Missing value output");

                                if let (Ok((_, p_slice)), Ok((_, v_slice))) = (
                                    policy_val.try_extract_tensor::<f32>(),
                                    value_val.try_extract_tensor::<f32>()
                                ) {
                                    let win_prob = v_slice[0];
                                    let momentum = v_slice[1];
                                    let efficiency = v_slice[2];

                                    let mut action_results = Vec::new();
                                    for &id in &action_ids {
                                        if (id as usize) < 22000 {
                                            let logit = p_slice[id as usize];
                                            let (desc, _, _, _, _) = get_action_desc_rich(
                                                id,
                                                &new_state,
                                                &state.card_db,
                                                new_state.current_player as usize,
                                                "en"
                                            );
                                            action_results.push(json!({
                                                "id": id,
                                                "desc": desc,
                                                "logit": logit
                                            }));
                                        }
                                    }

                                    action_results.sort_by(|a, b| b["logit"].as_f64().unwrap().partial_cmp(&a["logit"].as_f64().unwrap()).unwrap());

                                    response_json = json!({
                                        "success": true,
                                        "value": {
                                            "win_prob": win_prob,
                                            "momentum": momentum,
                                            "efficiency": efficiency
                                        },
                                        "actions": action_results
                                    }).to_string();
                                }
                            }
                        },
                        Err(e) => {
                            status = 400;
                            response_json = json!({"success": false, "error": e}).to_string();
                        }
                    }
                } else {
                    status = 501;
                    response_json = json!({"error": "Model not loaded"}).to_string();
                }
            }
            #[cfg(not(feature = "nn"))]
            {
                status = 501;
                response_json = json!({"error": "NN feature not enabled"}).to_string();
            }
        },
        "api/ai_suggest" => {
            let room_id = get_header(&request, "X-Room-Id");
            let lang = get_header(&request, "X-Language").unwrap_or("jp".to_string());
            if let (Some(rid), Ok(body)) = (room_id, parse_body::<Value>(&mut request)) {
                let rooms = state.rooms.lock().unwrap();
                if let Some(room_arc) = rooms.get(&rid) {
                    let room = room_arc.lock().unwrap();
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
                registry.insert(normalize_code(&m.card_no), json!({
                    "name": m.name,
                    "type": "member",
                    "img": m.img_path
                }));
            }
            for l in state.card_db.lives.values() {
                registry.insert(normalize_code(&l.card_no), json!({
                    "name": l.name,
                    "type": "live",
                    "img": l.img_path
                }));
            }
            for e in state.card_db.energy_db.values() {
                registry.insert(normalize_code(&e.card_no), json!({
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
