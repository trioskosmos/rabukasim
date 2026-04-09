pub fn env_flag_enabled(var: &str) -> bool {
    std::env::var(var)
        .ok()
        .map(|value| {
            let value = value.trim();
            !matches!(value, "0" | "false" | "FALSE" | "off" | "OFF")
        })
        .unwrap_or(false)
}

pub fn env_threshold_us(var: &str, default: u64) -> u64 {
    std::env::var(var)
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(default)
}
