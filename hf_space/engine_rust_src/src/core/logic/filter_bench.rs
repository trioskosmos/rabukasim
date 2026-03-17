use crate::core::logic::card_db::CardDatabase;
use crate::core::logic::card_db::MemberCard;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::models::AbilityContext;
use crate::core::logic::GameState;
use std::time::Instant;

pub fn run_benchmark() {
    let mut db = CardDatabase::default();
    
    // Create 100 member cards with names
    for i in 1..=100 {
        let mut m = MemberCard::default();
        m.card_id = i;
        m.name = format!("Member {}", i);
        if i % 10 == 0 {
            m.name = "優木せつ菜".to_string();
        } else if i % 5 == 0 {
            m.name = "澁谷かのん".to_string();
        }
        m.normalized_name = m.name.replace(" ", "");
        db.enrich_member(&mut m);
        db.members.insert(i, m.clone());
        let lid = CardDatabase::to_logic_id(i);
        db.members_vec[lid] = Some(m);
    }

    let state = GameState::default();
    let ctx = AbilityContext::default();
    
    // Create a filter for "せつ菜" (Character ID 27)
    let mut filter = CardFilter::default();
    filter.char_id_1 = 27;
    
    println!("Starting benchmark with character filter (Fast Path)...");
    let start = Instant::now();
    let iterations = 1_000_000;
    let mut _match_count = 0;
    
    for _ in 0..iterations {
        for cid in 1..=100 {
            if filter.matches(&state, &db, cid, None, false, None, &ctx) {
                _match_count += 1;
            }
        }
    }
    
    let duration = start.elapsed();
    println!("Completed {} iterations ({} total match checks) in {:?}", iterations, iterations * 100, duration);
    println!("Average time per match check: {:?}", duration / (iterations as u32 * 100));
}
