"""Download the race backdrops from Warcraft Wiki and save them as backdrops/<race>.webp.

Each race gets a screenshot of its starting zone. Skyborne start on Zephras Isle,
which has no screenshots on the wiki yet, so they get Dalaran, where Alliance
Skyborne arrive. The images are cropped to 16:10 (the screen's shape) and
shrunk to 1440x900 so the page stays light.

Run: python3 -I tools/fetch-backdrops.py [backdrops]
Needs Pillow. Files that already exist are skipped; delete one to fetch it again.
"""
import io
import pathlib
import sys
import time
import urllib.parse
import urllib.request

from PIL import Image

# race (lowercase, no spaces) -> (Warcraft Wiki file name, horizontal focus 0..1 for the crop)
BACKDROPS = {
    "human": ("Northshire Abbey.jpg", 0.5),
    "dwarf": ("Kharanos.jpg", 0.5),
    "gnome": ("Gnomeregan Entrance.jpg", 0.5),
    "nightelf": ("Dolanaar.jpg", 0.5),
    "orc": ("Valley of Trials.jpg", 0.5),
    "undead": ("Tirisfal Glades.jpg", 0.5),
    "tauren": ("Camp Narache.jpg", 0.5),
    "troll": ("Durotar.jpg", 0.5),
    "skyborne": ("Zones Dalaran 021.jpg", 0.5),
}
SIZE = (1440, 900)
USER_AGENT = "barplanner-build/1.0 (+https://github.com/rubensayshi/wowforever-barplanner)"


def url_for(name):
    return "https://warcraft.wiki.gg/images/" + urllib.parse.quote(name.replace(" ", "_"))


def crop_to(img, size, focus):
    w, h = img.size
    tw, th = size
    if w / h > tw / th:  # too wide: cut the sides around the focus point
        nw = round(h * tw / th)
        left = min(max(round(w * focus - nw / 2), 0), w - nw)
        img = img.crop((left, 0, left + nw, h))
    else:  # too tall: keep the middle
        nh = round(w * th / tw)
        top = (h - nh) // 2
        img = img.crop((0, top, w, top + nh))
    return img.resize(size, Image.LANCZOS)


def main(out_dir="backdrops"):
    out = pathlib.Path(out_dir)
    out.mkdir(exist_ok=True)
    for race, (name, focus) in BACKDROPS.items():
        path = out / f"{race}.webp"
        if path.exists():
            print(f"{race}: have it")
            continue
        req = urllib.request.Request(url_for(name), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as r:
            img = Image.open(io.BytesIO(r.read())).convert("RGB")
        crop_to(img, SIZE, focus).save(path, "WEBP", quality=55, method=6)
        print(f"{race}: {name} -> {path} ({path.stat().st_size // 1024} KB)")
        time.sleep(2)


if __name__ == "__main__":
    main(*sys.argv[1:])
