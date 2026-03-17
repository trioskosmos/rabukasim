use super::models::TurnEvent;
use super::state::GameState;

impl GameState {
    pub fn log(&mut self, msg: String) {
        if self.ui.silent {
            return;
        }

        let (turn_prefix, body) = if msg.starts_with("[Turn") {
            if let Some(idx) = msg.find("] ") {
                (msg[..=idx].to_string(), msg[idx + 2..].to_string())
            } else {
                (format!("[Turn {}]", self.turn), msg)
            }
        } else {
            (format!("[Turn {}]", self.turn), msg)
        };

        let full_msg = if let Some(id) = self.ui.current_execution_id {
            format!("{} [ID: {}] {}", turn_prefix, id, body)
        } else {
            format!("{} {}", turn_prefix, body)
        };

        if self.ui.rule_log.is_none() {
            self.ui.rule_log = Some(Vec::with_capacity(32));
        }
        self.ui.rule_log.as_mut().unwrap().push(full_msg);
    }

    pub fn log_rule(&mut self, rule: &str, msg: &str) {
        self.log_event("RULE", msg, -1, -1, self.current_player, Some(rule), true);
    }

    pub fn log_turn_event(
        &mut self,
        event_type: &str,
        source_cid: i32,
        ability_idx: i16,
        player_id: u8,
        description: &str,
    ) {
        if self.ui.silent {
            return;
        }
        let turn = self.turn as u32;
        let phase = self.phase;
        if self.core.turn_history.is_none() {
            self.core.turn_history = Some(Vec::with_capacity(64));
        }
        let history = self.core.turn_history.as_mut().unwrap();
        if history.len() > 2000 {
            return;
        }
        history.push(TurnEvent {
            turn,
            phase,
            player_id,
            event_type: event_type.to_string(),
            source_cid,
            ability_idx,
            description: description.to_string(),
        });
    }

    pub fn trace_internal(&mut self, msg: &str) {
        if self.debug.debug_mode {
            let trace_msg = format!("[TRC] {}", msg);
            self.debug.trace_log.push(trace_msg);
        }
    }

    pub fn log_event(
        &mut self,
        event_type: &str,
        description: &str,
        source_cid: i32,
        ability_idx: i16,
        player_id: u8,
        rule_ref: Option<&str>,
        log_to_rule_log: bool,
    ) {
        let turn = self.turn as u32;
        let phase = self.phase;
        let silent = self.ui.silent;

        if !silent {
            if self.core.turn_history.is_none() {
                self.core.turn_history = Some(Vec::with_capacity(64));
            }
            let history = self.core.turn_history.as_mut().unwrap();
            if history.len() < 2000 {
                history.push(TurnEvent {
                    turn,
                    phase,
                    player_id,
                    event_type: event_type.to_string(),
                    source_cid,
                    ability_idx,
                    description: description.to_string(),
                });
            }
        }

        if log_to_rule_log && !silent {
            let turn_prefix = format!("[Turn {}]", turn);
            let rule_prefix = rule_ref.map(|rule| format!("[{}] ", rule)).unwrap_or_default();
            let full_msg = format!("{}{}{}", turn_prefix, rule_prefix, description);
            if self.ui.rule_log.is_none() {
                self.ui.rule_log = Some(Vec::with_capacity(32));
            }
            self.ui.rule_log.as_mut().unwrap().push(full_msg);
        }
    }
}