"""Inline every font and image into one self-contained page.
Run from this folder:  python3 build.py   ->  writes ../index.html"""
import base64, re, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MIME = {"woff2": "font/woff2", "webp": "image/webp", "png": "image/png", "jpg": "image/jpeg"}
src = open(os.path.join(HERE, "page.html"), encoding="utf-8").read()
cache = {}
def repl(m):
    p = m.group(1)
    if p not in cache:
        data = open(os.path.join(HERE, p), "rb").read()
        cache[p] = f"data:{MIME[p.rsplit('.', 1)[1]]};base64," + base64.b64encode(data).decode()
    return cache[p]
out = re.sub(r"\{\{ASSET:([^}]+)\}\}", repl, src)
if "{{" in out:
    sys.exit("unresolved asset placeholder")
dst = os.path.join(HERE, "..", "index.html")
open(dst, "w", encoding="utf-8").write(out)
print(f"index.html {len(out)/1024:.0f} KB")
