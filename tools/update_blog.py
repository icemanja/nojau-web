"""Sustituye la lista de artículos del blog (entre <!-- BLOG:START --> y <!-- BLOG:END -->)
en index.html y en/index.html con las últimas entradas del RSS de WordPress.com.

Uso: python3 tools/update_blog.py [directorio_del_sitio] [--feed fichero_local.xml]
Si el RSS no se puede leer o no trae entradas, deja la web como está (no falla el despliegue).
"""
import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = "https://jdoblasblog.wordpress.com/feed/"
N = 3
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def clean(text, limit=170):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*\[(…|&hellip;|\.\.\.)\]\s*$", "", text)
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return text


def read_feed(src):
    if src:
        data = open(src, "rb").read()
    else:
        req = urllib.request.Request(FEED, headers={"User-Agent": "nojau-web-build"})
        data = urllib.request.urlopen(req, timeout=20).read()
    root = ET.fromstring(data)
    posts = []
    for item in root.iter("item"):
        title = html.unescape(item.findtext("title") or "").replace(" ", " ").strip()
        link = (item.findtext("link") or "").strip()
        date = parsedate_to_datetime(item.findtext("pubDate"))
        desc = clean(item.findtext("description"))
        if title and link.startswith("https://"):
            posts.append((date, title, link, desc))
    posts.sort(key=lambda p: p[0], reverse=True)
    return posts[:N]


def render(posts, lang):
    out = []
    for date, title, link, desc in posts:
        iso = date.date().isoformat()
        if lang == "es":
            shown = f"{date.day} {MESES[date.month - 1]} {date.year}"
            extra = f"<p>{html.escape(desc)}</p>" if desc else ""
        else:
            shown = f"{date.day} {MONTHS[date.month - 1]} {date.year}"
            extra = '<p lang="en">Article in Spanish.</p>'
        out.append(f'        <a class="post" href="{html.escape(link)}" rel="noopener" lang="es">'
                   f'<time datetime="{iso}">{shown}</time><div><h3>{html.escape(title)}</h3>{extra}</div></a>')
    return "\n".join(out)


def main():
    args = sys.argv[1:]
    feed = None
    if "--feed" in args:
        i = args.index("--feed")
        feed = args[i + 1]
        del args[i:i + 2]
    site = args[0] if args else "."
    try:
        posts = read_feed(feed)
    except Exception as e:  # red caída, XML roto…: se mantiene la lista actual
        print(f"Aviso: no se pudo leer el RSS ({e}); se mantiene la lista actual")
        return
    if not posts:
        print("Aviso: el RSS no trae entradas; se mantiene la lista actual")
        return
    for path, lang in [(f"{site}/index.html", "es"), (f"{site}/en/index.html", "en")]:
        s = open(path, encoding="utf-8").read()
        new, n = re.subn(r"(<!-- BLOG:START -->\n).*?(\n<!-- BLOG:END -->)",
                         lambda m: m.group(1) + render(posts, lang) + m.group(2), s, flags=re.S)
        if n != 1:
            print(f"Aviso: marcadores del blog no encontrados en {path}")
            continue
        open(path, "w", encoding="utf-8").write(new)
        print(f"{path}: {len(posts)} artículos")


if __name__ == "__main__":
    main()
