pub mod api;
pub mod static_files;

use tiny_http::{Request, Response, Header, Method};
use std::sync::Arc;
use crate::models::AppState;

pub fn route_request(request: Request, state: Arc<AppState>) {
    let url = request.url().to_string();
    let method = request.method().to_string();
    let (path_raw, query) = match url.split_once('?') {
        Some((p, q)) => (p, Some(q)),
        None => (url.as_str(), None),
    };

    let path = if path_raw.len() > 1 && path_raw.ends_with('/') {
        &path_raw[..path_raw.len() - 1]
    } else {
        path_raw
    };

    // CORS Handling
    if request.method() == &Method::Options {
        let response = Response::empty(200)
            .with_header(Header::from_bytes(&b"Access-Control-Allow-Origin"[..], &b"*"[..]).unwrap())
            .with_header(Header::from_bytes(&b"Access-Control-Allow-Methods"[..], &b"GET, POST, OPTIONS"[..]).unwrap())
            .with_header(Header::from_bytes(&b"Access-Control-Allow-Headers"[..], &b"Content-Type, X-Room-Id, X-Session-Token, X-Player-Idx"[..]).unwrap());
        let _ = request.respond(response);
        return;
    }

    let path = path.trim_start_matches('/');
    if path.starts_with("api/") || path == "state" {
        println!("[API] {} {}", method, url);
        api::handle_api_request(request, path, query, state);
    } else {
        if !url.contains(".png") && !url.contains(".webp") && !url.contains(".js") && !url.contains(".css") {
            println!("[Static] {} {}", method, url);
        }
        static_files::handle_static_file(request);
    }
}
