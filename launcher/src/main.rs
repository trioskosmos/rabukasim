use tiny_http::Server;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

// Import engine components
use engine_rust::core::models::{CardDatabase};

// Internal modules are now in lib.rs
use rabuka_launcher::models::{AppState};
use rabuka_launcher::handlers::route_request;
use rabuka_launcher::utils::{get_local_ip, launcher_url, preferred_server_ports};
use rabuka_launcher::{Assets};

fn snapshot_is_valid(db: &CardDatabase) -> bool {
    !db.members.is_empty() && !db.lives.is_empty()
}

fn binary_snapshot_is_stale(bin_path: &Path, json_path: &Path) -> bool {
    let bin_meta = match std::fs::metadata(bin_path) {
        Ok(meta) => meta,
        Err(_) => return true,
    };
    let json_meta = match std::fs::metadata(json_path) {
        Ok(meta) => meta,
        Err(_) => return false,
    };

    match (bin_meta.modified(), json_meta.modified()) {
        (Ok(bin_time), Ok(json_time)) => bin_time < json_time,
        _ => false,
    }
}

fn candidate_runtime_db_paths() -> &'static [&'static str] {
    &[
        "data/cards_compiled.json",
        "../data/cards_compiled.json",
        "../../data/cards_compiled.json",
        "../../../data/cards_compiled.json",
        "static_content/data/cards_compiled.json",
        "../static_content/data/cards_compiled.json",
    ]
}

fn find_runtime_db_json_path() -> Option<PathBuf> {
    candidate_runtime_db_paths()
        .iter()
        .map(PathBuf::from)
        .find(|path| path.exists())
}

fn snapshot_cache_path(json_path: Option<&Path>) -> PathBuf {
    json_path
        .and_then(Path::parent)
        .map(|parent| parent.join("cards_compiled.bin"))
        .unwrap_or_else(|| PathBuf::from("data/cards_compiled.bin"))
}


fn main() {
    let start_time = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();

    let args: Vec<String> = std::env::args().collect();
    let debug_mode = args.contains(&"--debug".to_string()) || args.contains(&"-d".to_string());

    if debug_mode {
        println!("[DEBUG] RabukaSim Debug Mode: ENABLED");

        println!("[DEBUG] Card ability logic will be logged to terminal.");
    }

    println!("Loading card database...");
    let runtime_json_path = find_runtime_db_json_path();
    let bin_path = snapshot_cache_path(runtime_json_path.as_deref());
    let json_label = runtime_json_path
        .as_ref()
        .map(|path| path.display().to_string())
        .unwrap_or_else(|| "<embedded launcher asset>".to_string());
    println!("[DB] Canonical runtime JSON mirror: {}", json_label);
    println!("[DB] Canonical binary snapshot cache: {}", bin_path.display());
    let stale_binary = runtime_json_path
        .as_deref()
        .map(|json_path| binary_snapshot_is_stale(&bin_path, json_path))
        .unwrap_or(true);

    let mut need_new_snapshot = false;
    let card_db = match std::fs::read(&bin_path) {
        Ok(bin_data) => {
            match CardDatabase::from_binary(&bin_data) {
                Ok(db) => {
                    if !stale_binary && snapshot_is_valid(&db) {
                        println!("[DB] Loaded from binary snapshot (FAST)");
                        db
                    } else {
                        if stale_binary {
                            println!("[DB] Binary snapshot is older than JSON, reloading from JSON...");
                        } else {
                            println!("[DB] Binary snapshot is missing member/live cards, reloading from JSON...");
                        }
                        need_new_snapshot = true;
                        load_db_from_json()
                    }
                },
                Err(e) => {
                    println!("[DB] Binary load failed, falling back to JSON: {}", e);
                    need_new_snapshot = true;
                    load_db_from_json()
                }
            }
        },
        Err(_) => {
            println!("[DB] No binary snapshot found, loading from JSON...");
            need_new_snapshot = true;
            load_db_from_json()
        }
    };

    // Regenerate binary snapshot when missing or stale
    if need_new_snapshot {
        if let Ok(bin_data) = card_db.to_binary() {
            let _ = std::fs::write(&bin_path, bin_data);
            println!("[DB] Produced binary snapshot for next run.");
        }
    }

    // Vanilla DB: same card data but with ability suppression enabled
    let mut vanilla_card_db = card_db.clone();
    vanilla_card_db.is_vanilla = true;

    println!("==========================================");
    println!("Database Initialization (v2):");
    println!("  - Instance ID:           {}", start_time);
    println!("  - Member Cards (16-bit): {}", card_db.members.len());
    println!("  - Live Cards (16-bit):   {}", card_db.lives.len());
    println!("  - Energy Cards:          {}", card_db.energy_db.len());
    println!("  - Logic Slots (12-bit):  4096");
    println!("==========================================");

    let app_state = Arc::new(AppState {
        rooms: Mutex::new(HashMap::new()),
        card_db,
        vanilla_card_db,
        server_instance_id: start_time,
        debug_mode,
    });

    // 3. Start Background Cleanup Thread
    let cleanup_state = app_state.clone();
    thread::spawn(move || {
        loop {
            thread::sleep(Duration::from_secs(60));
            if let Ok(mut rooms) = cleanup_state.rooms.lock() {
                let initial_count = rooms.len();
                rooms.retain(|_, r| {
                     if let Ok(room) = r.lock() {
                         room.last_update.elapsed().unwrap_or(Duration::from_secs(0)).as_secs() < 3600
                     } else {
                         false
                     }
                });
                let dropped = initial_count - rooms.len();
                if dropped > 0 {
                    println!("[Cleanup] Removed {} inactive rooms. Active: {}", dropped, rooms.len());
                }
            }
        }
    });

    // 4. Start Server
    let env_port = std::env::var("PORT").ok().and_then(|p| p.parse().ok());
    let ports = preferred_server_ports(env_port);

    let mut server = None;
    let mut port = 0;

    for p in ports {
        match Server::http(format!("0.0.0.0:{}", p)) {
            Ok(s) => {
                server = Some(s);
                port = p;
                break;
            }
            Err(e) if env_port.is_some() => panic!("Failed to bind to requested PORT {}: {}", p, e),
            Err(_) => continue,
        }
    }

    let server = server.expect("Failed to start server. Is the port blocked?");

    println!("--------------------------------------------------");
    println!("Rabuka Launcher (Multiplayer Host) is Running!");

    println!("Local:   http://127.0.0.1:{}", port);

    if let Ok(my_ip) = get_local_ip() {
        println!("Network: http://{}:{}", my_ip, port);
    }
    println!("--------------------------------------------------");

    // Auto-open browser
    let url = launcher_url(port);
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(1000));
        if webbrowser::open(&url).is_err() {
            println!("[WARN] Failed to open browser automatically. Open {} manually.", url);
        }
    });

    let shared_state = app_state.clone();
    for request in server.incoming_requests() {
        let state_ref = shared_state.clone();
        thread::spawn(move || {
            route_request(request, state_ref);
        });
    }
}

fn load_db_from_json() -> CardDatabase {
    if let Some(path) = find_runtime_db_json_path() {
        let path_label = path.display().to_string();
        if let Ok(db_json) = std::fs::read_to_string(&path) {
            println!("[DB] Loading live JSON file: {}", path_label);
            return CardDatabase::from_json(&db_json)
                .unwrap_or_else(|err| panic!("Failed to parse CardDatabase from {}: {}", path_label, err));
        }
    }

    let db_file = Assets::get("data/cards_compiled.json").expect("Missing cards_compiled.json!");
    println!("[DB] Loading embedded launcher asset: data/cards_compiled.json");
    let db_json = std::str::from_utf8(db_file.data.as_ref()).expect("Failed to read DB json");
    CardDatabase::from_json(db_json).expect("Failed to parse CardDatabase from JSON")
}
