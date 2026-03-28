use crate::core::logic::{AbilityContext, CardDatabase};

pub fn source_ability<'a>(
    db: &'a CardDatabase,
    ctx: &AbilityContext,
) -> Option<&'a crate::core::logic::Ability> {
    let ability_index = usize::try_from(ctx.ability_index).ok()?;
    db.get_member(ctx.source_card_id)
        .and_then(|card| card.abilities.get(ability_index))
        .or_else(|| {
            db.get_live(ctx.source_card_id)
                .and_then(|card| card.abilities.get(ability_index))
        })
}

pub fn tap_opponent_chooser_player(_db: &CardDatabase, ctx: &AbilityContext) -> u8 {
    ctx.activator_id
}
