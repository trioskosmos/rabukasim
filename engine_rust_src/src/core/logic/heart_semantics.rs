use serde_json::Value;

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

pub fn decode_heart_type_from_params(params: Option<&Value>) -> Option<usize> {
    params
        .and_then(|value| value.as_object())
        .and_then(|obj| obj.get("heart_type").or_else(|| obj.get("HEART_TYPE")))
        .and_then(decode_heart_type_value)
}

pub fn decode_heart_type_from_text(text: &str) -> Option<usize> {
    let lower = text.to_ascii_lowercase();

    if lower.contains("heart_00") || lower.contains("heart00") || lower.contains("heart0") {
        return Some(6);
    }
    
    // 1. Try explicit heart_type= pattern first
    if let Some(idx) = lower.find("heart_type=") {
        let tail = &lower[idx + "heart_type=".len()..];
        let token = tail
            .split(|ch: char| ch.is_whitespace() || ch == ',' || ch == '|' || ch == ')' || ch == ']')
            .find(|part| !part.is_empty())?;

        let color = match token.trim_matches(|ch: char| ch == '"' || ch == '\'' || ch == '{' || ch == '}') {
            "pink" | "heart_pink" => Some(0),
            "red" | "heart_red" => Some(1),
            "yellow" | "heart_yellow" => Some(2),
            "green" | "heart_green" => Some(3),
            "blue" | "heart_blue" => Some(4),
            "purple" | "heart_purple" => Some(5),
            "any" | "all" | "wild" => Some(6),
            other => other.parse::<u64>().ok().and_then(|num| decode_heart_type_value(&Value::from(num))),
        };
        if color.is_some() {
            return color;
        }
    }
    
    // 2. Try heart icon patterns like heart_02 or heart02
    for color in 1..=6 {
        let token = format!("heart_{:02}", color);
        if text.contains(&token) || text.contains(&format!("heart{:02}", color)) {
            return Some(color);
        }
    }
    
    // 3. Try color names in the text
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
    
    None
}

pub fn decode_heart_type_from_icons(text: &str) -> Option<usize> {
    if text.contains("heart_00") || text.contains("heart00") || text.contains("heart0") {
        return Some(6);
    }

    for color in 1..=6 {
        let token = format!("heart_{:02}", color);
        if text.contains(&token) || text.contains(&format!("heart{:02}", color)) {
            return Some(color);
        }
    }
    None
}
