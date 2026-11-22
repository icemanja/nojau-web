#!/usr/bin/env python3
"""Pone en sitemap.xml la fecha real de última modificación de cada página.

La fecha de cada URL es la más reciente entre:
- el último commit que cambió esa página o la hoja de estilos compartida, y
- el artículo más reciente del blog que aparece en la página (lo inserta
  update_blog.py en cada publicación).

Uso: python3 tools/update_sitemap.py _site
"""
import re
import subprocess
import sys
from pathlib import Path

BASE = "https://www.nojau.es/"
SHARED = ["assets/site.css"]


def git_date(paths):
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", *paths],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def page_file(loc):
    rel = loc[len(BASE):] if loc.startswith(BASE) else loc
    return (rel.rstrip("/") + "/index.html").lstrip("/") if rel else "index.html"


def main(site_dir):
    site = Path(site_dir)
    sitemap = site / "sitemap.xml"
    xml = sitemap.read_text(encoding="utf-8")

    def fix(match):
        block = match.group(0)
        loc = re.search(r"<loc>([^<]+)</loc>", block).group(1)
        rel = page_file(loc)
        dates = [d for d in [git_date([rel] + SHARED)] if d]
        html = site / rel
        if html.exists():
            dates += re.findall(r'<time datetime="(\d{4}-\d{2}-\d{2})"', html.read_text(encoding="utf-8"))
        if not dates:
            print(f"Aviso: sin fecha para {loc}; se deja como estaba")
            return block
        newest = max(dates)
        print(f"{loc} → {newest}")
        return re.sub(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{newest}</lastmod>", block)

    xml = re.sub(r"<url>.*?</url>", fix, xml, flags=re.S)
    sitemap.write_text(xml, encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
