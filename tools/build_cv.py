#!/usr/bin/env python3
"""Genera el CV en PDF (castellano e inglés) a partir del contenido de la web.

Todo el texto sale de index.html y en/index.html, así que el CV y la web
siempre dicen lo mismo. Requiere: beautifulsoup4 y playwright (chromium).

Uso: python3 tools/build_cv.py      → cv/javier-doblas-cv-es.pdf y -en.pdf
"""
import asyncio
import html
import re
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
MARK = ROOT / "tools" / "brand-mark.svg"

L = {
    "es": dict(src="index.html", out="javier-doblas-cv-es.pdf", lang="es",
               profile="Perfil", figures="En cifras", career="Trayectoria", cases="Hitos",
               areas="Dónde aporto", edu="Formación", page="Página",
               updated="Actualizado", months=["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                                              "agosto", "septiembre", "octubre", "noviembre", "diciembre"]),
    "en": dict(src="en/index.html", out="javier-doblas-cv-en.pdf", lang="en",
               profile="Profile", figures="At a glance", career="Career", cases="Milestones",
               areas="Expertise", edu="Education", page="Page",
               updated="Updated", months=["January", "February", "March", "April", "May", "June", "July",
                                          "August", "September", "October", "November", "December"]),
}


def inner(el):
    return "".join(str(c) for c in el.contents).strip()


def extract(path):
    s = BeautifulSoup((ROOT / path).read_text(encoding="utf-8"), "html.parser")
    hero = s.select_one("section.hero")
    d = {
        "eyebrow": hero.select_one(".eyebrow").get_text(" ", strip=True),
        "lead": hero.select_one(".lead").get_text(" ", strip=True),
        "figures": [(f.b.get_text(strip=True), f.span.get_text(" ", strip=True)) for f in s.select(".figures .fig")],
        "cases": [dict(tag=c.select_one(".tag").get_text(" ", strip=True),
                       h=c.h3.get_text(" ", strip=True),
                       p=c.p.get_text(" ", strip=True),
                       chips=[li.get_text(strip=True) for li in c.select("li")]) for c in s.select(".cases .case")],
        "areas": [(a.h3.get_text(" ", strip=True), a.p.get_text(" ", strip=True)) for a in s.select(".areas .area")],
        "career": [],
        "edu": [],
        "photo": (ROOT / "img" / "javier-doblas.jpg").as_uri(),
    }
    for r in s.select(".timeline .row"):
        h3 = r.h3
        small = h3.small.get_text(" ", strip=True).lstrip("· ").strip() if h3.small else ""
        if h3.small:
            h3.small.extract()
        d["career"].append(dict(when=r.select_one(".when").get_text(" ", strip=True),
                                role=h3.get_text(" ", strip=True), org=small,
                                p=r.p.get_text(" ", strip=True), minor="minor" in r.get("class", [])))
    for e in s.select(".edu > div"):
        b = e.b.get_text(" ", strip=True)
        e.b.extract()
        d["edu"].append((b, e.get_text(" ", strip=True)))
    return d


def esc(t):
    return html.escape(t, quote=False)


def render(d, t, today):
    mark = re.sub(r'class="brand-mark"', 'class="mark"', MARK.read_text(encoding="utf-8"))
    figs = "".join(f'<div class="fig"><b>{esc(n)}</b><span>{esc(x)}</span></div>' for n, x in d["figures"])
    career = "".join(
        f'<div class="row{" minor" if c["minor"] else ""}"><div class="when">{esc(c["when"])}</div>'
        f'<div><h3>{esc(c["role"])}{(" <small>· " + esc(c["org"]) + "</small>") if c["org"] else ""}</h3>'
        f'<p>{esc(c["p"])}</p></div></div>' for c in d["career"])
    cases = "".join(
        f'<div class="case"><div class="tag">{esc(c["tag"])}</div><h3>{esc(c["h"])}</h3><p>{esc(c["p"])}</p>'
        f'<div class="chips">{" · ".join(esc(x) for x in c["chips"])}</div></div>' for c in d["cases"])
    areas = "".join(f'<div class="area"><h3>{esc(h)}</h3><p>{esc(p)}</p></div>' for h, p in d["areas"])
    edu = "".join(f'<div class="edu"><b>{esc(b)}</b><span>{esc(x)}</span></div>' for b, x in d["edu"])
    date = f'{t["months"][today.month - 1]} {today.year}'
    f = FONTS.as_uri()
    return f"""<!doctype html><html lang="{t['lang']}"><head><meta charset="utf-8">
<title>Javier Doblas Martín · CV</title>
<style>
@font-face{{font-family:Fraunces;src:url({f}/fraunces-opsz-normal.woff2);font-style:normal;font-weight:100 900}}
@font-face{{font-family:Fraunces;src:url({f}/fraunces-opsz-italic.woff2);font-style:italic;font-weight:100 900}}
@font-face{{font-family:'Instrument Sans';src:url({f}/instrument-sans-400.woff2);font-weight:400}}
@font-face{{font-family:'Instrument Sans';src:url({f}/instrument-sans-500.woff2);font-weight:500}}
@font-face{{font-family:'Instrument Sans';src:url({f}/instrument-sans-600.woff2);font-weight:600}}
@page{{size:A4;margin:14mm 16mm 13mm}}
:root{{--paper:#F4F0E8;--paper2:#EBE5D9;--ink:#16212E;--ink2:#3C4756;--muted:#5A6270;--line:#D6CDBD;--accent:#A3491F}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:'Instrument Sans',Arial,sans-serif;font-size:9.6pt;line-height:1.45;color:var(--ink2)}}
h1,h2,h3,p{{margin:0}}
header{{display:grid;grid-template-columns:1fr 30mm;gap:8mm;align-items:center;padding-bottom:6mm;border-bottom:1px solid var(--line)}}
.brand{{display:flex;align-items:center;gap:4mm}}
.mark{{height:15mm;width:auto;color:var(--ink)}}
.brand-dot{{fill:var(--accent)}}
.name{{border-left:1px solid var(--line);padding-left:4mm}}
h1{{font-family:Fraunces,Georgia,serif;font-weight:500;font-size:24pt;line-height:1.05;color:var(--ink)}}
.role{{font-size:8.2pt;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-top:2mm}}
.contact{{margin-top:4mm;font-size:9pt;color:var(--ink2)}}
.contact a{{color:var(--accent);text-decoration:none}}
.upd{{display:block;margin-top:1mm;font-size:8pt;color:var(--muted)}}
.photo{{width:30mm;height:30mm;border-radius:50%;object-fit:cover}}
h2{{font-size:8pt;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:600;margin:5mm 0 2.5mm}}
.lead{{font-family:Fraunces,Georgia,serif;font-size:11.5pt;line-height:1.45;color:var(--ink)}}
.figs{{display:grid;grid-template-columns:repeat(4,1fr);gap:5mm;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:3.5mm 0}}
.fig b{{display:block;font-family:Fraunces,Georgia,serif;font-weight:500;font-size:19pt;line-height:1;color:var(--ink);margin-bottom:1.5mm}}
.fig span{{font-size:8.2pt;color:var(--muted);line-height:1.3;display:block}}
.row{{display:grid;grid-template-columns:20mm 1fr;gap:4mm;padding:1.15mm 0;border-top:1px solid var(--line);break-inside:avoid}}
.row:first-child{{border-top:0}}
.when{{font-size:8.6pt;color:var(--muted);padding-top:.6mm}}
.row h3{{font-size:10pt;font-weight:600;color:var(--ink)}}
.row h3 small{{font-weight:400;color:var(--ink2);font-size:9.6pt}}
.row p{{margin-top:.5mm}}
.row.minor h3{{font-weight:500}}
.cases{{display:grid;grid-template-columns:1fr 1fr;gap:5mm 7mm}}
.case{{break-inside:avoid;border-top:2px solid var(--ink);padding-top:2.5mm}}
.tag{{font-size:7.6pt;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);font-weight:600}}
.case h3{{font-family:Fraunces,Georgia,serif;font-weight:500;font-size:11.5pt;line-height:1.25;color:var(--ink);margin:1.5mm 0}}
.chips{{margin-top:1.5mm;font-size:8.2pt;color:var(--muted)}}
.areas{{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm 6mm}}
.area{{break-inside:avoid}}
.area h3{{font-size:9.6pt;font-weight:600;color:var(--ink);margin-bottom:1mm}}
.area p{{font-size:8.8pt;line-height:1.4}}
.edus{{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm 6mm}}
.edu{{break-inside:avoid}}
.edu b{{display:block;color:var(--ink);font-weight:600}}
.edu span{{font-size:9pt}}
.p2{{break-before:page}}
.p2 > h2:first-child{{margin-top:0}}
footer{{margin-top:5mm;padding-top:2.5mm;border-top:1px solid var(--line);font-size:8pt;color:var(--muted);display:flex;justify-content:space-between}}
</style></head><body>
<header>
  <div>
    <div class="brand">{mark}<div class="name"><h1>Javier Doblas Martín</h1><div class="role">{esc(d['eyebrow'])}</div></div></div>
    <div class="contact"><a href="mailto:jdoblas@nojau.es">jdoblas@nojau.es</a> · <a href="https://www.nojau.es/">www.nojau.es</a> · <a href="https://www.linkedin.com/in/javierdoblas/">linkedin.com/in/javierdoblas</a><span class="upd">{t['updated']}: {date}</span></div>
  </div>
  <img class="photo" src="{d['photo']}" alt="">
</header>
<h2>{t['profile']}</h2>
<p class="lead">{esc(d['lead'])}</p>
<h2>{t['figures']}</h2>
<div class="figs">{figs}</div>
<h2>{t['cases']}</h2>
<div class="cases">{cases}</div>
<section class="p2">
<h2>{t['career']}</h2>
<div class="career">{career}</div>
<h2>{t['areas']}</h2>
<div class="areas">{areas}</div>
<h2>{t['edu']}</h2>
<div class="edus">{edu}</div>
</section>
</body></html>"""


async def main():
    import datetime
    today = datetime.date.today()
    out = ROOT / "cv"
    out.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        for k, t in L.items():
            tmp = ROOT / "tools" / f"_cv-{k}.html"
            tmp.write_text(render(extract(t["src"]), t, today), encoding="utf-8")
            await pg.goto(tmp.as_uri())
            await pg.wait_for_timeout(500)
            await pg.pdf(path=str(out / t["out"]), format="A4", print_background=True,
                         prefer_css_page_size=True)
            tmp.unlink()
            print("→", out / t["out"])
        await b.close()


if __name__ == "__main__":
    asyncio.run(main())
