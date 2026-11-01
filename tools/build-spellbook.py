"""Build the spellbook data in bar-planner.html.

Spell lists per class and level come from the What's Training addon
(fusionpit/WhatsTraining, Classes/Vanilla). Names and icons come from
Wowhead's Classic tooltip API. Talents, stances, racials and professions
are listed by hand below and checked against the names Wowhead returns.
This is vanilla Classic data: Forever's class changes are not in it.

Run: python3 -I tools/build-spellbook.py bar-planner.html [cache.json]
The cache keeps tooltip lookups between runs.
"""
import concurrent.futures
import json
import pathlib
import re
import sys
import urllib.request

WT = "https://raw.githubusercontent.com/fusionpit/WhatsTraining/master/Classes/Vanilla/{}.lua"
TOOLTIP = "https://nether.wowhead.com/classic/tooltip/{}/{}"
CLASSES = ["Warrior", "Paladin", "Hunter", "Rogue", "Priest", "Shaman", "Mage", "Warlock", "Druid"]

# Active talent abilities (rank 1). Later ranks come from the trainer data.
TALENTS = {
    "WARRIOR": {"Sweeping Strikes": 12292, "Mortal Strike": 12294, "Piercing Howl": 12323, "Death Wish": 12328,
                "Bloodthirst": 23881, "Last Stand": 12975, "Concussion Blow": 12809, "Shield Slam": 23922},
    "PALADIN": {"Divine Favor": 20216, "Holy Shock": 20473, "Blessing of Kings": 20217, "Seal of Command": 20375,
                "Repentance": 20066, "Blessing of Sanctuary": 20911, "Holy Shield": 20925, "Consecration": 26573},
    "HUNTER": {"Aimed Shot": 19434, "Scatter Shot": 19503, "Trueshot Aura": 19506, "Intimidation": 19577,
               "Bestial Wrath": 19574, "Counterattack": 19306, "Deterrence": 19263, "Wyvern Sting": 19386},
    "ROGUE": {"Ghostly Strike": 14278, "Riposte": 14251, "Blade Flurry": 13877, "Adrenaline Rush": 13750,
              "Cold Blood": 14177, "Preparation": 14185, "Premeditation": 14183, "Hemorrhage": 16511},
    "PRIEST": {"Inner Focus": 14751, "Power Infusion": 10060, "Holy Nova": 15237, "Lightwell": 724,
               "Mind Flay": 15407, "Silence": 15487, "Vampiric Embrace": 15286, "Shadowform": 15473,
               "Divine Spirit": 14752},
    "SHAMAN": {"Elemental Mastery": 16166, "Nature's Swiftness": 16188, "Mana Tide Totem": 16190, "Stormstrike": 17364},
    "MAGE": {"Presence of Mind": 12043, "Arcane Power": 12042, "Pyroblast": 11366, "Blast Wave": 11113,
             "Combustion": 11129, "Cold Snap": 12472, "Ice Block": 11958, "Ice Barrier": 11426},
    "WARLOCK": {"Amplify Curse": 18288, "Curse of Exhaustion": 18223, "Siphon Life": 18265, "Dark Pact": 18220,
                "Fel Domination": 18708, "Demonic Sacrifice": 18788, "Soul Link": 19028, "Shadowburn": 17877,
                "Conflagrate": 17962},
    "DRUID": {"Insect Swarm": 5570, "Nature's Grasp": 16689, "Moonkin Form": 24858, "Feral Charge": 16979,
              "Faerie Fire (Feral)": 16857, "Nature's Swiftness": 17116, "Swiftmend": 18562},
}

# Stance bar per class, in stance bar order. page = first slot of the main bar while in it (None = no own page).
STANCES = {
    "WARRIOR": [("Battle Stance", 2457, 73), ("Defensive Stance", 71, 85), ("Berserker Stance", 2458, 97)],
    "DRUID": [("Bear Form", 5487, 97), ("Aquatic Form", 1066, None), ("Cat Form", 768, 73),
              ("Travel Form", 783, None), ("Moonkin Form", 24858, 109)],
    "ROGUE": [("Stealth", 1784, 73)],
    "PRIEST": [("Shadowform", 15473, 73)],
}

# Passives and pet training that What's Training lists but can't go on a bar.
SKIP = {"Reincarnation", "Mail", "Plate Mail", "Parry", "Dual Wield", "Great Stamina", "Natural Armor",
        "Arcane Resistance", "Fire Resistance", "Frost Resistance", "Nature Resistance", "Shadow Resistance",
        "Growl", "Feline Grace", "Detect Traps"}

# Spells learned from class quests or with another spell, missing from the trainer lists: name -> (id, level)
EXTRA = {
    "HUNTER": {"Auto Shot": (75, 1), "Call Pet": (883, 10), "Dismiss Pet": (2641, 10), "Revive Pet": (982, 10),
               "Feed Pet": (6991, 10)},
    "WARLOCK": {"Summon Imp": (688, 1), "Summon Voidwalker": (697, 10), "Summon Succubus": (712, 20),
                "Summon Felhunter": (691, 30), "Summon Felsteed": (5784, 40), "Inferno": (1122, 50),
                "Summon Dreadsteed": (23161, 60)},
    "PALADIN": {"Summon Warhorse": (13819, 40), "Summon Charger": (23214, 60)},
}

# Level of rank 1 where the trainer data gets it wrong (quest-learned spells): name -> level
LEVELS = {
    "WARRIOR": {"Defensive Stance": 10, "Berserker Stance": 30, "Intercept": 30, "Sunder Armor": 10},
    "SHAMAN": {"Stoneskin Totem": 4, "Searing Totem": 10, "Healing Stream Totem": 20},
    "DRUID": {"Bear Form": 10, "Maul": 10, "Aquatic Form": 16},
    "HUNTER": {"Tame Beast": 10},
    "PALADIN": {"Blessing of Might": 4, "Blessing of Wisdom": 14},
    "ROGUE": {"Instant Poison": 20, "Deadly Poison V": 60},
}

# Wowhead race ids used by What's Training: 1 Human, 2 Orc, 3 Dwarf, 4 Night Elf, 5 Undead, 6 Tauren, 7 Gnome, 8 Troll
RACE_NAMES = {1: "Human", 2: "Orc", 3: "Dwarf", 4: "Night Elf", 5: "Undead", 6: "Tauren", 7: "Gnome", 8: "Troll"}
GENERAL = [  # (name, id, races or None, classes or None)
    ("Attack", 6603, None, None),
    ("Shoot", 5019, None, ["PRIEST", "MAGE", "WARLOCK"]),
    ("Stoneform", 20594, ["Dwarf"], None), ("Find Treasure", 2481, ["Dwarf"], None),
    ("Escape Artist", 20589, ["Gnome"], None), ("Perception", 20600, ["Human"], None),
    ("Shadowmeld", 20580, ["Night Elf"], None), ("Blood Fury", 20572, ["Orc"], None),
    ("War Stomp", 20549, ["Tauren"], None), ("Berserking", 20554, ["Troll"], None),
    ("Will of the Forsaken", 7744, ["Undead"], None), ("Cannibalize", 20577, ["Undead"], None),
    ("First Aid", 3273, None, None), ("Cooking", 2550, None, None), ("Fishing", 7620, None, None),
    ("Find Minerals", 2580, None, None), ("Find Herbs", 2383, None, None), ("Smelting", 2656, None, None),
    ("Disenchant", 13262, None, None), ("Basic Campfire", 818, None, None),
]
ITEMS = [("Hearthstone", 6948)]
# Wowhead shows a placeholder icon for these; use what the game shows instead.
ICON_OVERRIDE = {"Attack": "inv_sword_04"}

TOKENS = re.compile(
    r"\[(?P<level>\d+)\]\s*=|\bid\s*=\s*(?P<id>\d+)|\braces?\s*=\s*(?P<races>\{[^}]*\}|\d+)"
    r"|local\s+(?P<arr>\w+)\s*=\s*\{(?P<arrbody>[^}]*)\}|requiredIds\s*=\s*(?P<req>\{[^}]*\}|\w+)")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (bar-planner build script)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse_class(text):
    """Returns (entries, rank arrays, required ids). entry = {id, level, races}."""
    entries, arrays, required = [], [], set()
    level = None
    for m in TOKENS.finditer(text):
        if m["level"]:
            level = int(m["level"])
        elif m["id"]:
            entries.append({"id": int(m["id"]), "level": level, "races": None})
        elif m["races"] and entries:
            entries[-1]["races"] = [int(x) for x in re.findall(r"\d+", m["races"])]
        elif m["arr"]:
            ids = [int(x) for x in re.findall(r"\b\d{2,}\b", re.sub(r"--\[\[.*?\]\]", "", m["arrbody"]))]
            if ids:
                arrays.append(ids)
        elif m["req"]:
            required.update(int(x) for x in re.findall(r"\d+", m["req"]))
    return entries, arrays, required


def tooltips(keys, cache):
    todo = [k for k in keys if k not in cache]

    def fetch(k):
        kind, num = k.split(":")
        try:
            d = json.loads(get(TOOLTIP.format(kind, num)))
            return k, {"name": d.get("name"), "icon": d.get("icon"), "passive": ">Passive<" in (d.get("tooltip") or "")}
        except Exception as e:  # noqa: BLE001 - report and skip
            print("tooltip failed", k, e, file=sys.stderr)
            return k, None

    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        for k, v in pool.map(fetch, todo):
            if v:
                cache[k] = v
    return cache


def main(html_path, cache_path=None):
    cache_file = pathlib.Path(cache_path) if cache_path else None
    cache = json.loads(cache_file.read_text()) if cache_file and cache_file.exists() else {}

    parsed = {}
    for cls in CLASSES:
        parsed[cls.upper()] = parse_class(get(WT.format(cls)))

    keys = {f"spell:{e['id']}" for es, arrs, req in parsed.values() for e in es}
    keys |= {f"spell:{i}" for es, arrs, req in parsed.values() for a in arrs for i in a}
    keys |= {f"spell:{i}" for es, arrs, req in parsed.values() for i in req}
    keys |= {f"spell:{i}" for t in TALENTS.values() for i in t.values()}
    keys |= {f"spell:{s[1]}" for st in STANCES.values() for s in st}
    keys |= {f"spell:{v[0]}" for ex in EXTRA.values() for v in ex.values()}
    keys |= {f"spell:{g[1]}" for g in GENERAL}
    keys |= {f"item:{i[1]}" for i in ITEMS}
    tooltips(sorted(keys), cache)
    if cache_file:
        cache_file.write_text(json.dumps(cache, indent=0, sort_keys=True))

    def tip(kind, i):
        return cache.get(f"{kind}:{i}")

    def check(name, i, kind="spell"):
        t = tip(kind, i)
        if not t or t["name"] != name:
            print(f"name mismatch {kind} {i}: expected {name!r}, Wowhead has {t and t['name']!r}", file=sys.stderr)
            return None
        return t

    data = {"classes": {}, "general": [], "items": [], "stances": {}}
    for cls, (entries, arrays, required) in parsed.items():
        talents = {n: i for n, i in TALENTS[cls].items() if check(n, i)}
        talent_ids = set(talents.values())
        level_of = {}
        races_of = {}
        for e in entries:
            if e["id"] not in level_of or (e["level"] or 99) < (level_of[e["id"]] or 99):
                level_of[e["id"]] = e["level"]
            if e["races"]:
                races_of[e["id"]] = [RACE_NAMES[r] for r in e["races"] if r in RACE_NAMES]
        ids = set(level_of) | set(required) | {i for a in arrays for i in a} | talent_ids
        ids |= {s[1] for s in STANCES.get(cls, [])}
        for name, (i, lvl) in EXTRA.get(cls, {}).items():
            if check(name, i):
                ids.add(i)
                level_of[i] = lvl
        by_name = {}
        for i in ids:
            t = tip("spell", i)
            if not t or t["passive"] or not t["name"] or t["name"] in SKIP:
                continue
            by_name.setdefault(t["name"], {"icon": t["icon"], "ids": set()})["ids"].add(i)
        spells = []
        for name, info in by_name.items():
            talent = name in talents
            # rank order: a rank array from the file if one covers these ids, else by level
            order = next((a for a in arrays if info["ids"] & set(a)), None)
            if order:
                ranked = [i for i in order if i in info["ids"]] + sorted(info["ids"] - set(order))
            else:
                ranked = sorted(info["ids"], key=lambda i: (level_of.get(i) or (0 if i not in talent_ids else -1), i))
            ranks = []
            for i in ranked:
                lvl = level_of.get(i)
                if lvl is None:
                    lvl = 0 if (talent and i == talents[name]) else 1  # 0 = from a talent
                ranks.append([i, lvl])
            if talent and ranks[0][0] != talents[name]:
                ranks.sort(key=lambda r: (r[0] != talents[name], r[1]))
            if name in LEVELS.get(cls, {}):
                ranks[0][1] = LEVELS[cls][name]
            item = {"n": name, "i": info["icon"], "r": ranks}
            if talent:
                item["t"] = 1
            races = {r for i in info["ids"] for r in races_of.get(i, [])}
            if races and all(i in races_of for i in info["ids"]):
                item["race"] = sorted(races)
            spells.append(item)
        spells.sort(key=lambda s: (s.get("t", 0), s["r"][0][1], s["n"]))
        data["classes"][cls] = spells
        if cls in STANCES:
            data["stances"][cls] = [{"n": n, "i": tip("spell", i)["icon"], "page": p} for n, i, p in STANCES[cls] if check(n, i)]

    for name, i, races, classes in GENERAL:
        t = check(name, i)
        if t:
            g = {"n": name, "i": ICON_OVERRIDE.get(name, t["icon"])}
            if races:
                g["race"] = races
            if classes:
                g["cls"] = classes
            data["general"].append(g)
    for name, i in ITEMS:
        t = check(name, i, "item")
        if t:
            data["items"].append({"n": name, "i": t["icon"], "id": i})

    html_path = pathlib.Path(html_path)
    html = html_path.read_text(encoding="utf-8")
    start, end = "/* spellbook-data:start */", "/* spellbook-data:end */"
    block = f"{start}\nconst SPELLBOOK = {json.dumps(data, separators=(',', ':'))};\n{end}"
    if start not in html:
        sys.exit("spellbook-data markers not found in " + str(html_path))
    html = re.sub(re.escape(start) + ".*?" + re.escape(end), lambda _: block, html, flags=re.S)
    html_path.write_text(html, encoding="utf-8")
    for cls, spells in data["classes"].items():
        print(f"{cls:8} {len(spells):3} spells, {sum(1 for s in spells if s.get('t'))} talents")


if __name__ == "__main__":
    main(*sys.argv[1:])
