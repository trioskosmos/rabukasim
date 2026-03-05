use crate::core::enums::Zone;
use crate::core::generated_layout::*;

#[derive(Debug, Clone, Copy, Default)]
pub struct DecodedSlot {
    pub target_slot: u8,
    pub source_zone: Zone,
    pub dest_zone: Zone,
    pub count_op: u8,
    pub is_dynamic: bool,
    pub is_opponent: bool,
    pub is_reveal_until_live: bool,
    pub is_empty_slot_only: bool,
    pub is_wait: bool,
    pub area_idx: u8,
}

impl DecodedSlot {
    pub fn decode(raw_s: i32) -> Self {
        let s = raw_s as u32;
        let source_zone_val = ((s >> S_STANDARD_SOURCE_ZONE_SHIFT) & S_STANDARD_SOURCE_ZONE_MASK as u32) as u8;
        let dest_zone_val = ((s >> S_STANDARD_DEST_ZONE_SHIFT) & S_STANDARD_DEST_ZONE_MASK as u32) as u8;

        Self {
            target_slot: ((s >> S_STANDARD_TARGET_SLOT_SHIFT) & S_STANDARD_TARGET_SLOT_MASK as u32) as u8,
            source_zone: Self::decode_zone(source_zone_val),
            dest_zone: Self::decode_zone(dest_zone_val),
            count_op: ((s >> S_STANDARD_REMAINDER_ZONE_SHIFT) & S_STANDARD_REMAINDER_ZONE_MASK as u32) as u8,
            is_dynamic: ((s >> S_STANDARD_IS_DYNAMIC_SHIFT) & S_STANDARD_IS_DYNAMIC_MASK as u32) != 0,
            is_opponent: ((s >> S_STANDARD_IS_OPPONENT_SHIFT) & S_STANDARD_IS_OPPONENT_MASK as u32) != 0,
            is_reveal_until_live: ((s >> S_STANDARD_IS_REVEAL_UNTIL_LIVE_SHIFT) & S_STANDARD_IS_REVEAL_UNTIL_LIVE_MASK as u32) != 0,
            is_empty_slot_only: ((s >> S_STANDARD_IS_EMPTY_SLOT_SHIFT) & S_STANDARD_IS_EMPTY_SLOT_MASK as u32) != 0,
            is_wait: ((s >> S_STANDARD_IS_WAIT_SHIFT) & S_STANDARD_IS_WAIT_MASK as u32) != 0,
            area_idx: ((s >> S_STANDARD_AREA_IDX_SHIFT) & S_STANDARD_AREA_IDX_MASK as u32) as u8,
        }
    }

    fn decode_zone(val: u8) -> Zone {
        match val {
            1 => Zone::DeckTop,
            2 => Zone::DeckBottom,
            3 => Zone::Energy,
            4 => Zone::Stage,
            6 => Zone::Hand,
            7 => Zone::Discard,
            8 => Zone::Deck,
            13 => Zone::LiveSet,
            14 => Zone::SuccessPile,
            15 => Zone::Yell,
            _ => Zone::Default,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct BytecodeInstruction {
    pub op: i32,
    pub v: i32,
    pub a: i64,
    pub s: DecodedSlot,
    pub raw_s: i32,
}

impl BytecodeInstruction {
    pub fn new(op: i32, v: i32, a: i64, raw_s: i32) -> Self {
        Self {
            op,
            v,
            a,
            s: DecodedSlot::decode(raw_s),
            raw_s,
        }
    }

    pub fn decode(bytecode: &[i32], ip: usize) -> Self {
        let op = bytecode[ip];
        let v = if ip + 1 < bytecode.len() { bytecode[ip + 1] } else { 0 };
        let a_low = if ip + 2 < bytecode.len() { bytecode[ip + 2] } else { 0 } as u32;
        let a_high = if ip + 3 < bytecode.len() { bytecode[ip + 3] } else { 0 } as u32;
        let raw_s = if ip + 4 < bytecode.len() { bytecode[ip + 4] } else { 0 };

        let a = ((a_high as i64) << 32) | (a_low as i64);

        Self::new(op, v, a, raw_s)
    }
}
