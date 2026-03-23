use std::fs;

use engine_rust::core::logic::card_db::CardDatabase;

fn main() {
    let json = fs::read_to_string("..\\engine\\gen\\cards_compiled.json").unwrap();
    let db = CardDatabase::from_json(&json).unwrap();
    if let Some(member) = db.get_member(4397) {
        println!("Member: {}", member.name);
        for (i, ab) in member.abilities.iter().enumerate() {
            println!("Ability {}:", i);
            if let Some(fp) = &ab.frame_program {
                for (j, frame) in fp.frames.iter().enumerate() {
                    println!("  Frame {}: {:?}", j, frame);
                }
            } else {
                println!("  No FrameProgram");
            }
        }
    } else {
        println!("Member 4397 not found");
    }
}
