use serde::Deserialize;

#[derive(Debug, Deserialize, Default)]
pub struct Config {
    #[serde(rename = "config")]
    pub header: ConfigHeader,
    pub item: ItemConfig<u32>,
}

#[derive(Debug, Deserialize, Default)]
#[serde(rename_all = "kebab-case")]
pub struct ConfigHeader {
    pub per_character_items: bool,
}

#[derive(Debug, Deserialize, Default)]
pub struct ItemConfig<T> {
    gem: CharacterConfig<T>,
    art: CharacterConfig<T>,
    accessory: CharacterConfig<T>,
    affinity: CharacterConfig<T>,
}

#[derive(Debug, Deserialize, Default)]
pub struct CharacterConfig<T> {
    pub matthew: T,
    pub a: T,
    pub nikol: T,
    pub glimmer: T,
    pub shulk: T,
    pub rex: T,
    pub nael: T,
}

pub enum ItemType {
    Gem,
    Art,
    Accessory,
    Affinity,
}

impl Config {
    pub fn get_gem_id(&self, character_id: u32) -> Option<u32> {
        self.header
            .per_character_items
            .then(|| self.item.gem.get(character_id))
    }

    pub fn get_art_id(&self, character_id: u32) -> Option<u32> {
        self.header
            .per_character_items
            .then(|| self.item.art.get(character_id))
    }

    pub fn get_accessory_id(&self, character_id: u32) -> Option<u32> {
        self.header
            .per_character_items
            .then(|| self.item.accessory.get(character_id))
    }

    pub fn get_affinity_id(&self, character_id: u32) -> Option<u32> {
        self.header
            .per_character_items
            .then(|| self.item.affinity.get(character_id))
    }

    pub fn get_item_type(&self, item_id: u32) -> Option<ItemType> {
        if self.item.gem.contains(item_id) {
            return Some(ItemType::Gem);
        }
        if self.item.art.contains(item_id) {
            return Some(ItemType::Art);
        }
        if self.item.accessory.contains(item_id) {
            return Some(ItemType::Accessory);
        }
        if self.item.affinity.contains(item_id) {
            return Some(ItemType::Affinity);
        }
        None
    }
}

impl<T> CharacterConfig<T>
where
    T: Copy,
{
    pub fn get(&self, character_id: u32) -> T {
        let id = if character_id > 35 {
            character_id - 35
        } else {
            character_id
        };
        match id {
            1 => self.matthew,
            2 => self.a,
            3 => self.nikol,
            4 => self.glimmer,
            5 => self.shulk,
            6 => self.rex,
            7 => self.nael,
            _ => panic!("unknown character id {character_id}"),
        }
    }

    pub fn contains(&self, id: T) -> bool
    where
        T: PartialEq,
    {
        self.matthew == id
            || self.a == id
            || self.nikol == id
            || self.glimmer == id
            || self.shulk == id
            || self.rex == id
            || self.nael == id
    }
}
