#!/usr/bin/sh
set -e

if ! type "cargo-skyline" > /dev/null; then
  cargo install --git https://github.com/jam1garner/cargo-skyline
fi

target="$(pwd)/target"
cargo_target=${CARGO_TARGET_DIR:-$target}

cargo +skyline skyline build --release
zip -r "$cargo_target/release.zip" patch_bdat.py cfg/
pushd  "$cargo_target/aarch64-skyline-switch/release/"
zip "$cargo_target/release.zip" libxc3fr_unlock_kit_balance.nro
popd