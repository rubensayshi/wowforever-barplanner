"""Inline the default backdrop screenshot into bar-planner.html.

The default is Kharanos (Dun Morogh) from Warcraft Wiki, shrunk to 1440x810 WebP:

  curl -A "Mozilla/5.0" -o Kharanos.jpg https://warcraft.wiki.gg/images/Kharanos.jpg
  python3 -c "from PIL import Image; Image.open('Kharanos.jpg').convert('RGB').resize((1440, 810)).save('kharanos.webp', quality=55, method=6)"

Then run: python3 -I tools/embed-backdrop.py kharanos.webp bar-planner.html
"""
import base64
import pathlib
import re
import sys

START, END = "/* backdrop:start */", "/* backdrop:end */"


def main(img_path, html_path):
    data = base64.b64encode(pathlib.Path(img_path).read_bytes()).decode()
    block = f'{START}\n:root {{ --backdrop: url("data:image/webp;base64,{data}"); }}\n{END}'
    html_path = pathlib.Path(html_path)
    html = html_path.read_text(encoding="utf-8")
    if START not in html:
        sys.exit("backdrop markers not found in " + str(html_path))
    html = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda _: block, html, flags=re.S)
    html_path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:])
