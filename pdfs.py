"""PDF generation for SERAFIX: product datasheets, category catalogues and full catalogues (4 languages).

Uses headless Chromium (Playwright) so Arabic/Cyrillic shaping is correct. Results are cached in
.pdfcache/ by content hash, so only changed products are re-rendered.
"""
import hashlib, html, os, shutil, time

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, ".pdfcache")
LOGO = open(os.path.join(ROOT, "static", "assets", "logo", "serafix-horizontal-color.svg"), encoding="utf-8").read()
LOGO_W = open(os.path.join(ROOT, "static", "assets", "logo", "serafix-horizontal-white.svg"), encoding="utf-8").read()
FONT_DIR = "file://" + os.path.join(ROOT, "fonts-pdf")

T = {
    "tr": {"ds": "Ürün Teknik Föyü", "cat": "Ürün Kataloğu", "codes": "Ürün kodları", "variants": "Ölçüler ve kodlar", "specs": "Teknik özellikler",
           "contact": "Fiyat ve teslim bilgisi için bize ulaşın", "made": "Türkiye'de üretilmiştir", "contents": "İçindekiler", "products": "ürün",
           "edition": "2026 Baskısı", "draft": "TASLAK: Ürün görselleri değiştirilecektir"},
    "en": {"ds": "Product Datasheet", "cat": "Product Catalogue", "codes": "Product codes", "variants": "Sizes & codes", "specs": "Technical specifications",
           "contact": "Contact us for prices and delivery terms", "made": "Made in Türkiye", "contents": "Contents", "products": "products",
           "edition": "2026 Edition", "draft": "DRAFT: product photos to be replaced"},
    "ru": {"ds": "Технический лист изделия", "cat": "Каталог продукции", "codes": "Коды изделий", "variants": "Размеры и коды", "specs": "Технические характеристики",
           "contact": "Свяжитесь с нами для получения цен и условий поставки", "made": "Произведено в Турции", "contents": "Содержание", "products": "изделий",
           "edition": "Издание 2026", "draft": "ЧЕРНОВИК: фотографии будут заменены"},
    "ar": {"ds": "النشرة الفنية للمنتج", "cat": "كتالوج المنتجات", "codes": "رموز المنتج", "variants": "المقاسات والرموز", "specs": "المواصفات الفنية",
           "contact": "تواصل معنا لمعرفة الأسعار وشروط التسليم", "made": "صُنع في تركيا", "contents": "المحتويات", "products": "منتجاً",
           "edition": "إصدار 2026", "draft": "مسودة: سيتم استبدال صور المنتجات"},
}

CSS = """
@font-face{font-family:Inter;font-weight:400;src:url(%(f)s/inter-400.ttf)}
@font-face{font-family:Inter;font-weight:600;src:url(%(f)s/inter-600.ttf)}
@font-face{font-family:Inter;font-weight:700;src:url(%(f)s/inter-700.ttf)}
@font-face{font-family:Inter;font-weight:300;src:url(%(f)s/inter-300.ttf)}
@page{size:A4;margin:0}
*{box-sizing:border-box}
body{margin:0;font-family:Inter,'Noto Sans Arabic','Noto Naskh Arabic','DejaVu Sans',sans-serif;color:#11261C;font-size:10pt;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:210mm;min-height:297mm;padding:16mm 15mm 22mm;position:relative;page-break-after:always}
.page:last-child{page-break-after:auto}
.hd{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #0F3B2A;padding-bottom:5mm;margin-bottom:7mm}
.hd svg{width:46mm;height:auto}
.hd .k{font-size:8.5pt;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#1F7A47}
[dir=rtl] .hd .k{letter-spacing:0}
h1{font-size:20pt;line-height:1.2;margin:0 0 2mm;font-weight:700}
.tag{display:inline-block;background:#E3F0E6;color:#0F3B2A;font-weight:700;font-size:8pt;padding:1mm 3mm;border-radius:10mm;margin-bottom:3mm}
.top{display:flex;gap:8mm;align-items:flex-start}
.img{flex:0 0 78mm;height:70mm;border:1px solid #E3E8E4;display:flex;align-items:center;justify-content:center;padding:5mm}
.img img{max-width:100%;max-height:100%;object-fit:contain}
.desc{font-size:10.5pt;line-height:1.55;color:#2D3A33;margin:0 0 4mm}
table{width:100%;border-collapse:collapse;font-size:9pt}
th{background:#0F3B2A;color:#fff;text-align:start;padding:2mm 3mm;font-weight:600}
td{border-bottom:1px solid #E3E8E4;padding:1.8mm 3mm;vertical-align:top}
td.c{font-family:'DejaVu Sans Mono',monospace;font-weight:700;color:#0F3B2A;white-space:nowrap;direction:ltr;unicode-bidi:isolate}
h2{font-size:12pt;margin:7mm 0 3mm;color:#0F3B2A}
.specs td:first-child{color:#5B6660;width:45%}
.ft{position:absolute;left:15mm;right:15mm;bottom:9mm;display:flex;justify-content:space-between;gap:6mm;font-size:8pt;color:#5B6660;border-top:1px solid #E3E8E4;padding-top:3mm}
.ft b{color:#0F3B2A}
.cover{background:#0F3B2A;color:#fff;display:flex;flex-direction:column;justify-content:space-between;padding:24mm 20mm}
.cover svg{width:110mm;height:auto}
.cover h1{font-size:34pt;font-weight:300;margin:0 0 4mm}
.cover p{color:#CFE3D5;font-size:12pt;margin:0}
.cover .dr{display:inline-block;border:1px solid #9FD9A9;color:#9FD9A9;padding:2mm 4mm;font-size:9pt;margin-top:8mm}
.toc{font-size:12pt}.toc div{display:flex;justify-content:space-between;border-bottom:1px solid #E3E8E4;padding:3.2mm 0}
.sect{background:#F3F7F4;border-inline-start:4px solid #1F7A47;padding:5mm 6mm;margin:0 0 6mm}
.sect h2{margin:0 0 1mm;font-size:16pt}.sect p{margin:0;color:#5B6660;font-size:9.5pt;line-height:1.5}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:5mm}
.card{border:1px solid #E3E8E4;padding:4mm;display:flex;gap:4mm;height:52mm;overflow:hidden}
.card .ci{flex:0 0 30mm;height:30mm;display:flex;align-items:center;justify-content:center}
.card .ci img{max-width:100%;max-height:100%;object-fit:contain}
.card b{display:block;font-size:9.5pt;line-height:1.3;margin-bottom:1.5mm}
.card small{display:block;font-size:7.5pt;color:#5B6660;line-height:1.4}
.card .cc{font-family:'DejaVu Sans Mono',monospace;font-size:7.5pt;color:#1F7A47;direction:ltr;unicode-bidi:isolate}
.flow{padding-bottom:26mm}
"""


def esc(s):
    return html.escape(str(s or ""))


def doc(L, inner, title):
    d = "rtl" if L == "ar" else "ltr"
    return f'<!doctype html><html lang="{L}" dir="{d}"><head><meta charset="utf-8"><title>{esc(title)}</title><style>{CSS.replace("%(f)s", FONT_DIR)}</style></head><body>{inner}</body></html>'


def footer(L, cfg, site, url_path):
    c = cfg.get("contact", {})
    contact = " · ".join(x for x in [c.get("phone"), c.get("email")] if x) or T[L]["contact"]
    return f'<div class="ft"><span><b>SERAFIX</b> · {esc(T[L]["made"])}</span><span dir="ltr">{esc(contact)}</span><span dir="ltr">{esc((site + url_path).replace("https://", ""))}</span></div>'


def img_src(p):
    """JPEG copy on white for PDFs (Chromium passes JPEG through; PNG/WebP would be stored losslessly)."""
    src = os.path.join(ROOT, "dist", "assets", "img", p["img"])  # normalized copy made by build.py
    if not os.path.exists(src):
        src = os.path.join(ROOT, "data", "img", p["img"])
    if not os.path.exists(src):
        return ""
    d = os.path.join(CACHE, "img"); os.makedirs(d, exist_ok=True)
    out = os.path.join(d, os.path.splitext(p["img"])[0] + ".jpg")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        from PIL import Image
        im = Image.open(src).convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[3])
        bg.save(out, "JPEG", quality=84, optimize=True, progressive=False)
    return "file://" + out


def spec_rows(p, L, t):
    rows = [(t["spec"]["group"], t["cat"][p["cat"]]), (t["spec"]["hs"], ", ".join(p.get("hs") or []))]
    if p.get("thick"): rows.append((t["spec"]["thick"], f"{p['thick']} mm"))
    if p.get("net"): rows.append((t["spec"]["net"], f"{p['net']} kg"))
    rows.append((t["spec"]["origin"], t["spec"]["originVal"]))
    rows = [(a, f'<bdi dir="ltr">{esc(b)}</bdi>' if any(ch.isdigit() for ch in str(b)) else esc(b)) for a, b in rows]
    for k, lab in (("material", "material"), ("pack", "pack")):
        v = (p.get(k) or {}).get(L)
        if v: rows.append((t["spec"][lab], esc(v)))
    if p.get("moq"): rows.append((t["spec"]["moq"], esc(p["moq"])))
    return rows


def datasheet(p, L, t, cfg, site, url_path):
    var_rows = "".join(f'<tr><td class="c">{esc(v["code"])}</td><td>{esc(v["size"].get(L, ""))}</td><td dir="ltr" style="text-align:end">{esc(v.get("net") and v["net"] + " kg")}</td></tr>' for v in p["vars"])
    specs = "".join(f"<tr><td>{esc(a)}</td><td>{b}</td></tr>" for a, b in spec_rows(p, L, t))
    inner = f'''<div class="page"><div class="hd">{LOGO}<span class="k">{esc(T[L]["ds"])}</span></div>
<span class="tag">{esc(t["cat"][p["cat"]])}</span><h1>{esc(p["name"][L])}</h1>
<div class="top"><div class="img"><img src="{img_src(p)}"></div><div style="flex:1;min-width:0"><p class="desc">{esc(p["desc"][L])}</p>
<table class="specs"><tr><th colspan="2">{esc(T[L]["specs"])}</th></tr>{specs}</table></div></div>
<h2>{esc(T[L]["variants"])}</h2><table><tr><th>{esc(T[L]["codes"])}</th><th>{esc(t["spec"]["group"] if False else T[L]["variants"])}</th><th style="text-align:end">{esc(t["spec"]["net"])}</th></tr>{var_rows}</table>
{footer(L, cfg, site, url_path)}</div>'''
    return doc(L, inner, p["name"][L])


def catalogue(products, L, t, cats, cat_slug, cfg, site, intro, only_cat=None):
    sel = [c for c in cats if only_cat in (None, c) and any(p["cat"] == c for p in products)]
    pages = []
    title = T[L]["cat"] if not only_cat else t["cat"][only_cat]
    cover = f'''<div class="page cover"><div>{LOGO_W}</div><div><h1>{esc(title)}</h1><p>{esc(T[L]["edition"])} · {esc(T[L]["made"])}</p>
<div class="dr">{esc(T[L]["draft"])}</div></div><p dir="ltr">{esc(site.replace("https://", ""))}</p></div>'''
    pages.append(cover)
    if not only_cat:
        toc = "".join(f'<div><span>{esc(t["cat"][c])}</span><span>{sum(1 for p in products if p["cat"] == c)} {esc(T[L]["products"])}</span></div>' for c in sel)
        pages.append(f'<div class="page"><div class="hd">{LOGO}<span class="k">{esc(T[L]["cat"])}</span></div><h1 style="margin-bottom:6mm">{esc(T[L]["contents"])}</h1><div class="toc">{toc}</div>{footer(L, cfg, site, "/" + L + "/products/")}</div>')
    for c in sel:
        items = [p for p in products if p["cat"] == c]
        chunks, i, first = [], 0, True
        while i < len(items):
            n = 6 if first else 8
            chunks.append(items[i:i + n]); i += n; first = False
        for k, chunk in enumerate(chunks):
            cards = "".join(f'''<div class="card"><div class="ci"><img src="{img_src(p)}"></div><div style="min-width:0"><b>{esc(p["name"][L])}</b>
<span class="cc">{esc(", ".join(p["codes"][:6]) + (" …" if len(p["codes"]) > 6 else ""))}</span><small>{esc(p["desc"][L][:150])}</small></div></div>''' for p in chunk)
            sect = f'<div class="sect"><h2>{esc(t["cat"][c])}</h2><p>{esc(intro[c])}</p></div>' if k == 0 else f'<div class="sect" style="padding:3mm 6mm"><h2 style="font-size:12pt;margin:0">{esc(t["cat"][c])}</h2></div>'
            pages.append(f'''<div class="page"><div class="hd">{LOGO}<span class="k">{esc(T[L]["cat"])}</span></div>
{sect}<div class="grid">{cards}</div>{footer(L, cfg, site, "/" + L + "/products/" + cat_slug[c] + "/")}</div>''')
    return doc(L, "".join(pages), title)


def generate(products, i18n, extra, langs, cats, cat_slug, cfg, dist, pdf_url, path, site):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise ImportError("playwright not installed") from e
    from seo import SEO
    os.makedirs(CACHE, exist_ok=True)
    jobs = []
    for L, _, _ in langs:
        t = i18n[L]
        for p in products:
            h = datasheet(p, L, t, cfg, site, path(L, "product", p))
            jobs.append((pdf_url(L, "datasheet", p), h, [img_src(p)]))
        for c in [c for c in cats if any(p["cat"] == c for p in products)]:
            h = catalogue(products, L, t, cats, cat_slug, cfg, site, SEO[L]["cat_intro"], only_cat=c)
            jobs.append((pdf_url(L, "cat", c), h, [img_src(p) for p in products if p["cat"] == c]))
        h = catalogue(products, L, t, cats, cat_slug, cfg, site, SEO[L]["cat_intro"])
        jobs.append((pdf_url(L, "catalogue"), h, [img_src(p) for p in products]))
    t0 = time.time(); made = 0
    browser = None
    with sync_playwright() as pw:
        for url, h, imgs in jobs:
            key = hashlib.sha1((h + "|".join(f"{i}:{os.path.getmtime(i[7:]) if i and os.path.exists(i[7:]) else 0}" for i in imgs) + CSS).encode()).hexdigest()
            cached = os.path.join(CACHE, key + ".pdf")
            if not os.path.exists(cached):
                if browser is None:
                    browser = pw.chromium.launch(); page = browser.new_page()
                tmp = os.path.join(CACHE, "_tmp.html"); open(tmp, "w", encoding="utf-8").write(h)
                page.goto("file://" + tmp); page.wait_for_load_state("load")
                page.pdf(path=cached, format="A4", print_background=True, prefer_css_page_size=True)
                try:
                    import subprocess
                    subprocess.run(["qpdf", "--object-streams=generate", "--compress-streams=y", "--recompress-flate", "--compression-level=9", "--replace-input", cached], check=False, capture_output=True)
                except FileNotFoundError:
                    pass
                made += 1
            out = os.path.join(dist, url.lstrip("/"))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copyfile(cached, out)
        if browser: browser.close()
    print(f"PDFs: {len(jobs)} files ({made} rendered, {len(jobs) - made} from cache) in {time.time() - t0:.0f}s")
