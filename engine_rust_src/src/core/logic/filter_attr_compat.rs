use crate::core::logic::filter::CardFilter;
use serde_json::Value;

fn group_id_from_name(name: &str) -> Option<u8> {
    match name {
        "HASUNOSORA" | "HASU" => Some(4),
        "LIELLA" => Some(3),
        "NIJIGASAKI" | "NIJIGAKU" | "NIJI" => Some(2),
        "AQOURS" | "AQUOURS" => Some(1),
        "MUSE" | "MUS" | "U'S" | "M'S" => Some(0),
        "ARISE" => Some(10),
        "SAINT_SNOW" => Some(11),
        "SUNNY_PASSION" => Some(12),
        "MUSICAL" => Some(13),
        _ => None,
    }
}

fn unit_id_from_name(name: &str) -> Option<u8> {
    match name {
        "PRINTEMPS" => Some(0),
        "LILY_WHITE" | "LILYWHITE" => Some(1),
        "BIBI" => Some(2),
        "CYARON" => Some(3),
        "AZALEA" => Some(4),
        "GUILTY_KISS" | "GUILTYKISS" => Some(5),
        "DIVER_DIVA" | "DIVERDIVA" => Some(6),
        "A_ZU_NA" | "AZUNA" => Some(7),
        "QU4RTZ" => Some(8),
        "R3BIRTH" => Some(9),
        "CATCHU" => Some(10),
        "KALEIDOSCORE" => Some(11),
        "5YNCRI5E" | "SYNCRISE" => Some(12),
        "CERISE_BOUQUET" | "CERISE" => Some(13),
        "DOLLCHESTRA" | "DOLL" => Some(14),
        "MIRA_CRA_PARK" | "MIRA-CRA" | "MIRAKURA" => Some(15),
        _ => None,
    }
}

pub fn card_filter_from_attr(a: i64) -> CardFilter {
    CardFilter::from_attr(a)
}

pub fn card_filter_to_attr(filter: &CardFilter) -> i64 {
    filter.to_attr() as i64
}

fn parse_semantic_heart_filter(part: &str) -> Option<(u8, u8)> {
    let upper = part.trim().to_uppercase();
    let token = upper.as_str();
    let token = token.strip_prefix("HAS_").unwrap_or(token);
    let token = token
        .strip_prefix("HEART_")
        .or_else(|| token.strip_prefix("COLOR_"))
        .unwrap_or(token);

    let (color_part, threshold_part) =
        token.rsplit_once("_X").or_else(|| token.rsplit_once('X'))?;

    let color_mask = match color_part {
        "SMILE" | "PINK" | "COLOR_0" | "00" | "0" => 1 << 0,
        "RED" | "COLOR_1" | "01" | "1" => 1 << 1,
        "YELLOW" | "COLOR_2" | "02" | "2" => 1 << 2,
        "GREEN" | "PURE" | "COLOR_3" | "03" | "3" => 1 << 3,
        "BLUE" | "COOL" | "COLOR_4" | "04" | "4" => 1 << 4,
        "PURPLE" | "COLOR_5" | "05" | "5" => 1 << 5,
        "ANY" | "ALL" | "COLOR_7" => 1 << 6,
        _ => return None,
    };

    let threshold = threshold_part.trim_start_matches('_').parse::<u8>().ok()?;
    Some((color_mask, threshold))
}

fn semantic_heart_mask_from_value(value: &Value) -> Option<u8> {
    if let Some(mask) = value.as_u64() {
        return match mask {
            0 => Some(1 << 0),
            1 => Some(1 << 1),
            2 => Some(1 << 2),
            3 => Some(1 << 3),
            4 => Some(1 << 4),
            5 => Some(1 << 5),
            6 => Some(1 << 6),
            _ => None,
        };
    }

    let value = value.as_str()?.trim().to_uppercase();
    match value.as_str() {
        "PINK" | "SMILE" => Some(1 << 0),
        "RED" => Some(1 << 1),
        "YELLOW" => Some(1 << 2),
        "GREEN" | "PURE" => Some(1 << 3),
        "BLUE" | "COOL" => Some(1 << 4),
        "PURPLE" => Some(1 << 5),
        "ANY" | "ALL" => Some(1 << 6),
        "0" | "COLOR_0" => Some(1 << 0),
        "1" | "COLOR_1" => Some(1 << 1),
        "2" | "COLOR_2" => Some(1 << 2),
        "3" | "COLOR_3" => Some(1 << 3),
        "4" | "COLOR_4" => Some(1 << 4),
        "5" | "COLOR_5" => Some(1 << 5),
        "6" | "COLOR_7" => Some(1 << 6),
        _ => None,
    }
}

fn apply_string_token(filter: &mut CardFilter, extras: &mut u64, part: &str) {
    let part_trimmed = part.trim();
    let part = part_trimmed.to_uppercase();
    if part.is_empty() {
        return;
    }

    if part == "OPPONENT" || part == "TARGET=OPPONENT" || part == "TARGET_OPPONENT" {
        filter.is_enabled = true;
        filter.target_player = 2;
        return;
    }
    if part == "SELF"
        || part == "ME"
        || part == "PLAYER"
        || part == "TARGET=SELF"
        || part == "TARGET_PLAYER"
    {
        filter.is_enabled = true;
        filter.target_player = 1;
        return;
    }
    if part == "BOTH" || part == "ALL" || part == "TARGET=BOTH" || part == "TARGET_ALL" {
        filter.is_enabled = true;
        filter.target_player = 3;
        return;
    }

    if part == "HAS_GROUP_AQOURS_OR_SAINT_SNOW" {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = 101;
        return;
    }

    if part_trimmed.contains("NAME_IN") {
        filter.is_enabled = true;
        filter.special_id = 1;
        // Extract and store the name in color_mask for now
        if let Some(eq_pos) = part_trimmed.find('=') {
            let name_value = part_trimmed[eq_pos + 1..].trim();
            // Store first character as a simple hash in color_mask
            if let Some(first_char) = name_value.chars().next() {
                filter.color_mask = (first_char as u8) & 0x7F;
            }
        }
        return;
    }
    if part_trimmed.contains("NOT_NAME=MY") {
        filter.is_enabled = true;
        filter.special_id = 2;
        return;
    }
    if part == "SAME_NAME_AS_REVEALED" {
        filter.is_enabled = true;
        filter.special_id = 4;
        return;
    }
    if part == "SELECTED_DISCARD" {
        filter.is_enabled = true;
        filter.special_id = 6;
        return;
    }

    if let Some((color_mask, threshold)) = parse_semantic_heart_filter(part_trimmed) {
        filter.is_enabled = true;
        filter.value_enabled = true;
        filter.value_threshold = threshold;
        filter.is_le = false;
        filter.is_cost_type = false;
        filter.color_mask = color_mask;
        return;
    }

    if part.starts_with("COST") {
        let val_str = if part.contains('=') {
            part.split('=').last()
        } else {
            part.split('_').last()
        };
        if let Some(s) = val_str {
            if let Ok(threshold) = s.parse::<u8>() {
                filter.is_enabled = true;
                filter.value_enabled = true;
                filter.value_threshold = threshold;
                filter.is_le = part.contains("_LE");
                filter.is_cost_type = true;
            }
        }
        return;
    }

    if part.starts_with("GROUP_ID=") || part.starts_with("GROUP_ID_") {
        let gid_str = if part.contains('=') {
            part.split('=').last()
        } else {
            part.split('_').last()
        };
        if let Some(s) = gid_str {
            if let Ok(gid) = s.parse::<u8>() {
                filter.is_enabled = true;
                filter.group_enabled = true;
                filter.group_id = gid;
            }
        }
        return;
    }

    if part.starts_with("UNIT_") {
        let unit_name = part.replace("UNIT_", "").replace("_ONLY", "");
        if let Some(unit_id) = unit_id_from_name(unit_name.as_str()) {
            filter.is_enabled = true;
            filter.unit_enabled = true;
            filter.unit_id = unit_id;
        } else if let Some(group_id) = group_id_from_name(unit_name.as_str()) {
            filter.is_enabled = true;
            filter.group_enabled = true;
            filter.group_id = group_id;
        }
        return;
    }

    if part == "TAPPED" || part == "STATUS=TAPPED" {
        filter.is_enabled = true;
        filter.is_tapped = true;
    } else if part == "HAS_BLADE_HEART" {
        filter.is_enabled = true;
        filter.has_blade_heart = true;
    } else if part == "NOT_HAS_BLADE_HEART" {
        filter.is_enabled = true;
        filter.not_has_blade_heart = true;
    } else if part == "TYPE_MEMBER" {
        filter.is_enabled = true;
        filter.card_type = 1;
    } else if part == "TYPE_LIVE" {
        filter.is_enabled = true;
        filter.card_type = 2;
    } else if part == "AQOURS" || part == "AQUOURS" {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = 1;
    } else if part == "M'S" || part == "U'S" || part == "MUSE" || part == "MUS" {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = 0;
    } else if part == "UNIQUE_NAMES=TRUE" || part == "UNIQUE_NAMES" || part == "SAME_UNIQUE_NAMES" {
        filter.is_enabled = true;
        filter.unique_names = true;
    } else if part == "SMILE" || part == "PINK" || part == "COLOR_0" {
        filter.is_enabled = true;
        filter.color_mask |= 1 << 0;
    } else if part == "PURE" || part == "GREEN" || part == "COLOR_3" {
        filter.is_enabled = true;
        filter.color_mask |= 1 << 3;
    } else if part == "COOL" || part == "BLUE" || part == "COLOR_4" {
        filter.is_enabled = true;
        filter.color_mask |= 1 << 4;
    } else if part == "RED" || part == "COLOR_1" {
        filter.is_enabled = true;
        filter.color_mask |= 1 << 1;
    } else if part == "YELLOW" || part == "COLOR_2" {
        filter.is_enabled = true;
        filter.color_mask |= 1 << 2;
    } else if part == "PURPLE" || part == "COLOR_5" {
        filter.is_enabled = true;
        filter.color_mask |= 1 << 5;
    } else if part == "ANY" || part == "COLOR_7" {
        filter.is_enabled = true;
        filter.color_mask |= 1 << 6;
    } else if part.starts_with("BLADE_LE") {
        let val_str = part.replace("BLADE_LE", "").replace("_", "");
        if let Ok(threshold) = val_str.parse::<u8>() {
            filter.is_enabled = true;
            filter.value_enabled = true;
            filter.value_threshold = threshold;
            filter.is_le = true;
            *extras |= crate::core::generated_constants::FILTER_BLADE_FILTER_FLAG;
        }
    } else if part.starts_with("BLADE_GE") {
        let val_str = part.replace("BLADE_GE", "").replace("_", "");
        if let Ok(threshold) = val_str.parse::<u8>() {
            filter.is_enabled = true;
            filter.value_enabled = true;
            filter.value_threshold = threshold;
            filter.is_le = false;
            *extras |= crate::core::generated_constants::FILTER_BLADE_FILTER_FLAG;
        }
    } else if part == "COST_LE_REVEALED" {
        filter.is_enabled = true;
        filter.value_enabled = true;
        filter.value_threshold = 1;
        filter.is_le = true;
        filter.is_cost_type = true;
        *extras |= crate::core::generated_constants::FILTER_REVEALED_CONTEXT;
    } else if part == "HEART_PINK" {
        filter.is_enabled = true;
        filter.color_mask |= 1 << 0;
    } else if part == "HEART_BLUE" {
        filter.is_enabled = true;
        filter.color_mask |= 1 << 4;
    } else if part == "HASUNOSORA" || part == "HASU" {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = 4;
    } else if part == "LIELLA" {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = 3;
    } else if part == "NIJIGASAKI" || part == "NIJIGAKU" || part == "NIJI" {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = 2;
    } else if part == "ARISE" {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = 10;
    } else if part == "SAINT_SNOW" {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = 11;
    } else if part == "SUNNY_PASSION" {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = 12;
    } else if part == "MUSICAL" {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = 13;
    }
}

fn filter_from_semantic_string(filter: &str) -> (CardFilter, u64) {
    let mut parsed = CardFilter::default();
    let mut extras = 0u64;
    for part in filter.split(',') {
        apply_string_token(&mut parsed, &mut extras, part);
    }
    (parsed, extras)
}

pub fn map_filter_string_to_attr(filter: &str) -> u64 {
    let (parsed, extras) = filter_from_semantic_string(filter);
    card_filter_to_attr(&parsed) as u64 | extras
}

fn as_bool_robust(v: &serde_json::Value) -> bool {
    v.as_bool()
        .unwrap_or_else(|| v.as_i64().map(|i| i != 0).unwrap_or(false))
}

fn params_object<'a>(
    params: Option<&'a serde_json::Value>,
) -> Option<&'a serde_json::Map<String, serde_json::Value>> {
    let mut obj = params.and_then(|value| value.as_object())?;

    if let Some(sub) = obj.get("attr").or_else(|| obj.get("filter")) {
        if let Some(sub_obj) = sub.as_object() {
            obj = sub_obj;
        }
    }

    Some(obj)
}

pub fn filter_attr_from_params(params: Option<&serde_json::Value>) -> Option<u64> {
    let obj = params_object(params)?;

    let mut filter = CardFilter::default();
    let mut extras = 0u64;

    if let Some(value) = obj.get("target_player") {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.target_player = (v & 0x3) as u8;
        } else if let Some(v) = value.as_str() {
            filter.is_enabled = true;
            filter.target_player = match v.to_uppercase().as_str() {
                "SELF" | "ME" | "PLAYER" => 1,
                "OPPONENT" => 2,
                "BOTH" | "ALL" => 3,
                _ => 0,
            };
        }
    }
    if let Some(value) = obj.get("card_type") {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.card_type = (v & 0x3) as u8;
        } else if let Some(v) = value.as_str() {
            filter.is_enabled = true;
            filter.card_type = match v.to_uppercase().as_str() {
                "MEMBER" => 1,
                "LIVE" => 2,
                _ => 0,
            };
        }
    }
    if let Some(value) = obj.get("group_enabled") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.group_enabled = true;
        }
    }
    if let Some(value) = obj.get("group_id") {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.group_enabled = true;
            filter.group_id = (v & 0x7F) as u8;
        }
    }
    if let Some(value) = obj.get("is_tapped") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.is_tapped = true;
        }
    }
    if let Some(value) = obj.get("has_blade_heart") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.has_blade_heart = true;
        }
    }
    if let Some(value) = obj.get("not_has_blade_heart") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.not_has_blade_heart = true;
        }
    }
    if let Some(value) = obj.get("unique_names") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.unique_names = true;
        }
    }
    if let Some(value) = obj.get("unit_enabled") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.unit_enabled = true;
        }
    }
    if let Some(value) = obj.get("unit_id") {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.unit_enabled = true;
            filter.unit_id = (v & 0x7F) as u8;
        }
    }
    if let Some(value) = obj.get("value_enabled") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.value_enabled = true;
        }
    }
    if let Some(value) = obj.get("value_threshold") {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.value_enabled = true;
            filter.value_threshold = (v & 0x1F) as u8;
        }
    }
    if let Some(value) = obj.get("is_le") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.is_le = true;
        }
    }
    if let Some(value) = obj.get("is_cost_type") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.is_cost_type = true;
        }
    }
    if let Some(value) = obj.get("heart_color").or_else(|| obj.get("heart_type")) {
        if let Some(mask) = semantic_heart_mask_from_value(value) {
            filter.is_enabled = true;
            filter.value_enabled = true;
            filter.color_mask = mask;
        }
    }
    if let Some(value) = obj
        .get("heart_count")
        .or_else(|| obj.get("min_count"))
        .or_else(|| obj.get("min"))
        .or_else(|| obj.get("count"))
        .or_else(|| obj.get("threshold"))
        .or_else(|| obj.get("value"))
    {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.value_enabled = true;
            filter.value_threshold = (v & 0x1F) as u8;
        }
    }
    if let Some(value) = obj.get("char_id_1") {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.char_id_1 = (v & 0x7F) as u8;
        }
    }
    if let Some(value) = obj.get("char_id_2") {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.char_id_2 = (v & 0x7F) as u8;
        }
    }
    if let Some(value) = obj.get("char_id_3") {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.char_id_3 = (v & 0x7F) as u8;
        }
    }
    if let Some(value) = obj.get("zone_mask") {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.zone_mask = (v & 0x7) as u8;
        }
    }
    if let Some(value) = obj.get("special_id") {
        if let Some(v) = value.as_u64() {
            filter.is_enabled = true;
            filter.special_id = (v & 0x7) as u8;
        } else if let Some(v) = value.as_str() {
            filter.is_enabled = true;
            filter.special_id = match v.to_uppercase().replace('_', " ").replace('-', " ").as_str()
            {
                "SAME NAME" | "SAMENAME" => 4,
                "NOT MY" | "NOTMY" => 2,
                "NOT SELF" | "NOTSELF" => 3,
                _ => 0,
            };
        }
    }
    if let Some(value) = obj.get("is_setsuna") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.is_setsuna = true;
        }
    }
    if let Some(value) = obj.get("compare_accumulated") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.compare_accumulated = true;
        }
    }
    if let Some(value) = obj.get("is_optional") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.is_optional = true;
        }
    }
    if let Some(value) = obj.get("keyword_energy") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.keyword_energy = true;
        }
    }
    if let Some(value) = obj.get("keyword_member") {
        if as_bool_robust(value) {
            filter.is_enabled = true;
            filter.keyword_member = true;
        }
    }

    if let Some(filter_str) = obj.get("FILTER").or_else(|| obj.get("filter")) {
        if let Some(filter_str) = filter_str.as_str() {
            let normalized = filter_str.trim();
            if normalized.eq_ignore_ascii_case("Umi/Yoshiko/Rina")
                || normalized.eq_ignore_ascii_case("Umi / Yoshiko / Rina")
            {
                let mut special = CardFilter::default();
                special.is_enabled = true;
                special.char_id_1 = 4;
                special.char_id_2 = 16;
                special.is_optional = obj
                    .get("is_optional")
                    .or_else(|| obj.get("IS_OPTIONAL"))
                    .map(|value| as_bool_robust(value))
                    .unwrap_or(true);
                return Some(card_filter_to_attr(&special) as u64);
            }
            let (parsed, parsed_extras) = filter_from_semantic_string(filter_str);
            filter = parsed;
            extras |= parsed_extras;
        }
    }

    let attr = card_filter_to_attr(&filter) as u64 | extras;
    if attr == 0 {
        None
    } else {
        Some(attr)
    }
}
