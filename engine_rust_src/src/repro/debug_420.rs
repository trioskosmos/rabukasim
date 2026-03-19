#[cfg(test)]
mod tests {
    use crate::core::logic::card_db::load_real_db;
    use crate::core::logic::models::AbilityContext;
    use crate::core::logic::action_factory::ActionFactory;

    #[test]
    fn debug_card_420() {
        let db = load_real_db();
        if let Some(card) = db.get_member(420) {
            println!("Card 420: {}", card.name);
            println!("Original Text: {}", card.original_text);
            println!("Ability Text: {}", card.ability_text);
            
            let ctx = AbilityContext {
                source_card_id: 420,
                ..Default::default()
            };
            let choice_text = ActionFactory::get_choice_text(&db, &ctx);
            println!("Choice Text: {}", choice_text);
            
            assert!(!choice_text.is_empty(), "Choice text for card 420 should not be empty!");
        } else {
            panic!("Card 420 not found in DB!");
        }
    }
}
