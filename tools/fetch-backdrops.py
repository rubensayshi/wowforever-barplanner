"""Download the class backdrops from Warcraft Wiki and save them as backdrops/<class>.webp.

Each class gets a screenshot of a place that fits it. The images are cropped to
16:10 (the screen's shape) and shrunk to 1440x900 so the page stays light.

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

# class -> (Warcraft Wiki file name, horizontal focus 0..1 for the crop)
BACKDROPS = {
    "warrior": ("Valley of Honor.jpg", 0.5),
    "paladin": ("Light's Hope Chapel.jpg", 0.5),
    "hunter": ("Mulgore vista.jpg", 0.5),
    "rogue": ("Ravenholdt.jpg", 0.5),
    "priest": ("Cathedral of Light.jpg", 0.5),
    "shaman": ("Kharanos.jpg", 0.5),
    "mage": ("The Mage Quarter.jpg", 0.5),
    "warlock": ("Dark Portal crater (Classic).jpg", 0.5),
    "druid": ("Moonglade.jpg", 0.5),
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
    for cls, (name, focus) in BACKDROPS.items():
        path = out / f"{cls}.webp"
        if path.exists():
            print(f"{cls}: have it")
            continue
        req = urllib.request.Request(url_for(name), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as r:
            img = Image.open(io.BytesIO(r.read())).convert("RGB")
        crop_to(img, SIZE, focus).save(path, "WEBP", quality=55, method=6)
        print(f"{cls}: {name} -> {path} ({path.stat().st_size // 1024} KB)")
        time.sleep(2)


if __name__ == "__main__":
    main(*sys.argv[1:])
