# Future Redeemed unlock kit balance editor
This is a tool to edit the distribution of unlock kits in Xenoblade Chronicles 3: Future Redeemed.

## Usage guide
This tool includes two components:

* A mod to make unlock kits specific to each character.
* A Python script to generate item names, descriptions and locations for the new unlock kits.

The archive in the [Releases](https://github.com/RoccoDev/xc3fr-unlock-kit-balance/releases) tab includes the mod, the script, and some default configuration files.

1. Extract a Future Redeemed BDAT dump with [bdat-rs](https://github.com/RoccoDev/bdat-rs) in JSON format, making sure to pass a list of names to convert known hashes to plain text.
2. Edit the configuration file (`cfg/unlocks.toml`) with your preferred settings. I recommend leaving the item IDs untouched, as they were picked from unused entries. Adding new item rows isn't possible because the game has hardcoded limits.
3. Edit the unlock kit distribution (`cfg/locations.toml`) as you see fit. You can also manually use the new item IDs in the BDATs. If you don't want the tool to
generate locations for you, pass the `--no-locations` options to the Python script.
4. Edit or create the language file for your supported languages (`cfg/lang_*.toml`), which defines the name and caption text for each new unlock kit.
5. Run the script in the root directory: `python patch_bdat.py path/to/json`. The BDAT dump will now reflect changes from the unlock kit redistribution. If you need to make further changes, simply run the script again and the newly created rows will be updated with the new changes.
6. Repack the BDATs and include them with your mod, as well as the [file loader](https://github.com/RoccoDev/xc3-file-loader). Then, copy the `cfg/unlocks.toml` file to the RomFS root, and put the mod file in the `skyline/plugins` directory. The structure should now look like this:
```
romfs/
    unlocks.toml
    skyline/
        plugins/
            libxc3fr_unlock_kit_balance.nro
            libxc3_file_loader.nro
    bdat/
        ...
```

The script also supports the following options:

```
usage: patch_bdat.py [--no-locations] [--random-locations [SEED]] bdat_json_path

positional arguments:
  bdat_json_path

options:
  --no-locations        Do not edit item locations
  --random-locations [SEED]
                        Randomize unlock kit locations (omit SEED for default seed)
```

## License
This mod is distributed under the terms of the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html). See [COPYING](COPYING) for details.
