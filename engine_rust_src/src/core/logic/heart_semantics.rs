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
