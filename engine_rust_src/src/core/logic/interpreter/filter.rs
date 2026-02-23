//! # Filtering Logic
//!
//! This module contains the logic for parsing filter strings into attribute bitmasks.

pub fn map_filter_string_to_attr(filter: &str) -> u64 {
    let mut attr: u64 = 0;
    for part in filter.split(',') {
        let part = part.trim().to_uppercase();
        if part.is_empty() { continue; }

        if part.starts_with("COST") {
            let val_str = if part.contains('=') {
                part.split('=').last()
            } else {
                part.split('_').last()
            };
            if let Some(s) = val_str {
                if let Ok(threshold) = s.parse::<i32>() {
                    attr |= 0x01000000 | ((threshold as u64) << 25);
                    if part.contains("_LE") { attr |= 0x40000000u64; }
                }
            }
        } else if part.starts_with("GROUP_ID=") || part.starts_with("GROUP_ID_") {
             let gid_str = if part.contains('=') {
                 part.split('=').last()
             } else {
                 part.split('_').last()
             };
              if let Some(s) = gid_str {
                 if let Ok(gid) = s.parse::<i32>() {
                    attr |= 0x10 | ((gid as u64) << 5);
                 }
              }
        } else if part.starts_with("UNIT_") {
            let unit_name = part.replace("UNIT_", "").replace("_ONLY", "");
            let unit_id = match unit_name.as_str() {
                "BIBI" => 0, "LILY_WHITE" | "LILYWHITE" => 2, "QU4RTZ" => 12, "AZUNA" => 11, "DIVERDIVA" => 13, "A_ZU_NA" => 11,
                _ => -1,
            };
            if unit_id >= 0 { attr |= 0x10000 | ((unit_id as u64) << 17); }
        } else if part == "TAPPED" {
            attr |= 0x1000; // Bit 12
        } else if part == "HAS_BLADE_HEART" {
            attr |= 0x2000; // Bit 13
        } else if part == "NOT_HAS_BLADE_HEART" {
            attr |= 0x4000; // Bit 14
        } else if part == "TYPE_MEMBER" {
            attr |= 0x04; // Bit 2 (1<<2 = 4)
        } else if part == "TYPE_LIVE" {
            attr |= 0x08; // Bit 3 (2<<2 = 8)
        } else if part == "AQOURS" {
            attr |= 0x10 | (1 << 5);
        } else if part == "M'S" || part == "μ'S" || part == "U'S" {
            attr |= 0x10 | (0 << 5);
        } else if part.contains("NAME_IN") && part.contains("澁谷かのん") {
            attr |= 1u64 << 48; // Special ID 1 (Moved to avoid collision with Group ID)
        } else if part.contains("NOT_NAME=MY舞") {
            attr |= 2u64 << 48; // Special ID 2 (Moved to avoid collision with Group ID)
        } else if part == "UNIQUE_NAMES=TRUE" || part == "UNIQUE_NAMES" || part == "SAME_UNIQUE_NAMES" {
            attr |= 0x8000; // Bit 15
        } else if part == "SMILE" || part == "PINK" || part == "COLOR_0" {
            attr |= 1u64 << 32;
        } else if part == "PURE" || part == "GREEN" || part == "COLOR_1" {
            attr |= 1u64 << 33;
        } else if part == "COOL" || part == "BLUE" || part == "COLOR_2" {
            attr |= 1u64 << 34;
        } else if part == "ALL_STARS_RED" || part == "RED" || part == "COLOR_3" {
            attr |= 1u64 << 35;
        } else if part == "ALL_STARS_YELLOW" || part == "YELLOW" || part == "COLOR_4" {
            attr |= 1u64 << 36;
        } else if part == "ALL_STARS_BLUE" || part == "LTBLUE" || part == "COLOR_5" {
            attr |= 1u64 << 37;
        } else if part == "ALL_STARS_PURPLE" || part == "PURPLE" || part == "COLOR_6" {
            attr |= 1u64 << 38;
        } else if part.starts_with("BLADE_LE") {
            // BLADE_LE_3 などのブレード制限フィルタ
            let val_str = part.replace("BLADE_LE", "").replace("_", "");
            if let Ok(threshold) = val_str.parse::<i32>() {
                attr |= 0x02000000 | ((threshold as u64) << 25); // Use bit 25 for threshold
                attr |= 0x40000000u64; // LE flag
            }
        } else if part.starts_with("BLADE_GE") {
            // BLADE_GE_5 などのブレード下限制限フィルタ
            let val_str = part.replace("BLADE_GE", "").replace("_", "");
            if let Ok(threshold) = val_str.parse::<i32>() {
                attr |= 0x02000000 | ((threshold as u64) << 25);
            }
        } else if part == "COST_LE_REVEALED" {
            // 公開されたカードのコスト制限
            attr |= 0x01000000 | (1u64 << 25);
            attr |= 0x40000000u64; // LE flag
            attr |= 1u64 << 43; // Bit 43: REVEALED context
        } else if part == "HEART_PINK" {
            attr |= 1u64 << 32; // Same as PINK
        } else if part == "HEART_BLUE" {
            attr |= 1u64 << 34; // Same as BLUE/COOL
        } else if part == "HASUNOSORA" {
            attr |= 0x10 | (4 << 5); // Group ID 4 for Hasunosora
        } else if part == "LIELLA" {
            attr |= 0x10 | (3 << 5); // Group ID 3 for Liella
        } else if part == "NIJIGASAKI" || part == "NIJIGAKU" {
            attr |= 0x10 | (2 << 5); // Group ID 2 for Nijigasaki
        }
    }
    attr
}
