# Bar Planner

Set up your WoW Forever action bars, macros and keybinds in the browser, then load them into the game with one string.

**Page:** https://rubensayshi.github.io/wowforever-barplanner/

- An in-game-looking screen: main bar with bars 2, 3 and 6–8 stacked on top, bars 4 and 5 on the right edge, stance bar and pet bar above.
- Pick a class and race (only the combos Forever allows), then drag spells from that class's spellbook. A level slider greys out spells you won't have yet.
- Write macros, plan the main bar once per stance or form, and bind keys in keybind mode (hover a button, press a key).
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
| [tools/build-spellbook.py](tools/build-spellbook.py) | Rebuilds the spellbook data in index.html: `python3 -I tools/build-spellbook.py index.html [cache.json]` |
| [tools/fetch-backdrops.py](tools/fetch-backdrops.py) | Downloads the race backdrops from Warcraft Wiki and shrinks them: `python3 -I tools/fetch-backdrops.py backdrops` (needs Pillow) |
| [.github/workflows/pages.yml](.github/workflows/pages.yml) | Publishes the page, the backdrops and BarPlan.zip on every push to `main`. |

## Plan string

`BP1:` followed by base64 of UTF-8 text. One record per line, fields separated by tabs (`\\`, `\t` and `\n` escaped):

```
BARPLAN 1
CLASS   SHAMAN
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
- Action slot numbers, including stance/form pages (slots 73–120, separate from bars 2–5): https://warcraft.wiki.gg/wiki/Action_slot (retail page; Classic uses the same pages for Warrior, Druid Cat/Bear, Rogue Stealth)
- Spellbook data: trainer spells per class and level from What's Training (https://github.com/fusionpit/WhatsTraining, Classes/Vanilla), names and icons from Wowhead's Classic tooltip API (https://nether.wowhead.com/classic/tooltip/spell/<id>). Vanilla data, not Forever's class changes.
- Race backdrops, starting-zone screenshots from Warcraft Wiki (fetched 2026-11-01, file names in tools/fetch-backdrops.py): Human Northshire Abbey, Dwarf Kharanos, Gnome Gates of Ironforge, Night Elf Dolanaar, Orc Valley of Trials, Undead Tirisfal Glades, Tauren Camp Narache, Troll Durotar, Skyborne Dalaran (Zephras Isle has no screenshots on the wiki yet). Some are from later expansions, so they don't always look like the Classic client. https://warcraft.wiki.gg/images/<file>
- Heading font: Marcellus (Google Fonts), standing in for the game's Friz Quadrata
- Spell icons load from https://wow.zamimg.com/images/wow/icons/

World of Warcraft and its icons and screenshots are Blizzard Entertainment's. This is a fan tool.
