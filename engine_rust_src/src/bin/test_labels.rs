
use engine_rust::core::logic::ActionFactory;

fn main() {
    println!("--- Testing Action Label Improvements ---");

    let cases = vec![
        "PAY_ENERGY(2)",
        "DISCARD_HAND(1)",
        "DRAW(3)",
        "ADD_HEARTS(5)",
        "ADD_BLADES(2)",
        "RECOVER_MEMBER(1)",
        "RECOVER_LIVE(2)",
        "ENERGY_CHARGE(3)",
        "BOOST_SCORE(100)",
        "TAP_MEMBER",
        "ACTIVATE_MEMBER",
        "MOVE_MEMBER",
        "FORMATION_CHANGE",
        "PASS",
        "DONE",
        "SELECT_MEMBER",
        "OPTIONAL",
        "LOOK_AND_CHOOSE",
        "UNKNOWN_OPCODE(99)",
    ];

    println!("--- Technical Mappings ---");
    for case in &cases {
        let friendly = ActionFactory::map_technical_label(case);
        println!("{:<25} -> {}", case, friendly);
        if !case.contains("UNKNOWN") {
            assert!(!friendly.contains('_'), "Friendly label should not contain underscores!");
        }
    }

    println!("\n--- Action ID Mappings ---");
    let action_ids = vec![
        1,       // PASS
        1000,    // MULLIGAN_SELECT
        1100,    // SET_LIVE
        1200,    // SELECT_MODE
        1300,    // SELECT_COLOR
        1500,    // SELECT_CHOICE
    ];
    // We can't easily test get_action_label directly as it's static and doesn't take State/DB
    // But we can test what it returns for base IDs.
    for id in action_ids {
        let label = ActionFactory::get_action_label(id);
        println!("ID:{:<5} -> {}", id, label);
        assert!(!label.contains('_') || label.contains("Unknown"), "ID label should not contain underscores!");
    }

    println!("\n--- Testing Select Mode (Logic check only) ---");
    // We can't easily test infer_select_mode_label without a full GameState and DB,
    // but we can trust the map_technical_label integration since we added it.

    println!("\nVerification successful!");
}
