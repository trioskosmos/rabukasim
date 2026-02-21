use tiny_http::{Request, Response, Header};
use crate::Assets;

pub fn handle_static_file(request: Request) {
    let url_raw = request.url();
    let (path_stripped, _query) = match url_raw.split_once('?') {
        Some((p, q)) => (p, Some(q)),
        None => (url_raw, None),
    };

    let rel_path = if path_stripped == "/" || path_stripped == "/index.html" {
        "index.html"
    } else {
        path_stripped.trim_start_matches('/')
    };

    // 1. Try local disk first (for live development/sync)
    let disk_path = std::path::Path::new("static_content").join(rel_path);
    if disk_path.exists() && disk_path.is_file() {
        if let Ok(data) = std::fs::read(&disk_path) {
            let mime = mime_guess::from_path(&disk_path).first_or_octet_stream();
            let response = Response::from_data(data)
                .with_header(Header::from_bytes(&b"Content-Type"[..], mime.as_ref().as_bytes()).unwrap())
                .with_header(Header::from_bytes(&b"Access-Control-Allow-Origin"[..], &b"*"[..]).unwrap());
            let _ = request.respond(response);
            return;
        }
    }

    // 2. Fallback to embedded assets
    if let Some(file) = Assets::get(rel_path) {
        let mime = mime_guess::from_path(rel_path).first_or_octet_stream();
        let response = Response::from_data(file.data.as_ref())
            .with_header(Header::from_bytes(&b"Content-Type"[..], mime.as_ref().as_bytes()).unwrap())
            .with_header(Header::from_bytes(&b"Access-Control-Allow-Origin"[..], &b"*"[..]).unwrap());
        let _ = request.respond(response);
    } else {
        println!("[Static] 404: {}", rel_path);
        let response = Response::from_string("Not Found")
            .with_status_code(404)
            .with_header(Header::from_bytes(&b"Access-Control-Allow-Origin"[..], &b"*"[..]).unwrap());
        let _ = request.respond(response);
    }
}
