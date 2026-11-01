# Barsmith

Set up your WoW Forever action bars, macros and keybinds in the browser, then load them into the game with one string.

**Page:** https://rubensayshi.github.io/wowforever-barplanner/

- An in-game-looking screen: main bar with bars 2, 3 and 6–8 stacked on top, bars 4 and 5 on the right edge, stance bar and pet bar above.
- Pick a class and race (only the combos Forever allows), then drag spells from that class's Forever spellbook: trainer spells, active talents and racials, with spells new in Forever marked ★. A level slider greys out spells you won't have yet.
- Write macros, plan the main bar once per stance or form that swaps it (warrior stances, Cat and Bear Form, Stealth) and on its page 2 (Shift+2), and bind keys in keybind mode (hover a button, press a key).
- Keep as many plans per class as you like. They're saved in your browser; the plan string moves them anywhere else.
- Works with EllesmereUI, which uses the game's normal bar slots and keybinds.

## Getting it into the game

1. Download [BarPlan.zip](https://rubensayshi.github.io/wowforever-barplanner/BarPlan.zip) and unzip it into `Interface/AddOns`, so you get `Interface/AddOns/BarPlan`.
2. Copy the plan string from the page.
3. In game, out of combat: `/barplan`, paste, **Check**, **Apply**. This creates the macros, fills the buttons and saves the keybinds. Spells you haven't learned yet are skipped and go onto their button when you learn them.
4. **Export my bars** in `/barplan` gives you a string to load back into the page.

The addon refuses a plan made for a different class. It hasn't been tested in the real game client yet, only against a mock of the WoW API.

## Files

| File | What it is |
|---|---|
| [index.html](index.html) | The planner, with the spellbook data embedded. Plans are saved in your browser. |
| [backdrops/](backdrops) | One screenshot per race (its starting zone) for the screen's backdrop, 1440x900 WebP. |
| [addon/BarPlan](addon/BarPlan) | The in-game importer (`/barplan`). |
| [tools/build-spellbook.py](tools/build-spellbook.py) | Rebuilds the spellbook data in index.html from Forever's data: `python3 -I tools/build-spellbook.py index.html [cache-dir]` |
| [tools/fetch-backdrops.py](tools/fetch-backdrops.py) | Downloads the race backdrops from Warcraft Wiki and shrinks them: `python3 -I tools/fetch-backdrops.py backdrops` (needs Pillow) |
| [.github/workflows/pages.yml](.github/workflows/pages.yml) | Publishes the page, the backdrops and BarPlan.zip on every push to `main`. |

## Plan string

`BP1:` followed by base64 of UTF-8 text. One record per line, fields separated by tabs (`\\`, `\t` and `\n` escaped):

```
BARPLAN 1
CLASS   SHAMAN
RACE    Dwarf
MACRO   name  icon  perChar  body
SLOT    slot  spell|macro|item|clear  value
BIND    key   command
```

Spells are names, optionally with a rank (`Healing Wave(Rank 1)`), or `spell:ID`. Items are names or `item:ID`.

## Sources

Read 2026-11-01.

- EllesmereUI source (retail 7.2.2, April 2026): https://github.com/Anysu94/EllesmereUI . `EllesmereUIActionBars/EllesmereUIActionBars.lua` maps Bar 1–8 to the standard action pages (slots 1–12, 61, 49, 25, 37, 145, 157, 169) and binding commands ACTIONBUTTON / MULTIACTIONBAR1–7BUTTON. Not checked against the Forever build.
- EllesmereUI on Forever: https://www.icy-veins.com/wow-forever/news/wow-forever-players-can-now-build-their-perfect-ui-with-ellesmereui/ (403 when fetched; title from search results)
- ForeverSVFix release notes (SavedVariables loading bug, EllesmereUI profiles): https://github.com/nobewayo/ForeverSVFix/releases
- EUI Tweaks (lists game version 1.60.1): https://www.curseforge.com/wow/addons/eui-tweaks
- Action slot numbers, including stance/form pages (slots 73–120, separate from bars 2–5): https://warcraft.wiki.gg/wiki/Action_slot (retail page; Forever differs for some forms, see the next two lines)
- Which forms swap the main bar in Forever: the client's SpellShapeshiftForm table, column BonusActionBar, for build 1.60.1.70707: https://wago.tools/db2/SpellShapeshiftForm?build=1.60.1.70707 . Cat Form 1, Bear and Dire Bear Form 3, Battle Stance 1, Defensive Stance 2, Berserker Stance 3, Stealth 1 (page = slot 73 + 12 × (value − 1)). Moonkin Form and Shadowform are 0, so they keep the normal main bar, unlike retail. There's no Prowl form, so Prowl should stay on the Cat Form page (not checked in game: `/dump GetBonusBarOffset()` while prowling should print 1).
- Forever's own UI source, 1.60.1 (70532), mirrored at https://github.com/Gethe/wow-ui-source/tree/forever (read 2026-11-01): `Blizzard_ActionBarController/ActionBarController.lua` pages the main bar by `C_ActionBar.GetBonusBarIndex()` (so by the table above), and `Blizzard_ActionBar/Shared/MultiActionBars.xml` gives Edit Mode's Bar 2, 3, 4 (RightBar1), 5 (RightBar2) and 6–8 the slots 61, 49, 25, 37, 145, 157, 169 and buttons MULTIACTIONBAR1–7BUTTON, the same as the planner's bars.
- Spellbook data (read 2026-11-01), built by tools/build-spellbook.py:
  - Trainer spells per class with each rank's level, active talents and racials: wowforevertalents.com (https://wowforevertalents.com/abilities/, /<class>/, /racials/), which reads the Forever client build 1.60.1.70707 and the server hotfixes of 30 October.
  - Spell IDs per rank, passive flags and race limits (for example Desperate Prayer is Dwarf-only, Fear Ward is for every priest): the Forever client's tables for build 1.60.1.70707 via wago.tools (https://wago.tools/db2/SkillLineAbility?build=1.60.1.70707, plus SpellName, Spell, SpellMisc, Talent, TalentTab).
  - Spells newer than the client tables (Oath of Light, the top rank of Lacerate) and renamed ranks have no ID, so their tooltip is the text from wowforevertalents.com.
- Race backdrops, starting-zone screenshots from Warcraft Wiki (fetched 2026-11-01, file names in tools/fetch-backdrops.py): Human Northshire Abbey, Dwarf Kharanos, Gnome Gates of Ironforge, Night Elf Dolanaar, Orc Valley of Trials, Undead Tirisfal Glades, Tauren Camp Narache, Troll Durotar, Skyborne Dalaran (Zephras Isle has no screenshots on the wiki yet). Some are from later expansions, so they don't always look like the Classic client. https://warcraft.wiki.gg/images/<file>
- Original idea: Naowh's Forever action bar planner, https://naowh.gg/forever/action-bars (it only sets up bars for Naowh's own addon suite)
- Heading font: Marcellus (Google Fonts), standing in for the game's Friz Quadrata
- Spell icons load from https://wow.zamimg.com/images/wow/icons/
- Tooltips load from Wowhead's Forever database when you hover a spell, stance or item: https://nether.wowhead.com/forever/tooltip/spell/<id> (the same source as https://www.wowhead.com/forever/spell=<id>). Checked 2026-11-01: 26 of 40 sampled spells differ from Classic, e.g. Lightning Bolt has a 2.5 sec cast. General spells (Attack, racials) have no ID in the data, so they keep the planner's own tooltip.

World of Warcraft and its icons and screenshots are Blizzard Entertainment's. This is a fan tool.
