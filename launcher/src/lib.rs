use rust_embed::RustEmbed;

pub mod models;
pub mod serialization;
pub mod utils;
pub mod handlers;

#[derive(RustEmbed)]
#[folder = "static_content/"]
pub struct Assets;

#[derive(RustEmbed)]
#[folder = "../ai/decks/"]
pub struct Decks;

// Forced rebuild for static assets update
