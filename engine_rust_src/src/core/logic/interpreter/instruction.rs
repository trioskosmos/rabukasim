use crate::core::enums::Zone;
// Removed unused FLAG_TARGET_OPPONENT

#[derive(Debug, Clone, Copy, Default)]
pub struct DecodedSlot {
    pub target_slot: u8,
    pub source_zone: Zone,
    pub dest_zone: Zone,
    pub flags: u8,
    pub count_op: u8,
    pub is_dynamic: bool,
    pub area_idx: u8,
}

impl DecodedSlot {
    pub fn decode(raw_s: i32) -> Self {
        let s = raw_s as u32 as u64;
        let source_zone_val = ((s >> 16) & 0x0F) as u8;
        let dest_zone_val = ((s >> 20) & 0x0F) as u8;
        let flags = ((s >> 24) & 0xFF) as u8;

        Self {
            target_slot: (s & 0xFF) as u8,
            source_zone: Self::decode_zone(source_zone_val),
            dest_zone: Self::decode_zone(dest_zone_val),
            flags,
            count_op: ((s >> 8) & 0xFF) as u8,
            is_dynamic: (s & 0x01000000) != 0, // Bit 24 is often the dynamic/opponent flag
            area_idx: ((s >> 28) & 0x0F) as u8,
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

    pub fn is_opponent(&self) -> bool {
        (self.flags & 0x01) != 0 // Bit 24 of raw_s
    }

    pub fn is_reveal_until_live(&self) -> bool {
        (self.flags & 0x02) != 0 // Bit 25 of raw_s
    }

    pub fn is_empty_slot_only(&self) -> bool {
        (self.flags & 0x04) != 0 // Bit 26 of raw_s
    }

    pub fn is_wait(&self) -> bool {
        (self.flags & 0x08) != 0 // Bit 27 of raw_s
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
