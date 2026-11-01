The in-game half of **[Barsmith](https://rubensayshi.github.io/wowforever-barplanner/)**, a free web page for planning your WoW Forever action bars, macros + keybinds. You set it all up on the page, copy 1 string, paste it into `/barsmith` and the addon does the dragging and binding for you.

I think it's most useful for alts (or after a fresh install) where setting up 8 bars and a pile of keybinds by hand is a bit of a chore. If your bars are already sorted this probably isn't for you.

## How it works

1. Open **[the Barsmith page](https://rubensayshi.github.io/wowforever-barplanner/)**, pick your class + race and drag spells from the Forever spellbook onto your bars. Write your macros, then use keybind mode to bind keys like you would in game (hover a button, press a key)
2. Copy the plan string at the bottom of the page
3. In game, out of combat: `/barsmith`, paste, **Check** to see what it'll change, then **Apply**

Apply creates or updates the plan's macros, puts spells, macros + items on their buttons and sets the keybinds (and saves them). Buttons and keys that aren't in the plan are left alone.

## What it does

- Spells you haven't learned yet are skipped and go onto their planned button once you learn them (as long as that button is still empty). Same for items you pick up later. `/barsmith auto` turns that off
- Stance and form bars: warrior stances, Cat + Bear Form and Stealth swap the main bar, so on the page you plan the main bar once per stance and the addon fills each of those pages
- **Export my bars** in `/barsmith` turns your current bars into a string you can load into the page, so you don't have to start from scratch
- It refuses a plan made for another class (no Shaman bars on your Warrior)
- Works with EllesmereUI, Bartender4, Dominos and ElvUI: they show the game's normal bar slots and pass the keybinds on to their own buttons. They number bars by action page though, so Bar 2 on the page is their bar 6, Bar 3 is 5, Bar 4 is 3, Bar 5 is 4 and Bars 6-8 are 13-15 (Dominos: 12-14)

## Commands

- `/barsmith` opens the window (paste, Check, Apply, Export my bars)
- `/barsmith apply` runs the last applied plan again
- `/barsmith auto` turns auto-fill for newly learned spells on or off
- `/barsmith export` opens the window with your current bars as a string

## Known issues

- **Not tested on the Forever client yet.** I tried it on WoW Classic, where it worked fine, and the rest is checked against a mock of the WoW API, so expect some funkyness. Make a backup of your `WTF` folder if you're attached to your current setup
- Some bar addons switch the main bar for Shadowform, Moonkin Form or Prowl where Forever itself doesn't. The addon copies the right buttons onto those pages too, but I haven't checked that in game yet
- Bars and keys can't be changed in combat (the game doesn't allow it), so Apply asks you to try again after the fight. Auto-fill just catches up once you're out of combat

If something comes out wrong, a comment with your class, your plan string and what you expected vs what you got helps a lot. Which class is broken for you?

## Credits

- The idea comes from [Naowh's Forever action bar planner](https://naowh.gg/forever/action-bars), which only sets up bars for Naowh's own addon suite
- Spells, talents and racials from [wowforevertalents.com](https://wowforevertalents.com/), tooltips from Wowhead's Forever database
- Source: [github.com/rubensayshi/wowforever-barplanner](https://github.com/rubensayshi/wowforever-barplanner)
