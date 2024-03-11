use std::arch::asm;

use skyline::{hook, hooks::InlineCtx, patching};

use crate::{
    config::{Config, ItemType},
    get_config,
};

static mut CUR_CHARACTER_PTR: u64 = 0;
static mut ARTS_MODE: ArtsMode = ArtsMode::Regular;

enum ArtsMode {
    Regular,
    Callback,
}

pub fn install_hooks() {
    if !get_config().header.per_character_items {
        return;
    }

    skyline::install_hooks!(
        get_item_slot,
        get_item_slot2,
        get_item_count,
        patch_intermediary,
        mnu_patch_art_interm,
        item_confirm_dialog,
        pickup_cmp,
        pickup_type
    );

    unsafe {
        patching::patch_data(0x008d2980, &0xD2824690_u32).unwrap(); // mov x16, #0x1234
        patching::patch_data(0x008d2984, &0x1400000D_u32).unwrap(); // b 56
    }
}

#[hook(offset = 0x002ebbe0, inline)]
unsafe fn get_item_slot(ctx: &mut InlineCtx) {
    patch_register(ctx, 1)
}

#[hook(offset = 0x0059db18, inline)]
unsafe fn get_item_slot2(ctx: &mut InlineCtx) {
    patch_register(ctx, 1)
}

#[hook(offset = 0x002eb668, inline)]
unsafe fn get_item_count(ctx: &mut InlineCtx) {
    patch_register(ctx, 1)
}

#[hook(offset = 0x00527144, inline)]
unsafe fn item_confirm_dialog(ctx: &mut InlineCtx) {
    patch_register(ctx, 8)
}

#[hook(offset = 0x009f1b70, inline)]
unsafe fn pickup_cmp(ctx: &mut InlineCtx) {
    let item_id = *ctx.registers[21].w.as_ref();
    if get_config().get_item_type(item_id + 1).is_some() {
        *ctx.registers[0].w.as_mut() = item_id;
    }
}

#[hook(offset = 0x009f1b90, inline)]
unsafe fn pickup_type(ctx: &mut InlineCtx) {
    let item_id = *ctx.registers[21].w.as_ref() + 1;
    let announce_id = ctx.registers[8].w.as_mut();
    match get_config().get_item_type(item_id) {
        Some(ItemType::Gem) => *announce_id = 0x1d,
        Some(ItemType::Accessory) => *announce_id = 0x1c,
        Some(ItemType::Art) => *announce_id = 0x1b,
        Some(ItemType::Affinity) => *announce_id = 0x1a,
        None => {}
    }
}

#[hook(offset = 0x008d29b8)]
unsafe fn patch_intermediary(p1: u64, p2: u64) -> u64 {
    // IPC register is used to pass a sentinel around
    let mut magic: u64;
    asm!(
        "mov {magic}, x16",
        magic = out(reg) magic,
    );

    if magic == 0x1234 {
        // This is actually the other function
        CUR_CHARACTER_PTR = p1;

        let ret: u64;
        asm!(
            // Unset sentinel
            "mov x16, #0x0",
            // Original function:
            "ldr x8, [x0, #0x10]",
            "ldr {ret}, [x8, #0x8]",
            ret = out(reg) ret
        );

        return ret;
    }

    call_original!(p1, p2);
    // The original doesn't actually return, restore x0
    p1
}

#[hook(offset = 0x00787398, inline)]
unsafe fn mnu_patch_art_interm(ctx: &mut InlineCtx) {
    CUR_CHARACTER_PTR = *ctx.registers[21].x.as_ref();
    ARTS_MODE = ArtsMode::Callback;
}

unsafe fn patch_register(ctx: &mut InlineCtx, register: usize) {
    let item = match *ctx.registers[register].w.as_ref() {
        16134 => get_art_id(),
        16135 => patch(get_chr_id(0x3428), Config::get_accessory_id),
        16136 => patch(get_chr_id(0x2210), Config::get_gem_id),
        16137 => patch(get_chr_id(0x1c0), Config::get_affinity_id),
        _ => None,
    };
    if let Some(item) = item {
        *ctx.registers[register].w.as_mut() = item;
    }
}

unsafe fn get_art_id() -> Option<u32> {
    let chr_id = match ARTS_MODE {
        ArtsMode::Regular => get_chr_id(0x6368),
        ArtsMode::Callback => get_chr_id(0x90),
    };
    ARTS_MODE = ArtsMode::Regular;
    patch(chr_id, Config::get_art_id)
}

fn patch(chr_id: u32, extract: impl Fn(&Config, u32) -> Option<u32>) -> Option<u32> {
    if chr_id == 0 {
        if cfg!(feature = "debug-invalid-chr") {
            panic!("Invalid current character, function not covered by hooks?");
        } else {
            return None;
        }
    }
    let new = extract(get_config(), chr_id);
    new.and_then(|v| (v != 0).then_some(v))
}

unsafe fn get_chr_id(offset: usize) -> u32 {
    let ptr = CUR_CHARACTER_PTR as *const u8;
    let ptr = ptr.add(offset) as *const u32;
    *ptr
}
