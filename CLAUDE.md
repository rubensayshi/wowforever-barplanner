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

### Releasing the addon

The addon is on CurseForge as "Barsmith Importer", project ID 1778365 (https://authors.curseforge.com/#/projects/1778365/files). The project page's logo and description are in `art/`. v1.0.0-beta1 was the first release (2026-11-01).

To release:

1. Add an entry for the new version at the top of `CHANGELOG.md`. It's the changelog CurseForge shows (`.pkgmeta` `manual-changelog`), written for players.
2. Commit it to `main` and push.
3. Tag the commit and push only that tag: `git tag -a v1.0.0-beta2 -m "Barsmith Importer v1.0.0-beta2"` then `git push origin v1.0.0-beta2`. Don't use `git push --tags`: every tag pushed starts its own release run, so an old tag would be uploaded again.

Pushing a `v*` tag runs `.github/workflows/release.yml`. It uses BigWigsMods/packager v2.6.1 (configured by `.pkgmeta`) to zip `addon/Barsmith` with the root `LICENSE` and `CHANGELOG.md`, fill in `@project-version@` from the tag, upload to CurseForge and make a GitHub release. A tag containing `beta` or `alpha` is uploaded as that release type. The packager marks the file for each interface in the TOC (16001 → Forever 1.60.1, 11509 → Classic Era 1.15.9). The upload needs the repo secret `CF_API_KEY` (set) and `## X-Curse-Project-ID:` in the TOC. If the TOC ever gets split, the only Forever suffix the packager knows is `_Camelot.toc`, not `_Forever.toc`.

Running the packager locally (to debug a release without the pipeline) works from Git Bash on Windows. Download `release.sh` from the packager's tag and run `bash release.sh -d -t <repo> -r <absolute dir>`; `-d` skips the upload, `-z` also skips the zip. It needs `jq` and `zip`. On Windows, `zip` is GnuWin32's (`C:\Program Files (x86)\GnuWin32\bin`) and `jq` needs a wrapper that adds `-b`, since Windows jq writes `\r\n` and that breaks the game version IDs in the upload. For a real upload, set `CF_API_KEY` and leave out `-d`.

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
