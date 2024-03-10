use std::sync::OnceLock;

use crate::config::Config;

mod config;
mod hooks;

static CONFIG: OnceLock<Config> = OnceLock::new();

#[skyline::main(name = "xc3fr_unlock_balance")]
pub fn main() {
    println!("[XC3FR-UK] Loading...");

    let config = std::fs::read_to_string("rom:/unlocks.toml")
        .map(|f| {
            if cfg!(debug_assertions) {
                toml::de::from_str(&f).unwrap()
            } else {
                toml::de::from_str(&f).unwrap_or_default()
            }
        })
        .unwrap_or_default();
    CONFIG.set(config).unwrap();

    #[cfg(debug_assertions)]
    println!("Loaded config {:#?}", get_config());

    println!("[XC3FR-UK] Installing hooks");
    hooks::install_hooks();

    println!("[XC3FR-UK] Loaded!");
}

pub fn get_config() -> &'static Config {
    CONFIG.get().unwrap()
}
