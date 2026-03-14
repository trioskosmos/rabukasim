fn main() {
    let a: u64 = 1688849866162176;
    println!("A: 0x{:X}", a);
    println!("target_player: {}", (a >> 0) & 0x3);
    println!("card_type: {}", (a >> 2) & 0x3);
    println!("group_enabled: {}", (a >> 4) & 0x1);
    println!("group_id: {}", (a >> 5) & 0x7F);
    println!("unit_enabled: {}", (a >> 16) & 0x1);
    println!("unit_id: {}", (a >> 17) & 0x7F);
    println!("char_id_1: {}", (a >> 39) & 0x7F);
    println!("char_id_2: {}", (a >> 46) & 0x7F);
    println!("special_id: {}", (a >> 56) & 0x7);

    // Let's print bit 39-45 and 46-52 specifically
    println!("Bits 39-45: {}", (a >> 39) & 0x7F);
    println!("Bits 46-52: {}", (a >> 46) & 0x7F);
}
