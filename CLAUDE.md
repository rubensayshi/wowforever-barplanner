# Barsmith

A static page for planning WoW Forever action bars, macros and keybinds, plus an addon (`/barsmith`) that applies the plan in game. See [README.md](README.md) for what users see and the plan string format. Record new sources in its Sources section.

## What's here

- `index.html`: the whole planner in one file (HTML, CSS and JS, no framework, no build step). Plans are saved in `localStorage` under `barplanner.v3`; older keys (`v2`, `v1`) are migrated on load, so keep that migration working if the saved shape changes.
- The spellbook data sits inside `index.html` between `/* spellbook-data:start */` and `/* spellbook-data:end */`. Don't edit it by hand; rebuild it with `tools/build-spellbook.py`.
- `addon/Barsmith/`: the in-game importer (Lua, one file). The `.toc` lists interface versions 16001 (Forever) and 11509 (Classic Era). It reads the same `BP1:` plan string the page writes, so change both sides together.
- `backdrops/`: one 1440x900 WebP per race, made by `tools/fetch-backdrops.py`.
- `tools/`: Python scripts that fetch data. Run them with `python3 -I`.

## Building and publishing

There is no build for the page itself. `.github/workflows/pages.yml` runs on every push to `main` (or by hand): it copies `index.html` and `backdrops/` into `_site`, zips `addon/Barsmith` into `_site/Barsmith.zip` (with the TOC's `@project-version@` filled in from `git describe`), and deploys that to GitHub Pages at https://rubensayshi.github.io/wowforever-barplanner/ (repo `rubensayshi/wowforever-barplanner`).

Addon releases: pushing a tag `v*` runs `.github/workflows/release.yml`, which uses BigWigsMods/packager (configured by `.pkgmeta`) to zip `addon/Barsmith`, fill in `@project-version@` and upload to CurseForge as "Barsmith Importer" and to GitHub Releases. A tag containing `beta` or `alpha` is uploaded as that release type. Add an entry to `CHANGELOG.md` before tagging: it's the changelog CurseForge shows (`.pkgmeta` `manual-changelog`). The packager tags the file for each interface in the TOC (16001 → Forever 1.60.1, 11509 → Classic Era). The upload needs the repo secret `CF_API_KEY` and `## X-Curse-Project-ID:` in the TOC. The packager only knows the `_Camelot.toc` suffix for Forever, not `_Forever.toc`, if the TOC ever gets split.

If you add a file the page needs, add it to the workflow's copy step too.

Regenerating data:

```
python3 -I tools/build-spellbook.py index.html [cache-dir]   # spellbook from wowforevertalents.com + wago.tools (build 1.60.1.70707)
python3 -I tools/fetch-backdrops.py backdrops                # needs Pillow
```

## Checking changes

- Page: open `index.html` in a browser (or serve the folder) and try it. There are no automated tests.
- Addon: tried on WoW Classic (2026-11-01), where it worked; not yet tested on the Forever client. Beyond that, only checked against a mock of the WoW API (not in this repo).

## Git

We do everything on `main`. Pushing to `main` publishes the page through GitHub Pages.
