use criterion::{black_box, criterion_group, criterion_main, Criterion, BatchSize};
use engine_rust::core::logic::card_db::{CardDatabase, MemberCard};
use engine_rust::core::logic::filter::CardFilter;
use engine_rust::core::logic::models::{AbilityContext, GameState};
use std::time::Duration;

fn benchmark_card_filter(c: &mut Criterion) {
    let mut db = CardDatabase::default();

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

    let mut group = c.benchmark_group("card_filter");
    group.measurement_time(Duration::from_secs(5));
    group.sample_size(100);

    group.bench_function("character_filter_100_cards", |b| {
        let mut attr: u64 = 0;
        attr |= (27u64 & 0x7F) << 39;
        let filter = CardFilter::from_attr(attr as i64);

        b.iter(|| {
            let mut match_count = 0;
            for cid in 1..=100 {
                if filter.matches(&state, &db, cid, None, false, None, &ctx) {
                    match_count += 1;
                }
            }
            black_box(match_count);
        });
    });

    group.bench_function("filter_1000_iterations", |b| {
        let mut attr: u64 = 0;
        attr |= (27u64 & 0x7F) << 39;
        let filter = CardFilter::from_attr(attr as i64);

        b.iter(|| {
            for _ in 0..1000 {
                for cid in 1..=100 {
                    black_box(filter.matches(&state, &db, cid, None, false, None, &ctx));
                }
            }
        });
    });

    group.finish();
}

fn benchmark_game_state_clone(c: &mut Criterion) {
    let mut db = CardDatabase::default();

    for i in 1..=50 {
        let mut m = MemberCard::default();
        m.card_id = i;
        m.name = format!("Member {}", i);
        m.normalized_name = m.name.replace(" ", "");
        db.enrich_member(&mut m);
        db.members.insert(i, m.clone());
        let lid = CardDatabase::to_logic_id(i);
        db.members_vec[lid] = Some(m);
    }

    let deck: Vec<i32> = (1..=50).collect();
    let energy: Vec<i32> = (1..=12).collect();
    let lives: Vec<i32> = (1..=12).collect();

    let mut state = GameState::default();
    state.initialize_game(
        deck.clone(),
        deck.clone(),
        energy.clone(),
        energy.clone(),
        lives.clone(),
        lives.clone(),
    );

    let mut group = c.benchmark_group("game_state_operations");
    group.measurement_time(Duration::from_secs(5));
    group.sample_size(100);

    group.bench_function("clone_full_game_state", |b| {
        b.iter(|| {
            black_box(state.clone());
        });
    });

    group.bench_function("get_legal_actions_initial", |b| {
        b.iter(|| {
            black_box(state.get_legal_action_ids(&db));
        });
    });

    group.finish();
}

fn benchmark_database_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("database");
    group.measurement_time(Duration::from_secs(5));
    group.sample_size(100);

    group.bench_function("create_card_database", |b| {
        b.iter(|| {
            let db = CardDatabase::default();
            black_box(db);
        });
    });

    group.bench_function("card_lookup_by_id", |b| {
        let mut db = CardDatabase::default();
        for i in 1..=100 {
            let mut m = MemberCard::default();
            m.card_id = i;
            m.name = format!("Member {}", i);
            db.members.insert(i, m);
        }

        b.iter(|| {
            for i in 1..=100 {
                black_box(db.members.get(&i));
            }
        });
    });

    group.finish();
}

criterion_group!(
    benches,
    benchmark_card_filter,
    benchmark_game_state_clone,
    benchmark_database_operations
);
criterion_main!(benches);
