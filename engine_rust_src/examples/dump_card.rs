use engine_rust::core::logic::card_db::CardDatabase;

fn main() {
    let db = CardDatabase::load_from_json("..\\engine\\gen\\cards_compiled.json").unwrap();
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
