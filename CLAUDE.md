# Barsmith

A static page for planning WoW Forever action bars, macros and keybinds, plus an addon (`/barplan`) that applies the plan in game. See [README.md](README.md) for what users see and the plan string format. Record new sources in its Sources section.

## What's here

- `index.html`: the whole planner in one file (HTML, CSS and JS, no framework, no build step). Plans are saved in `localStorage` under `barplanner.v3`; older keys (`v2`, `v1`) are migrated on load, so keep that migration working if the saved shape changes.
- The spellbook data sits inside `index.html` between `/* spellbook-data:start */` and `/* spellbook-data:end */`. Don't edit it by hand; rebuild it with `tools/build-spellbook.py`.
- `addon/BarPlan/`: the in-game importer (Lua, one file). The `.toc` lists interface versions 16001 (Forever) and 11509 (Classic Era). It reads the same `BP1:` plan string the page writes, so change both sides together.
- `backdrops/`: one 1440x900 WebP per race, made by `tools/fetch-backdrops.py`.
- `tools/`: Python scripts that fetch data. Run them with `python3 -I`.

## Building and publishing

There is no build for the page itself. `.github/workflows/pages.yml` runs on every push to `main` (or by hand): it copies `index.html` and `backdrops/` into `_site`, zips `addon/BarPlan` into `_site/BarPlan.zip`, and deploys that to GitHub Pages at https://rubensayshi.github.io/wowforever-barplanner/ (repo `rubensayshi/wowforever-barplanner`).

If you add a file the page needs, add it to the workflow's copy step too.

Regenerating data:

```
python3 -I tools/build-spellbook.py index.html [cache-dir]   # spellbook from wowforevertalents.com + wago.tools (build 1.60.1.70707)
python3 -I tools/fetch-backdrops.py backdrops                # needs Pillow
```

## Checking changes

- Page: open `index.html` in a browser (or serve the folder) and try it. There are no automated tests.
- Addon: not tested in the real game client yet, only against a mock of the WoW API (not in this repo).

## Git

We do everything on `main`. Pushing to `main` publishes the page through GitHub Pages.
