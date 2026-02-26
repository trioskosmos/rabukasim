//! # Filtering Logic
//!
//! This module contains the logic for parsing filter strings into attribute bitmasks.

use crate::core::enums::*;
use super::constants::*;

pub fn map_filter_string_to_attr(filter: &str) -> u64 {
    let mut attr: u64 = 0;
    for part in filter.split(',') {
        let part_trimmed = part.trim();
        let part = part_trimmed.to_uppercase();
        if part.is_empty() { continue; }

        // Check for NAME_IN with Japanese characters before uppercase conversion
        if part_trimmed.contains("NAME_IN") && part_trimmed.contains("澁谷かのん") {
            attr |= 1u64 << FILTER_SPECIAL_SHIFT;
            continue;
        }
        if part_trimmed.contains("NOT_NAME=MY舞") {
            attr |= 2u64 << FILTER_SPECIAL_SHIFT;
            continue;
        }

        if part.starts_with("COST") {
            let val_str = if part.contains('=') {
                part.split('=').last()
            } else {
                part.split('_').last()
            };
            if let Some(s) = val_str {
                if let Ok(threshold) = s.parse::<i32>() {
                    attr |= FILTER_COST_FLAG | ((threshold as u64) << FILTER_VALUE_SHIFT);
                    if part.contains("_LE") { attr |= FILTER_IS_LE; }
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
                    attr |= FILTER_GROUP_FLAG | ((gid as u64) << FILTER_GROUP_SHIFT);
                 }
              }
        } else if part.starts_with("UNIT_") {
            let unit_name = part.replace("UNIT_", "").replace("_ONLY", "");
            let unit_id: i32 = match unit_name.as_str() {
                "PRINTEMPS" => 0, 
                "LILY_WHITE" | "LILYWHITE" => 1,
                "BIBI" => 2,
                "CYARON" | "CYARON!" => 3,
                "AZALEA" => 4,
                "GUILTY_KISS" | "GUILTYKISS" => 5,
                "DIVER_DIVA" | "DIVERDIVA" => 6,
                "A_ZU_NA" | "AZUNA" => 7,
                "QU4RTZ" => 8,
                "R3BIRTH" => 9,
                "CATCHU" | "CATCHU!" => 10,
                "KALEIDOSCORE" => 11,
                "5YNCRI5E" | "SYNCRISE" => 12,
                "CERISE_BOUQUET" | "CERISE" => 13,
                "DOLLCHESTRA" => 14,
                "MIRA_CRA_PARK" | "MIRACRA" | "MIRACRA_PARK" => 15,
                "EDEL_NOTE" | "EDELNOTE" => 16,
                _ => -1,
            };
            if unit_id >= 0 { attr |= FILTER_UNIT_FLAG | ((unit_id as u64) << FILTER_UNIT_SHIFT); }
        } else if part == "TAPPED" {
            attr |= FILTER_TAPPED;
        } else if part == "HAS_BLADE_HEART" {
            attr |= FILTER_HAS_BLADE_HEART;
        } else if part == "NOT_HAS_BLADE_HEART" {
            attr |= FILTER_NOT_HAS_BLADE_HEART;
        } else if part == "TYPE_MEMBER" {
            attr |= FILTER_TYPE_MEMBER;
        } else if part == "TYPE_LIVE" {
            attr |= FILTER_TYPE_LIVE;
        } else if part == "AQOURS" {
            attr |= FILTER_GROUP_FLAG | (1 << FILTER_GROUP_SHIFT);
        } else if part == "M'S" || part == "μ'S" || part == "U'S" || part == "MUSE" {
            attr |= FILTER_GROUP_FLAG | (0 << FILTER_GROUP_SHIFT);
        } else if part == "UNIQUE_NAMES=TRUE" || part == "UNIQUE_NAMES" || part == "SAME_UNIQUE_NAMES" {
            attr |= FILTER_UNIQUE_NAMES;
        } else if part == "SMILE" || part == "PINK" || part == "COLOR_0" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 0);
        } else if part == "PURE" || part == "GREEN" || part == "COLOR_1" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 1);
        } else if part == "COOL" || part == "BLUE" || part == "COLOR_2" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 2);
        } else if part == "ALL_STARS_RED" || part == "RED" || part == "COLOR_3" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 3);
        } else if part == "ALL_STARS_YELLOW" || part == "YELLOW" || part == "COLOR_4" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 4);
        } else if part == "ALL_STARS_BLUE" || part == "LTBLUE" || part == "COLOR_5" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 5);
        } else if part == "ALL_STARS_PURPLE" || part == "PURPLE" || part == "COLOR_6" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 6);
        } else if part.starts_with("BLADE_LE") {
            let val_str = part.replace("BLADE_LE", "").replace("_", "");
            if let Ok(threshold) = val_str.parse::<i32>() {
                attr |= FILTER_BLADE_FILTER_FLAG | ((threshold as u64) << FILTER_VALUE_SHIFT);
                attr |= FILTER_IS_LE;
            }
        } else if part.starts_with("BLADE_GE") {
            let val_str = part.replace("BLADE_GE", "").replace("_", "");
            if let Ok(threshold) = val_str.parse::<i32>() {
                attr |= FILTER_BLADE_FILTER_FLAG | ((threshold as u64) << FILTER_VALUE_SHIFT);
            }
        } else if part == "COST_LE_REVEALED" {
            attr |= FILTER_COST_FLAG | (1u64 << FILTER_VALUE_SHIFT);
            attr |= FILTER_IS_LE;
            attr |= FILTER_REVEALED_CONTEXT;
        } else if part == "HEART_PINK" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 0);
        } else if part == "HEART_BLUE" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 2);
        } else if part == "HASUNOSORA" {
            attr |= FILTER_GROUP_FLAG | (4 << FILTER_GROUP_SHIFT);
        } else if part == "LIELLA" {
            attr |= FILTER_GROUP_FLAG | (3 << FILTER_GROUP_SHIFT);
        } else if part == "NIJIGASAKI" || part == "NIJIGAKU" {
            attr |= FILTER_GROUP_FLAG | (2 << FILTER_GROUP_SHIFT);
        }
    }
    attr
}
