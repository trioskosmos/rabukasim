use serde_json::Value;

#[inline]
fn get_param_case_insensitive<'a>(
    params: &'a serde_json::Map<String, serde_json::Value>,
    key: &str,
) -> Option<&'a serde_json::Value> {
    params.get(key).or_else(|| params.get(&key.to_uppercase()))
}

#[inline]
fn decode_heart_type_token(token: &str) -> Option<usize> {
    let trimmed = token.trim_matches(|ch: char| {
        ch == '"' || ch == '\'' || ch == '{' || ch == '}' || ch == '[' || ch == ']'
    });
    decode_heart_type_value(&Value::String(trimmed.to_string()))
}

#[inline]
fn decode_labeled_heart_type(text: &str) -> Option<usize> {
    let lower = text.to_ascii_lowercase();
    for marker in ["heart_type", "hearttype"] {
        let Some(idx) = lower.find(marker) else {
            continue;
        };

        let tail = &text[idx + marker.len()..];
        let token = tail
            .trim_start_matches(|ch: char| {
                ch.is_whitespace() || ch == '=' || ch == ':' || ch == '"' || ch == '\''
            })
            .split(|ch: char| {
                ch.is_whitespace()
                    || ch == ','
                    || ch == '|'
                    || ch == ')'
                    || ch == ']'
                    || ch == '}'
            })
            .find(|part| !part.is_empty())?;

        if let Some(color) = decode_heart_type_token(token) {
            return Some(color);
        }
    }

    None
}

#[inline]
pub fn decode_heart_type_value(value: &Value) -> Option<usize> {
    if let Some(text) = value.as_str() {
        let normalized = text.trim().to_ascii_uppercase();
        return match normalized.as_str() {
            "PINK" => Some(0),
            "RED" => Some(1),
            "YELLOW" => Some(2),
            "GREEN" => Some(3),
            "BLUE" => Some(4),
            "PURPLE" => Some(5),
            "ANY" | "ALL" | "WILD" => Some(6),
            _ => None,
        };
    }

    if let Some(num) = value.as_u64() {
        return match num {
            0 => Some(0),
            1..=6 => Some(num as usize),
            7 => Some(6),
            _ => None,
        };
    }

    None
}

#[inline]
pub fn decode_heart_type_from_params(params: Option<&Value>) -> Option<usize> {
    params
        .and_then(|value| value.as_object())
        .and_then(|obj| get_param_case_insensitive(obj, "heart_type"))
        .and_then(decode_heart_type_value)
}

pub fn decode_heart_type_from_text(text: &str) -> Option<usize> {
    let lower = text.to_ascii_lowercase();

    // 1. Try explicit heart_type markers first.
    if let Some(color) = decode_labeled_heart_type(text) {
        return Some(color);
    }

    // 2. Try heart icon patterns like heart_02 or heart02.
    if let Some(color) = decode_heart_type_from_icons(text) {
        return Some(color);
    }

    // 3. Try color names in the text.
    if lower.contains("yellow") || lower.contains("heart_yellow") {
        return Some(2);
    }
    if lower.contains("pink") || lower.contains("heart_pink") {
        return Some(0);
    }
    if lower.contains("red") || lower.contains("heart_red") {
        return Some(1);
    }
    if lower.contains("green") || lower.contains("heart_green") {
        return Some(3);
    }
    if lower.contains("blue") || lower.contains("heart_blue") {
        return Some(4);
    }
    if lower.contains("purple") || lower.contains("heart_purple") {
        return Some(5);
    }

    if lower.contains("heart_00") || lower.contains("heart00") || lower.contains("heart0") {
        return Some(6);
    }
    
    None
}

pub fn decode_heart_type_from_icons(text: &str) -> Option<usize> {
    let lower = text.to_ascii_lowercase();

    if lower.contains("heart_00") || lower.contains("heart00") {
        return Some(6);
    }

    for color in 1..=6 {
        let token = format!("heart_{:02}", color);
        if lower.contains(&token) || lower.contains(&format!("heart{:02}", color)) {
            return Some((color - 1) as usize);
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn decode_heart_type_from_text_parses_labeled_markers() {
        assert_eq!(decode_heart_type_from_text("heart_type=yellow"), Some(2));
        assert_eq!(decode_heart_type_from_text("{\"HEART_TYPE\":\"BLUE\"}"), Some(4));
        assert_eq!(decode_heart_type_from_text("heartType: purple"), Some(5));
    }

    #[test]
    fn decode_heart_type_from_text_falls_back_to_icons() {
        assert_eq!(decode_heart_type_from_text("Gain heart_03 and continue"), Some(2));
        assert_eq!(decode_heart_type_from_text("Reduce by heart_04"), Some(3));
        assert_eq!(decode_heart_type_from_text("Gain heart00"), Some(6));
    }

}
