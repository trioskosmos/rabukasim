use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct HeartBoard(pub u64);

impl HeartBoard {
    pub const MASK: u64 = 0xFF; // 8 bits per color

    pub fn get_color_count(&self, color: usize) -> u8 {
        if color >= 7 { return 0; }
        ((self.0 >> (color * 8)) & Self::MASK) as u8
    }

    pub fn set_color_count(&mut self, color: usize, val: u8) {
        if color >= 7 { return; }
        let mask = Self::MASK << (color * 8);
        self.0 = (self.0 & !mask) | ((val as u64) << (color * 8));
    }

    pub fn add_to_color(&mut self, color: usize, val: i32) {
        if color >= 7 { return; }
        let current = self.get_color_count(color) as i32;
        self.set_color_count(color, (current + val).max(0).min(255) as u8);
    }

    pub fn add_heart(&mut self, color: usize) {
        self.add_to_color(color, 1);
    }

    pub fn get_total_count(&self) -> u32 {
        let mut total = 0;
        for i in 0..7 {
            total += self.get_color_count(i) as u32;
        }
        total
    }

    pub fn from_array(arr: &[u8; 7]) -> Self {
        let mut val = 0u64;
        for i in 0..7 {
            val |= (arr[i] as u64) << (i * 8);
        }
        Self(val)
    }

    pub fn to_array(&self) -> [u8; 7] {
        let mut arr = [0u8; 7];
        for i in 0..7 {
            arr[i] = ((self.0 >> (i * 8)) & Self::MASK) as u8;
        }
        arr
    }

    pub fn add(&mut self, other: Self) {
        // Simple addition per segment.
        // Note: This relies on segments not overflowing 255.
        // For safety, we can mask or use saturating logic, but for raw MCTS, speed is king.
        self.0 += other.0;
    }

    pub fn satisfies(&self, req: Self) -> bool {
        let mut pool = self.to_array();
        let need = req.to_array();

        let mut wildcards = pool[6] as i32;
        let mut satisfied = 0;
        let mut total_req = 0;

        for i in 0..6 {
            let n = need[i] as i32;
            let h = pool[i] as i32;
            total_req += n;
            if h >= n {
                satisfied += n;
                pool[i] -= n as u8;
            } else {
                satisfied += h;
                pool[i] = 0;
                let deficit = n - h;
                let used_wild = wildcards.min(deficit);
                satisfied += used_wild;
                wildcards -= used_wild;
            }
        }

        let mut any_need = need[6] as i32;
        total_req += any_need;
        let used_wild = wildcards.min(any_need);
        satisfied += used_wild;
        any_need -= used_wild;

        if any_need > 0 {
            for i in 0..6 {
                let used = (pool[i] as i32).min(any_need);
                satisfied += used;
                any_need -= used;
                if any_need <= 0 {
                    break;
                }
            }
        }

        satisfied >= total_req
    }
}

#[inline]
pub fn process_hearts(pool: &mut [u32; 7], need: &[u32; 7]) -> (u32, u32) {
    let mut p8 = [0u8; 7];
    let mut n8 = [0u8; 7];
    for i in 0..7 {
        p8[i] = pool[i].min(255) as u8;
        n8[i] = need[i].min(255) as u8;
    }

    let mut satisfied = 0;
    let mut wildcards = p8[6] as i32;
    let mut total_req = 0;

    for i in 0..6 {
        let n = n8[i] as i32;
        let h = p8[i] as i32;
        total_req += n;
        if h >= n {
            satisfied += n;
            p8[i] -= n as u8;
        } else {
            satisfied += h;
            p8[i] = 0;
            let deficit = n - h;
            let used_wild = wildcards.min(deficit);
            satisfied += used_wild;
            wildcards -= used_wild;
        }
    }

    let mut any_need = n8[6] as i32;
    total_req += any_need;
    let used_wild = wildcards.min(any_need);
    satisfied += used_wild;
    any_need -= used_wild;

    if any_need > 0 {
        for i in 0..6 {
            let used = (p8[i] as i32).min(any_need);
            satisfied += used;
            p8[i] -= used as u8;
            any_need -= used;
            if any_need <= 0 {
                break;
            }
        }
    }

    pool[6] = wildcards.max(0) as u32;
    for i in 0..6 {
        pool[i] = p8[i] as u32;
    }

    (satisfied as u32, total_req as u32)
}
