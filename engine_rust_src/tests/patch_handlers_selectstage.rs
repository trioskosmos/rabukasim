use std::fs;
use std::path::PathBuf;

#[test]
fn patch_handlers_selectstage() {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.push("src/core/logic/handlers.rs");

    let text = fs::read_to_string(&path).expect("read handlers.rs");
    let old = r#"        self.ui.current_execution_id = if execution_id > 0 {
            Some(execution_id)
        } else {
            None
        };

        let slot_idx = ctx_res.area_idx as usize;
        let ab_idx_call = if ctx_res.ability_index < 0 {
            0
        } else {
            ctx_res.ability_index as usize
        };
        let target_slot = ctx_res.target_slot as i32;

        self.activate_ability_with_choice(db, slot_idx, ab_idx_call, choice_idx, target_slot)?;
"#;
    let new = r#"        self.ui.current_execution_id = if execution_id > 0 {
            Some(execution_id)
        } else {
            None
        };

        let pending_choice_type = self
            .interaction_stack
            .last()
            .map(|pi| pi.choice_type)
            .unwrap_or(ChoiceType::None);

        let slot_idx = ctx_res.area_idx as usize;
        let ab_idx_call = if ctx_res.ability_index < 0 {
            0
        } else {
            ctx_res.ability_index as usize
        };
        let target_slot = ctx_res.target_slot as i32;

        if pending_choice_type == ChoiceType::SelectStage {
            self.resume_play_member(db, choice_idx, 0)?;
            self.clear_execution_id();
            crate::core::logic::interpreter::restore_response_state(
                self,
                response_origin.0,
                response_origin.1,
            );
            self.check_win_condition();
            return Ok(());
        }

        self.activate_ability_with_choice(db, slot_idx, ab_idx_call, choice_idx, target_slot)?;
"#;

    assert!(text.contains(old), "target block not found");
    let patched = text.replace(old, new);
    fs::write(&path, patched).expect("write handlers.rs");
}
