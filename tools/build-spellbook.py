"""Build the spellbook data in index.html from WoW Forever's own data.

Sources:
- wowforevertalents.com, which reads the Forever client (build 1.60.1.70707) and the
  server's hotfixes: the trainer spells per class with each rank's level (/abilities/<class>/),
  the talent trees (/<class>/) and the racials (/racials/). Spells the trainer no longer
  teaches and passives are left out, the way the site marks them. The site's talent calculator
  script gives each talent rank's spell ID, including the talents only the hotfixes add.
- The Forever client's tables via wago.tools (SpellName, Spell, SpellMisc, SkillLineAbility,
  Talent, TalentTab): spell IDs for each rank (for Wowhead tooltips) and which talents are passive.
  A talent is active when the client says its spell isn't passive. Only for spells the client
  tables don't have does the site's cost line decide (passives have none). The cost line alone
  isn't enough: Water Shield costs nothing and has no cooldown, so it has no cost line.

Run: python3 -I tools/build-spellbook.py index.html [cache-dir]
The cache dir keeps the downloaded pages and tables; delete it to fetch fresh data.
"""
import collections
import csv
import html as htmllib
import io
import json
import pathlib
import re
import sys
import time
import urllib.request

SITE = "https://wowforevertalents.com"
BUILD = "1.60.1.70707"
WAGO = "https://wago.tools/db2/{}/csv?build=" + BUILD
USER_AGENT = "barplanner-build/1.0 (+https://github.com/rubensayshi/wowforever-barplanner)"

CLASSES = ["WARRIOR", "PALADIN", "HUNTER", "ROGUE", "PRIEST", "SHAMAN", "MAGE", "WARLOCK", "DRUID"]
CLASS_ID = {"WARRIOR": 1, "PALADIN": 2, "HUNTER": 3, "ROGUE": 4, "PRIEST": 5, "SHAMAN": 7, "MAGE": 8, "WARLOCK": 9, "DRUID": 11}
CLASS_BIT = {c: 1 << (i - 1) for c, i in CLASS_ID.items()}
RACES = ["Human", "Dwarf", "Night Elf", "Gnome", "Orc", "Undead", "Tauren", "Troll", "Skyborne"]
# Bits in the client's 64-bit race masks (ChrRaces.PlayableRaceBit). Skyborne are two races, one per faction.
RACE_BITS = {"Human": [0], "Orc": [1], "Dwarf": [2], "Night Elf": [3], "Undead": [4], "Tauren": [5], "Gnome": [6], "Troll": [7],
             "Skyborne": [32, 33]}
ALL_RACES = (1 << 64) - 1
# Skyborne mages are always High Order (Alliance), Skyborne shamans always Windshaper (Horde).
SKYBORNE_BITS = {"MAGE": [32], "SHAMAN": [33]}
# Race sections on /racials/; both Skyborne factions are one race in the planner.
RACIAL_HEADINGS = {r: r for r in RACES} | {"High Order Skyborne": "Skyborne", "Windshaper Skyborne": "Skyborne"}
# Racials without a cooldown that still go on a bar.
RACIAL_TOGGLES = {"Find Treasure"}

# Stance bar per class, in stance bar order. page = first slot of the main bar while in it (None = no own page).
# Pages follow the client's SpellShapeshiftForm.BonusActionBar for this build (page = 73 + 12 * (bar - 1)):
# Cat 1, Bear 3, Battle 1, Defensive 2, Berserker 3, Stealth 1. Moonkin Form and Shadowform are 0, so unlike
# retail they keep the normal main bar. Prowl has no form of its own, so it stays on the Cat Form page.
STANCES = {
    "WARRIOR": [("Battle Stance", 73), ("Defensive Stance", 85), ("Berserker Stance", 97)],
    "DRUID": [("Bear Form", 97), ("Aquatic Form", None), ("Cat Form", 73), ("Travel Form", None), ("Moonkin Form", None)],
    "ROGUE": [("Stealth", 73)],
    "PRIEST": [("Shadowform", None)],
}

# Spells every class has, and professions. (name, classes or None)
GENERAL = [
    ("Attack", None), ("Shoot", ["PRIEST", "MAGE", "WARLOCK"]), ("Throw", ["WARRIOR", "ROGUE", "HUNTER"]),
    ("Shoot Bow", ["WARRIOR", "ROGUE"]), ("Shoot Gun", ["WARRIOR", "ROGUE"]), ("Shoot Crossbow", ["WARRIOR", "ROGUE"]),
    ("First Aid", None), ("Cooking", None), ("Fishing", None), ("Find Minerals", None), ("Find Herbs", None),
    ("Smelting", None), ("Disenchant", None), ("Basic Campfire", None),
]
GENERAL_ICONS = {"Attack": "inv_sword_04", "Shoot": "ability_shootwand", "Throw": "ability_throw", "Shoot Bow": "ability_marksmanship",
                 "Shoot Gun": "inv_weapon_rifle_01", "Shoot Crossbow": "inv_weapon_crossbow_01", "First Aid": "spell_holy_sealofsacrifice",
                 "Cooking": "inv_misc_food_15", "Fishing": "trade_fishing", "Find Minerals": "spell_nature_earthquake",
                 "Find Herbs": "inv_misc_flower_02", "Smelting": "spell_fire_flameblades", "Disenchant": "inv_enchant_disenchant",
                 "Basic Campfire": "spell_fire_fire"}
ITEMS = [("Hearthstone", 6948, "inv_misc_rune_01")]


def fetch(url, cache, name):
    path = cache / name
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=120) as r:
            path.write_bytes(r.read())
        time.sleep(1)
    return path.read_text(encoding="utf-8")


def table(name, cache):
    return list(csv.DictReader(io.StringIO(fetch(WAGO.format(name), cache, name + ".csv"))))


def clean(h):
    return re.sub(r" data-astro-cid-\w+", "", h)


def abilities(h):
    """Trainer spells on an /abilities/<class>/ page: (status, data, icon)."""
    pat = (r'<li class="cell status-(\w+)"[^>]*>\s*<button type="button" class="cell-btn"[^>]*data-tip="([^"]*)"[^>]*>'
           r'\s*<img src="[^"]*/icons/\w+/([^".]+)\.jpg"')
    return [(st, json.loads(htmllib.unescape(t)), icon) for st, t, icon in re.findall(pat, clean(h))]


def text(h):
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def talents(h):
    """Talents in the reference list on a /<class>/ page: (name, icon, points needed, cost line or None, text).
    Active talents have a cost line (mana, cast time, cooldown); passives don't."""
    out = []
    for b in re.findall(r'<li class="tref[^"]*"[^>]*>(.*?)</li>', clean(h), flags=re.S):
        name = re.search(r'<h4>\s*<a [^>]*>([^<]+)</a>', b)
        icon = re.search(r'/icons/\w+/([^".]+)\.jpg', b)
        points = re.search(r'<span class="tag">(\d+) points?</span>', b)
        cost = re.search(r'<p class="tref-cost">(.*?)</p>', b, flags=re.S)
        rank = re.findall(r'<p class="tref-rank">(.*?)</p>', b, flags=re.S)
        if name and icon:
            out.append((htmllib.unescape(name.group(1)).strip(), icon.group(1), int(points.group(1)) if points else 0,
                        text(cost.group(1)) if cost else None, text(re.sub(r'<span class="tref-rank-n">.*?</span>', "", rank[-1])) if rank else ""))
    return out


def talent_spell_ids(cache):
    """Spell ID per rank of every talent, from the site's talent calculator: {class: {name: [ids]}}.
    The client's Talent table lacks the talents Forever added in hotfixes (Water Shield, Riptide, ...)."""
    page = fetch(f"{SITE}/warrior/", cache, "talents-warrior.html")
    entry = re.search(r'component-url="/_astro/(TalentCalculator\.[^"]+\.js)"', page).group(1)
    out = {}
    for js in [entry] + re.findall(r'from"\./([^"]+\.js)"', fetch(f"{SITE}/_astro/{entry}", cache, entry)):
        s = fetch(f"{SITE}/_astro/{js}", cache, js)
        for m in re.finditer(r'\{"id":\d+,"slug":"\w+","name":"\w+","color":"#\w+","icon":"class_\w+","trees":', s):
            c = json.JSONDecoder().raw_decode(s, m.start())[0]
            out[c["slug"].upper()] = {t["name"]: [r.get("spellId", 0) for r in t["ranks"]] for tree in c["trees"] for t in tree["talents"]}
    if set(CLASSES) - set(out):
        sys.exit(f"talent calculator data not found for {sorted(set(CLASSES) - set(out))} (site layout changed?)")
    return out


def racials(h):
    """Active racials per race on /racials/: {race: [(name, icon, cooldown line, text)]}. Passives have no cooldown."""
    parts = re.split(r"<h([1-4])[^>]*>([^<]{2,40})</h\1>", clean(h))
    out = {}
    for i in range(1, len(parts) - 2, 3):
        race = RACIAL_HEADINGS.get(parts[i + 1].strip())
        if not race:
            continue
        for a in re.findall(r'<li class="ability">(.*?)</li>', parts[i + 2], flags=re.S):
            name = htmllib.unescape(re.search(r'<div class="ability-name">\s*([^<]+?)\s*<', a).group(1))
            icon = re.search(r'/icons/\w+/([^".]+)\.jpg', a).group(1)
            meta = re.search(r'<div class="ability-meta">([^<]*)</div>', a)
            desc = re.search(r'<div class="ability-text">(.*?)</div>', a, flags=re.S)
            if meta or name in RACIAL_TOGGLES:
                out.setdefault(race, []).append((name, icon, text(meta.group(1)) if meta else "", text(desc.group(1)) if desc else ""))
    return out


def main(html_path, cache_dir=".spellbook-cache"):
    cache = pathlib.Path(cache_dir)
    cache.mkdir(exist_ok=True)

    names = {int(r["ID"]): r["Name_lang"] for r in table("SpellName", cache)}
    subtext = {int(r["ID"]): r["NameSubtext_lang"] for r in table("Spell", cache)}
    passive = {int(r["SpellID"]): bool(int(r["Attributes_0"]) & 0x40) for r in table("SpellMisc", cache)}
    class_mask = collections.defaultdict(int)
    race_mask = collections.defaultdict(int)  # spell -> races that learn it (all rows together); 0 or all bits = everyone
    for r in table("SkillLineAbility", cache):
        i = int(r["Spell"])
        class_mask[i] |= int(r["ClassMask"]) or 0
        m = (int(r["RaceMasks_0"] or 0) & 0xFFFFFFFF) | ((int(r["RaceMasks_1"] or 0) & 0xFFFFFFFF) << 32)
        race_mask[i] |= m or ALL_RACES
    taught = set(class_mask)
    tab_class = {int(r["ID"]): int(r["ClassMask"]) for r in table("TalentTab", cache)}
    talent_rows = collections.defaultdict(dict)  # class bit -> name -> [rank spell ids]; Talent.ClassID is empty, the tree has the class
    for r in table("Talent", cache):
        ranks = [int(r[f"SpellRank_{i}"]) for i in range(9) if int(r[f"SpellRank_{i}"] or 0)]
        if ranks:
            talent_rows[tab_class.get(int(r["TabID"]), 0)][names.get(ranks[0], "")] = ranks
    site_talents = talent_spell_ids(cache)
    by_name = collections.defaultdict(list)
    for i, n in names.items():
        by_name[n].append(i)

    def spell_id(name, rank, cls=None, single=False, race=None):
        """The client spell ID for a spell name and rank label ('Rank 3' or ''). With race: the one that race learns."""
        ids = by_name.get(name, [])
        want = [i for i in ids if subtext.get(i, "") == rank] or (list(ids) if single else [])  # racials say "Racial", not a rank
        if race:
            bits = sum(1 << b for b in RACE_BITS[race])
            mine = [i for i in want if race_mask.get(i, 0) & bits and race_mask.get(i) != ALL_RACES]
            want = mine or want
        if cls:
            mine = [i for i in want if class_mask.get(i, 0) & CLASS_BIT[cls]]
            want = mine or [i for i in want if i in taught] or want
        else:
            want = [i for i in want if i in taught] or want
        return min(want) if want else 0

    data = {"classes": {}, "general": [], "items": [], "stances": {}}
    missing = []
    for cls in CLASSES:
        spells, seen = [], set()
        for status, d, icon in abilities(fetch(f"{SITE}/abilities/{cls.lower()}/", cache, f"abilities-{cls.lower()}.html")):
            if status == "removed" or d["p"] or d["n"] in seen:
                continue
            seen.add(d["n"])
            ranks, texts = [], []
            if d.get("tr"):  # rank 1 comes from a talent, later ranks from the trainer
                tr = d["tr"]
                ranks.append([(site_talents[cls].get(d["n"]) or [0])[0] or spell_id(d["n"], tr["r"], cls), tr["l"], 1])
                texts.append([tr.get("m", ""), tr.get("d", "")])
            for k in d["k"]:
                ranks.append([spell_id(d["n"], k["r"], cls, single=len(d["k"]) == 1), k["l"]])
                texts.append([k.get("m", ""), k.get("d", "")])
            missing += [f"{cls} {d['n']} {r[1]}" for r in ranks if not r[0]]
            item = {"n": d["n"], "i": icon, "r": ranks}
            # Ranks the client tables don't have (renamed or newer): no Wowhead tooltip, so keep the site's text.
            tt = {str(j): texts[j] for j, r in enumerate(ranks) if not r[0]}
            if tt:
                item["tt"] = tt
            mask = 0
            for r in ranks:
                mask |= race_mask.get(r[0], ALL_RACES)
            bits_for = dict(RACE_BITS, Skyborne=SKYBORNE_BITS.get(cls, RACE_BITS["Skyborne"]))
            races = [n for n, bits in bits_for.items() if any(mask >> b & 1 for b in bits)]
            if races and len(races) < len(RACE_BITS):
                item["race"] = sorted(races, key=RACES.index)
            if d.get("tr"):
                item["t"] = 1
            if status == "new":
                item["new"] = 1
            spells.append(item)

        # Active talents that the trainer doesn't teach (Elemental Mastery, Moonkin Form, ...).
        rows = talent_rows[CLASS_BIT[cls]]
        for n, icon, points, cost, desc in talents(fetch(f"{SITE}/{cls.lower()}/", cache, f"talents-{cls.lower()}.html")):
            if n in seen:  # already listed with its trainer ranks
                continue
            ids = site_talents[cls].get(n) or [0]
            if not all(ids):
                ids = rows.get(n) or [spell_id(n, "", cls, single=True)]
            if passive.get(ids[0], not cost):
                continue
            seen.add(n)
            lvl = 10 + points
            item = {"n": n, "i": icon, "r": [[i, lvl, 1] for i in ids], "t": 1}
            if not ids[0]:  # newer than the client tables: no Wowhead tooltip, so keep the site's text
                item["tt"] = {"0": [cost, desc]}
                missing.append(f"{cls} talent {n} (tooltip from wowforevertalents.com)")
            spells.append(item)

        spells.sort(key=lambda s: (s.get("t", 0), s["r"][0][1], s["n"]))
        data["classes"][cls] = spells
        if cls in STANCES:
            icons = {s["n"]: s["i"] for s in spells}
            data["stances"][cls] = [{"n": n, "i": icons[n], "page": p} for n, p in STANCES[cls] if n in icons]
            for n, _ in STANCES[cls]:
                if n not in icons:
                    print(f"{cls}: stance {n} isn't in the Forever spell list", file=sys.stderr)

    for name, classes in GENERAL:
        g = {"n": name, "i": GENERAL_ICONS[name], "id": spell_id(name, "", single=True)}
        if classes:
            g["cls"] = classes
        data["general"].append(g)
    racial = {}
    for race, abil in racials(fetch(f"{SITE}/racials/", cache, "racials.html")).items():
        for n, icon, meta, desc in abil:
            g = racial.setdefault(n, {"n": n, "i": icon, "id": spell_id(n, "Racial", single=True, race=race), "race": []})
            if race not in g["race"]:
                g["race"].append(race)
            if not g["id"]:
                g["tt"] = [meta, desc]
    for g in sorted(racial.values(), key=lambda g: (RACES.index(g["race"][0]), g["n"])):
        data["general"].append(g)
    for name, i, icon in ITEMS:
        data["items"].append({"n": name, "i": icon, "id": i})

    html_path = pathlib.Path(html_path)
    page = html_path.read_text(encoding="utf-8")
    start, end = "/* spellbook-data:start */", "/* spellbook-data:end */"
    block = f"{start}\nconst SPELLBOOK = {json.dumps(data, separators=(',', ':'))};\n{end}"
    if start not in page:
        sys.exit("spellbook-data markers not found in " + str(html_path))
    page = re.sub(re.escape(start) + ".*?" + re.escape(end), lambda _: block, page, flags=re.S)
    html_path.write_text(page, encoding="utf-8")
    for cls, spells in data["classes"].items():
        print(f"{cls:8} {len(spells):3} spells, {sum(1 for s in spells if s.get('t'))} talents, {sum(1 for s in spells if s.get('new'))} new")
    print(f"general: {len(data['general'])} ({sum(1 for g in data['general'] if g.get('race'))} racials)")
    for m in missing:
        print("no spell ID:", m, file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
