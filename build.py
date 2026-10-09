#!/usr/bin/env python3
"""SERAFIX static site builder.

Reads data/ (products, texts), templates/ and static/, writes the finished site to dist/.
Every product gets its own page in 4 languages with full SEO (title, description,
canonical, hreflang, Schema.org JSON-LD, sitemap).   Usage:  python build.py
"""
import json, os, re, shutil, sys, unicodedata
from urllib.parse import quote
from datetime import date
from jinja2 import Environment, FileSystemLoader, select_autoescape
from seo import SEO, CAT_SLUG, CATS

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
CFG = json.load(open(os.path.join(ROOT, "site.json"), encoding="utf-8"))
SITE = CFG["site_url"].rstrip("/")
from urllib.parse import urlparse
BASE = urlparse(SITE).path.rstrip("/")  # e.g. "/serafix" on GitHub project pages, "" on own domain
I18N = json.load(open(os.path.join(ROOT, "data", "i18n.json"), encoding="utf-8"))
def load_dir(d):
    out = []
    for f in sorted(os.listdir(os.path.join(ROOT, "data", d))):
        if f.endswith(".json"):
            x = json.load(open(os.path.join(ROOT, "data", d, f), encoding="utf-8"))
            x.setdefault("slug", f[:-5])
            out.append(x)
    return sorted(out, key=lambda x: (x.get("order") or 9999, x["slug"]))


PRODUCTS = load_dir("products")
GUIDES = load_dir("guides")
TOOLING = sorted(json.load(open(os.path.join(ROOT, "data", "tooling.json"), encoding="utf-8")), key=lambda x: x.get("order", 999))
LEGAL = json.load(open(os.path.join(ROOT, "data", "legal.json"), encoding="utf-8"))
for _i, _p in enumerate(PRODUCTS):
    _p["img"] = os.path.basename(_p.get("img") or "")
    _p.setdefault("id", 100000 + _i)
    _p["variants"] = len(_p.get("vars") or []) or 1
LANGS = [("tr", "TR", "Türkçe"), ("en", "EN", "English"), ("ru", "RU", "Русский"), ("ar", "AR", "العربية")]
LOCALE = {"tr": "tr_TR", "en": "en_US", "ru": "ru_RU", "ar": "ar_AR"}
DEFAULT = CFG.get("default_lang", "en")
EXTRA = {
 "tr": {"toolPhoto": "Kalıphanemizde tel erozyon ile kalıp parçası işleme", "emptyTitle": "Bu kategorideki ürünler yakında eklenecek", "emptyText": "Yağmur olukları ve özel sera profilleri için ölçü ve kesitinizi gönderin; ihtiyacınıza uygun profili birlikte belirleyelim.", "toolTag": "KALIP TASARIMI VE ÜRETİM", "toolTitle": "Kendi kalıphanemizden seri üretime", "toolLead": "Kalıplarımızı kendi kalıphanemizde tasarlıyor ve üretiyoruz; aşağıda parçalarımızı ürettiğimiz pres kalıplarından örnekler var. Çiziminizi veya numunenizi gönderin, parçanızın kalıbını biz yapalım ve seri üretime alalım.", "toolProc": {"progressive": "Progresif kalıp", "pierce": "Delme", "cut": "Kesme", "bend": "Büküm", "form": "Şekillendirme", "flatten": "Boru ezme"}, "toolNote": "Görselleri büyütmek için üzerine tıklayın. Kalıp çizimleri gizlidir ve paylaşılmaz.", "qAddShort": "Ekle", "qPick": "Ölçü seçip listeye ekleyin", "skip": "İçeriğe geç", "menu": "Menü", "qAdd": "Teklif listesine ekle", "qAdded": "Listede", "qTitle": "Teklif listeniz", "qClear": "Listeyi temizle",
        "qRemove": "Kaldır", "qQty": "Adet", "reqDrawing": "Teknik çizim iste", "reqCad": "3D CAD dosyası iste", "updated": "Son güncelleme",
        "guideTitle": "Sera Rehberi: Teknik Yazılar ve Seçim Kılavuzları | SERAFIX", "guideDesc": "Sera havalandırma, gölgeleme, kelepçe seçimi, galvaniz koruma ve ithalat üzerine sera kurucuları ve distribütörler için pratik rehberler.",
        "months": ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]},
 "en": {"toolPhoto": "Wire EDM machining of die components in our tool room", "emptyTitle": "Products in this category are coming soon", "emptyText": "Send us the size and cross-section you need for rain gutters or special greenhouse profiles, and we will work out the right profile with you.", "toolTag": "TOOLING & PRODUCTION", "toolTitle": "In-house tooling, from die to series production", "toolLead": "We design and build our dies in our own tool room. Below are examples of the press dies we use to make our parts. Send your drawing or sample and we will build the die for your part and take it into series production.", "toolProc": {"progressive": "Progressive die", "pierce": "Piercing", "cut": "Trimming", "bend": "Bending", "form": "Forming", "flatten": "Pipe flattening"}, "toolNote": "Click an image to enlarge. Die drawings are confidential and are not shared.", "qAddShort": "Add", "qPick": "Choose sizes to add", "skip": "Skip to content", "menu": "Menu", "qAdd": "Add to quote list", "qAdded": "In list", "qTitle": "Your quote list", "qClear": "Clear list",
        "qRemove": "Remove", "qQty": "Qty", "reqDrawing": "Request technical drawing", "reqCad": "Request 3D CAD file", "updated": "Last updated",
        "guideTitle": "Greenhouse Guide: Technical Articles & Buying Guides | SERAFIX", "guideDesc": "Practical guides for greenhouse builders and distributors on ventilation, shading, clamp selection, galvanizing and sourcing parts from Türkiye.",
        "months": ["January","February","March","April","May","June","July","August","September","October","November","December"]},
 "ru": {"toolPhoto": "Электроэрозионная обработка деталей штампа в нашем инструментальном цехе", "emptyTitle": "Продукция этой категории скоро появится", "emptyText": "Пришлите размеры и сечение нужного водосточного желоба или специального профиля, и мы вместе подберём подходящий профиль.", "toolTag": "ШТАМПЫ И ПРОИЗВОДСТВО", "toolTitle": "Собственные штампы: от проекта до серии", "toolLead": "Мы проектируем и изготавливаем штампы в собственном инструментальном цехе. Ниже примеры штампов, на которых мы производим наши детали. Пришлите чертёж или образец, и мы изготовим штамп для вашей детали и запустим её в серийное производство.", "toolProc": {"progressive": "Последовательный штамп", "pierce": "Пробивка", "cut": "Обрезка", "bend": "Гибка", "form": "Формовка", "flatten": "Сплющивание труб"}, "toolNote": "Нажмите на изображение, чтобы увеличить. Чертежи штампов конфиденциальны и не передаются.", "qAddShort": "Добавить", "qPick": "Выберите размеры", "skip": "Перейти к содержанию", "menu": "Меню", "qAdd": "Добавить в запрос", "qAdded": "В списке", "qTitle": "Ваш список для запроса", "qClear": "Очистить список",
        "qRemove": "Удалить", "qQty": "Кол-во", "reqDrawing": "Запросить чертёж", "reqCad": "Запросить 3D CAD", "updated": "Обновлено",
        "guideTitle": "Справочник по теплицам: статьи и руководства | SERAFIX", "guideDesc": "Практические руководства для строителей теплиц и дистрибьюторов: проветривание, зашторивание, выбор хомутов, оцинковка и закупка комплектующих в Турции.",
        "months": ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]},
 "ar": {"toolPhoto": "تشغيل قطع القوالب بالتآكل الكهربائي السلكي في ورشة القوالب لدينا", "emptyTitle": "ستتم إضافة منتجات هذه الفئة قريباً", "emptyText": "أرسل لنا المقاسات والمقطع المطلوب لمزاريب الأمطار أو البروفيلات الخاصة، وسنحدد معك البروفيل المناسب.", "toolTag": "القوالب والإنتاج", "toolTitle": "قوالبنا الخاصة: من التصميم إلى الإنتاج الكمي", "toolLead": "نصمم قوالبنا ونصنعها في ورشة القوالب الخاصة بنا. فيما يلي نماذج من قوالب المكابس التي ننتج بها قطعنا. أرسل رسمك الفني أو عينة، وسنصنع القالب لقطعتك ونبدأ إنتاجها الكمي.", "toolProc": {"progressive": "قالب تدريجي", "pierce": "ثقب", "cut": "قص", "bend": "ثني", "form": "تشكيل", "flatten": "سحق الأنابيب"}, "toolNote": "انقر على الصورة لتكبيرها. رسومات القوالب سرية ولا تتم مشاركتها.", "qAddShort": "أضف", "qPick": "اختر المقاسات للإضافة", "skip": "انتقل إلى المحتوى", "menu": "القائمة", "qAdd": "أضف إلى قائمة عرض السعر", "qAdded": "في القائمة", "qTitle": "قائمة طلب عرض السعر", "qClear": "مسح القائمة",
        "qRemove": "إزالة", "qQty": "الكمية", "reqDrawing": "اطلب الرسم الفني", "reqCad": "اطلب ملف CAD ثلاثي الأبعاد", "updated": "آخر تحديث",
        "guideTitle": "دليل البيوت المحمية: مقالات فنية وأدلة شراء | SERAFIX", "guideDesc": "أدلة عملية لشركات إنشاء البيوت المحمية والموزعين حول التهوية والتظليل واختيار المشابك والجلفنة واستيراد القطع من تركيا.",
        "months": ["يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"]},
}
GREEN_WORD = ("sera", "greenhouse", "теплич", "البيوت المحمية")

env = Environment(loader=FileSystemLoader(os.path.join(ROOT, "templates")), autoescape=select_autoescape(["html"]))


def fmt(s, n):
    return str(s).replace("{n}", str(n))


def slugify(s):
    s = unicodedata.normalize("NFKD", s.replace("ı", "i").replace("İ", "i")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")




NAME_COUNT = {}
for _p in PRODUCTS:
    for _l in ("tr", "en", "ru", "ar"):
        NAME_COUNT[(_l, _p["name"][_l])] = NAME_COUNT.get((_l, _p["name"][_l]), 0) + 1


def path(lang, key, p=None, cat=None):
    if key == "home": return f"/{lang}/"
    if key == "products": return f"/{lang}/products/"
    if key == "cat": return f"/{lang}/products/{CAT_SLUG[cat]}/"
    if key == "product": return f"/{lang}/products/{CAT_SLUG[p['cat']]}/{p['slug']}/"
    if key == "guide": return f"/{lang}/guide/"
    if key == "article": return f"/{lang}/guide/{p['slug']}/"
    return f"/{lang}/{key}/"


def nav_style(on, last=False):
    base = "display: flex; align-items: center; padding: 0 13px; min-height: 76px; box-sizing: border-box; text-decoration: none; border-inline-start: 1px solid #E3E8E4; border-bottom: 3px solid "
    return base + ("#1F7A47; color: #1F7A47" if on else "transparent; color: #3F4A44") + ("; border-inline-end: 1px solid #E3E8E4" if last else "")


def cat_style(on):
    return ("display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; min-height: 112px; padding: 16px 10px; border: none; "
            "border-inline-start: 1px solid #E3E8E4; border-top: 3px solid " + ("#1F7A47" if on else "transparent") + "; background: " + ("#EEF5F0" if on else "#FFFFFF")
            + "; color: " + ("#1F7A47" if on else "#3F4A44") + "; font-size: 13px; font-weight: 600; line-height: 1.3; text-align: center; text-decoration: none")


def clip(s, n=158):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


IMG_OK = (".webp", ".svg")


def safe_name(name):
    stem = os.path.splitext(name)[0]
    stem = unicodedata.normalize("NFKD", stem.replace("ı", "i").replace("İ", "I")).encode("ascii", "ignore").decode()
    return (re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "img") + ".webp"


def normalize_images(folder):
    """Panel uploads may be JPG/PNG/TIF, huge, CMYK or have spaces/Turkish letters in the name.
    Convert every such file in dist to a web-safe .webp (max 1600 px) and return {old: new} names."""
    from PIL import Image
    renamed = {}
    for root, _, files in os.walk(folder):
        for f in files:
            src = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            if ext == ".svg":
                continue
            try:
                im = Image.open(src)
                big = max(im.size) > 1600
            except Exception:
                continue
            if ext in IMG_OK and not big and safe_name(f) == f:
                continue
            if im.mode == "CMYK":
                im = im.convert("RGB")
            im = im.convert("RGBA") if ("A" in im.getbands() or im.mode == "P") else im.convert("RGB")
            im.thumbnail((1600, 1600))
            new = safe_name(f)
            im.save(os.path.join(root, new), "WEBP", quality=86, method=6)
            if new != f:
                os.remove(src)
            rel_old = os.path.relpath(src, folder).replace(os.sep, "/")
            renamed[rel_old] = os.path.relpath(os.path.join(root, new), folder).replace(os.sep, "/")
    return renamed


IMG_MAP = {}


def img_ref(v):
    """Panel may store '/assets/img/x.jpg', '/data/img/tooling/x.jpg' or 'x.jpg'; return the mapped path under assets/img."""
    v = (v or "").strip()
    if "img/" in v:
        v = v.split("img/", 1)[1]
    v = v.lstrip("/")
    return IMG_MAP.get(v, v)


def img_url(p):
    return "/assets/img/" + p["img"]


def card(p, L, t):
    return {"url": path(L, "product", p), "img": img_url(p), "name": p["name"][L], "alt": f"{p['name'][L]} — {t['cat'][p['cat']]}",
            "cat": t["cat"][p["cat"]], "multi": p["variants"] > 1, "badge": fmt(t["sizes"], p["variants"]),
            "search": " ".join([p["name"][L], p["name"]["en"], p["name"]["tr"], " ".join(p["codes"])]).lower(), "q": qdata(p, L)}


def qdata(p, L):
    return json.dumps({"id": p["slug"], "n": p["name"][L], "c": ", ".join(p["codes"]), "u": path(L, "product", p), "i": img_url(p)}, ensure_ascii=False)


def pdf_url(L, kind, x=None):
    if kind == "datasheet": return f"/assets/pdf/{L}/{x['slug']}.pdf"
    if kind == "catalogue": return f"/assets/pdf/SERAFIX-Catalogue-{L.upper()}.pdf"
    if kind == "cat": return f"/assets/pdf/{L}/category-{CAT_SLUG[x]}.pdf"


def link_tokens(html, L, u):
    html = re.sub(r"\{cat:(\w+)\}", lambda m: u["cat"].get(m.group(1), u["products"]), html)
    pages = {"oem": u["oem"], "quality": u["quality"], "downloads": u["downloads"], "contact": "#iletisim", "privacy": u["privacy"], "cookies": u["cookies"], "products": u["products"]}
    return re.sub(r"\{page:(\w+)\}", lambda m: pages.get(m.group(1), u["home"]), html)


def fill_legal(text):
    lg = CFG.get("legal", {})
    c = CFG.get("contact", {})
    vals = {"company": lg.get("company") or "[Şirket unvanı / Company name]", "address": lg.get("address") or c.get("address") or "[Adres / Address]",
            "email": c.get("email") or "[e-posta / email]", "phone": c.get("phone") or "[Telefon / Phone]", "tax_office": lg.get("tax_office") or "[Vergi dairesi]",
            "tax_no": lg.get("tax_no") or "[Vergi no]", "mersis": lg.get("mersis") or "[MERSİS no]", "registry": lg.get("registry") or "[Ticaret sicil no]",
            "responsible": lg.get("responsible") or "[Sorumlu kişi]"}
    for k, v in vals.items():
        text = text.replace("{" + k + "}", v)
    return text


def date_text(d, L):
    y, m, dd = d.split("-")
    mon = EXTRA[L]["months"][int(m) - 1]
    if L == "en": return f"{mon} {int(dd)}, {y}"
    return f"{int(dd)} {mon} {y}"


def guide_card(g, L):
    return {"url": path(L, "article", g), "title": g["title"][L], "summary": g["summary"][L], "tag": g["tag"][L]}


def wa_link(text=""):
    num = re.sub(r"\D", "", CFG["contact"].get("whatsapp", ""))
    if not num:
        return "#iletisim"
    return f"https://wa.me/{num}" + (f"?text={quote(text)}" if text else "")


def org_ld(L):
    o = {"@context": "https://schema.org", "@type": "Organization", "@id": SITE + "/#org", "name": "SERAFIX", "url": SITE + "/",
         "logo": SITE + "/assets/logo/serafix-symbol-color-512.png", "description": SEO[L]["org_desc"]}
    c = CFG["contact"]
    if c.get("email") or c.get("phone"):
        o["contactPoint"] = [{"@type": "ContactPoint", "contactType": "sales", "email": c.get("email") or None, "telephone": c.get("phone") or None,
                              "availableLanguage": ["Turkish", "English", "Russian", "Arabic"]}]
    same = [v for v in CFG.get("social", {}).values() if v]
    if same: o["sameAs"] = same
    return o


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}


def dumps(o):
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


PAGES = []  # (key, cat, product) – one entry per logical page


def render(L, key, cat=None, p=None):
    t = dict(I18N[L]); t.update(EXTRA[L])
    S = SEO[L]
    u = {"home": path(L, "home"), "products": path(L, "products"), "oem": path(L, "oem"), "quality": path(L, "quality"),
         "downloads": path(L, "downloads"), "guide": path(L, "guide"), "privacy": path(L, "privacy"), "cookies": path(L, "cookies"),
         "imprint": path(L, "imprint"), "cat": {c: path(L, "cat", cat=c) for c in CATS}}
    here = {lg: path(lg, key, p, cat) for lg, _, _ in LANGS}
    canonical = SITE + here[L]
    alternates = [{"hreflang": lg, "href": SITE + here[lg]} for lg, _, _ in LANGS] + [{"hreflang": "x-default", "href": SITE + here[DEFAULT]}]
    langs = [{"code": lg, "label": lb, "title": ti, "url": here[lg],
              "style": "display: flex; width: 100%; justify-content: space-between; align-items: center; gap: 12px; height: 44px; padding: 0 16px; font-size: 14px; text-decoration: none; "
              + ("background: #EEF5F0; color: #1F7A47; font-weight: 700" if lg == L else "background: #FFFFFF; color: #11261C")} for lg, lb, ti in LANGS]
    in_products = key in ("products", "cat", "product")
    ctx = dict(lang=L, dir="rtl" if L == "ar" else "ltr", t=t, u=u, langs=langs, curLang=L.upper(), canonical=canonical, alternates=alternates,
               ogLocale=LOCALE[L], sep="‹" if L == "ar" else "›", arrow="‹" if L == "ar" else "›", formAction=CFG.get("form_action", ""),
               navSt={"products": nav_style(in_products), "oem": nav_style(key == "oem"), "quality": nav_style(key == "quality"),
                      "downloads": nav_style(key == "downloads"), "guide": nav_style(key in ("guide", "article")), "plain": nav_style(False), "last": nav_style(False, True)},
               cpSt={c: cat_style(c == cat) for c in CATS}, waHref=wa_link(), refSlots=range(6), gridPad="80px 24px 0",
               oemSteps=[{"n": i + 1, "t": x["t"], "d": x["d"]} for i, x in enumerate(t["oem"]["steps"])],
               qcSteps=[{"n": f"{i + 1:02d}", "t": x["t"], "d": x["d"]} for i, x in enumerate(t["qual"]["qc"])],
               socials=[{"name": n, "url": CFG.get("social", {}).get(k)} for k, n in (("linkedin", "LinkedIn"), ("youtube", "YouTube"), ("instagram", "Instagram")) if CFG.get("social", {}).get(k)],
               legal=LEGAL, analytics=CFG.get("analytics_id", ""), homeGuides=[guide_card(g, L) for g in GUIDES[:3]],
               jsI18n=json.dumps({k: t[k] for k in ("qAdd", "qAdded", "qRemove", "qQty", "qAddShort")}, ensure_ascii=False).replace("'", "&#39;"))
    jsonld = []
    meta = {"image": SITE + "/assets/og-serafix.png"}
    home_crumb = (t["nav"]["home"], u["home"])

    if key == "home":
        body = "_home.html"
        items = PRODUCTS[:10]
        ctx.update(products=[card(x, L, t) for x in items], listTitle=t["ourProducts"], totalLabel=fmt(t["count"], len(PRODUCTS)),
                   hasMore=True, moreLabel=fmt(t["more"], len(PRODUCTS) - len(items)), isFiltered=False)
        slides = [card(x, L, t) for x in PRODUCTS if x.get("img")]
        ctx["heroSlides"] = slides
        ctx["heroData"] = dumps([{"n": x["name"], "c": x["cat"], "u": x["url"]} for x in slides])
        meta.update(title=S["home_title"], desc=S["home_desc"])
        jsonld += [org_ld(L), {"@context": "https://schema.org", "@type": "WebSite", "name": "SERAFIX", "url": SITE + "/", "inLanguage": L, "publisher": {"@id": SITE + "/#org"}}]
    elif key in ("products", "cat"):
        body = "_listpage.html"
        items = [x for x in PRODUCTS if cat is None or x["cat"] == cat]
        ctx.update(products=[card(x, L, t) for x in items], listTitle=t["cat"][cat] if cat else t["ourProducts"],
                   totalLabel=fmt(t["count"], len(items)) if items else "", hasMore=False, isFiltered=bool(cat), gridH1=True,
                   listIntro=S["cat_intro"][cat] if cat else S["products_desc"], gridPad="56px 24px 0", searchable=True)
        if cat:
            cn = t["cat"][cat]
            title = (cn + " | SERAFIX") if any(w in cn.lower() for w in GREEN_WORD) else S["cat_title"].format(cat=cn)
            meta.update(title=title, desc=clip(S["cat_intro"][cat]))
            if not items:
                meta["robots"] = "noindex,follow"
            jsonld.append(crumbs_ld([home_crumb, (t["nav"]["products"], u["products"]), (cn, u["cat"][cat])]))
        else:
            meta.update(title=S["products_title"], desc=clip(S["products_desc"]))
            jsonld.append(crumbs_ld([home_crumb, (t["nav"]["products"], u["products"])]))
        jsonld.append({"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": SITE + path(L, "product", x), "name": x["name"][L]} for i, x in enumerate(items)]})
    elif key == "product":
        body = "_detail.html"
        show_rest = L in ("tr", "en")
        specs = [{"l": t["spec"]["group"], "v": t["cat"][p["cat"]], "style": "color: #11261C; font-weight: 600"},
                 {"l": t["spec"]["codes"], "v": ", ".join(p["codes"]), "style": "color: #11261C; font-weight: 600; font-family: ui-monospace, Menlo, monospace; direction: ltr; text-align: start"},
                 {"l": t["spec"]["hs"], "v": ", ".join(p.get("hs") or []), "style": "color: #11261C; font-weight: 600; font-family: ui-monospace, Menlo, monospace; direction: ltr; text-align: start"}]
        ok = "color: #11261C; font-weight: 600"; ph = "color: #8A6A1F; font-weight: 600"
        if p.get("thick"): specs.append({"l": t["spec"]["thick"], "v": f"{p['thick']} mm", "style": ok})
        if p.get("net"): specs.append({"l": t["spec"]["net"], "v": f"{p['net']} kg", "style": ok})
        specs += [{"l": t["spec"]["unit"], "v": t["spec"]["unitVal"], "style": ok}, {"l": t["spec"]["origin"], "v": t["spec"]["originVal"], "style": ok},
                  {"l": t["spec"]["material"], "v": p.get("material", {}).get(L) or t["spec"]["materialVal"], "style": ok if p.get("material") else ph},
                  {"l": t["spec"]["pack"], "v": p.get("pack", {}).get(L) or t["spec"]["packVal"], "style": ok if p.get("pack") else ph},
                  {"l": t["spec"]["moq"], "v": p.get("moq") or t["spec"]["moqVal"], "style": ok if p.get("moq") else ph}]
        name = p["name"][L]
        quote_text = f"{name} ({', '.join(p['codes'])})"
        d = {"name": name, "cat": t["cat"][p["cat"]], "img": img_url(p), "alt": f"{name} — SERAFIX {p['codes'][0]}", "desc": p["desc"][L],
             "vars": [{"code": v["code"], "size": v["size"].get(L, ""), "rest": (v["rest"].get(L, "") if show_rest and v["rest"].get(L, "") != p["desc"][L] else ""),
                      "q": json.dumps({"id": p["slug"] + ":" + v["code"], "n": p["name"][L] + (" — " + v["size"].get(L, "") if v["size"].get(L) and len(p["vars"]) > 1 else ""),
                                       "c": v["code"], "u": path(L, "product", p), "i": img_url(p)}, ensure_ascii=False)} for v in p["vars"]],
             "multi": len(p["vars"]) > 1,
             "variantCount": fmt(t["variantCount"], len(p["vars"])), "specs": specs, "catUrl": u["cat"][p["cat"]],
             "quoteText": quote_text, "waUrl": wa_link(quote_text + " — " + canonical), "pdf": pdf_url(L, "datasheet", p), "q": qdata(p, L)}
        rel = [x for x in PRODUCTS if x["cat"] == p["cat"] and x["id"] != p["id"]][:4]
        ctx.update(d=d, related=[card(x, L, t) for x in rel])
        nm = name if NAME_COUNT[(L, name)] == 1 else f"{name} {p['codes'][0]}"
        title = S["prod_title"].format(name=nm, cat=t["cat"][p["cat"]])
        if len(title) > 65: title = f"{nm} | SERAFIX"
        meta.update(title=title, desc=clip(p["desc"][L], 158 - len(S["prod_suffix"])) + S["prod_suffix"],
                    image=SITE + img_url(p), ogType="product")
        prod = {"@context": "https://schema.org", "@type": "Product", "name": name, "description": p["desc"][L], "image": [SITE + img_url(p)],
                "sku": p["codes"][0], "mpn": p["codes"][0], "brand": {"@type": "Brand", "name": "SERAFIX"}, "manufacturer": {"@id": SITE + "/#org"},
                "category": t["cat"][p["cat"]], "url": canonical, "countryOfOrigin": {"@type": "Country", "name": "TR"},
                "additionalProperty": [{"@type": "PropertyValue", "name": "HS code", "value": ", ".join(p.get("hs") or [])}]}
        if p.get("thick"): prod["additionalProperty"].append({"@type": "PropertyValue", "name": "Sheet thickness", "value": p["thick"], "unitCode": "MMT"})
        if p.get("net"): prod["weight"] = {"@type": "QuantitativeValue", "value": p["net"], "unitCode": "KGM"}
        if len(p["vars"]) > 1:
            prod["hasVariant"] = [{"@type": "Product", "name": f"{name} {v['size'].get(L, '')}".strip(), "sku": v["code"]} for v in p["vars"]]
        jsonld += [prod, crumbs_ld([home_crumb, (t["nav"]["products"], u["products"]), (t["cat"][p["cat"]], u["cat"][p["cat"]]), (name, here[L])])]
    elif key == "guide":
        body = "_guide_index.html"
        ctx["guides"] = [guide_card(g, L) for g in GUIDES]
        meta.update(title=t["guideTitle"], desc=t["guideDesc"])
        jsonld.append(crumbs_ld([home_crumb, (t["nav"]["guide"], here[L])]))
        jsonld.append({"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": SITE + path(L, "article", g), "name": g["title"][L]} for i, g in enumerate(GUIDES)]})
    elif key == "article":
        body = "_guide.html"
        g = p
        ctx["g"] = {"title": g["title"][L], "summary": g["summary"][L], "tag": g["tag"][L], "date": g["date"], "dateText": date_text(g["date"], L),
                    "body": link_tokens(g["body"][L], L, u), "catLinks": [{"name": t["cat"][c], "url": u["cat"][c]} for c in g.get("cats", [])]}
        ctx["related"] = [card(x, L, t) for x in PRODUCTS if x["cat"] in g.get("cats", [])][:4]
        ctx["others"] = [guide_card(x, L) for x in GUIDES if x["slug"] != g["slug"]][:3]
        meta.update(title=g["title"][L] + " | SERAFIX" if len(g["title"][L]) <= 55 else g["title"][L], desc=g["desc"][L], ogType="article")
        jsonld.append({"@context": "https://schema.org", "@type": "Article", "headline": g["title"][L], "description": g["desc"][L], "inLanguage": L,
                       "datePublished": g["date"], "dateModified": g.get("updated", g["date"]), "author": {"@type": "Organization", "name": "SERAFIX"},
                       "publisher": {"@type": "Organization", "name": "SERAFIX", "logo": {"@type": "ImageObject", "url": SITE + "/assets/logo/serafix-symbol-color-512.png"}},
                       "mainEntityOfPage": canonical, "image": SITE + "/assets/og-serafix.png"})
        jsonld.append(crumbs_ld([home_crumb, (t["nav"]["guide"], u["guide"]), (g["title"][L], here[L])]))
    elif key in ("privacy", "cookies", "imprint"):
        body = "_legal.html"
        doc = LEGAL[key]
        ctx["doc"] = {"title": doc["title"][L], "body": link_tokens(fill_legal(doc["body"][L]), L, u), "updated": t["updated"] + ": " + date_text("2026-10-08", L)}
        meta.update(title=doc["title"][L] + " | SERAFIX", desc=doc["desc"][L])
        jsonld.append(crumbs_ld([home_crumb, (doc["title"][L], here[L])]))
    else:
        body = f"_{key}.html"
        meta.update(title=S[f"{key}_title"], desc=S[f"{key}_desc"])
        if key == "oem":
            ctx["capImgs"] = [img_ref(i) for i in json.load(open(os.path.join(ROOT, "data", "oem_caps.json"), encoding="utf-8")).get("images", [])]
            ctx["tooling"] = [{"img": "/assets/img/" + x["img"], "title": x["title"][L], "proc": [t["toolProc"].get(k, k) for k in x.get("process", [])]} for x in TOOLING]
        if key == "downloads":
            ctx["dlCatalogs"] = [{"code": lb, "title": t["dl"]["general"] + " — " + ti, "meta": fmt(t["dl"]["meta"].replace("103", "{n}"), len(PRODUCTS)),
                                  "href": pdf_url(lg, "catalogue"), "target": "_blank"} for lg, lb, ti in LANGS]
            ctx["dlGroups"] = [{"name": t["cat"][c], "count": fmt(t["dl"]["count"], sum(1 for x in PRODUCTS if x["cat"] == c)),
                                "pdf": pdf_url(L, "cat", c), "url": u["cat"][c]} for c in CATS if any(x["cat"] == c for x in PRODUCTS)]
        jsonld.append(crumbs_ld([home_crumb, (t["nav2"][key], here[L])]))

    ctx.update(body=body, meta=meta, jsonld=[dumps(j) for j in jsonld])
    html = env.get_template("page.html").render(**ctx)
    html = fill_placeholders(html)
    out = os.path.join(DIST, here[L].strip("/"), "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    return here


INDEXING = CFG.get("indexing", True)  # false = hide the whole site from search engines (pre-launch)


def with_base(html):
    if not INDEXING:
        html = re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex,nofollow">', html)
    if not BASE:
        return html
    return re.sub(r'(href|src|action)="/(?!/)', lambda m: f'{m.group(1)}="{BASE}/', html).replace("'/assets/", f"'{BASE}/assets/")


def fill_placeholders(html):
    c = CFG["contact"]
    rep = {"[TELEFON]": c.get("phone"), "[WHATSAPP]": c.get("whatsapp"), "[E-POSTA]": c.get("email"), "[ADRES]": c.get("address"), "[ÇALIŞMA SAATLERİ]": c.get("hours")}
    for k, v in rep.items():
        if v: html = html.replace(k, v)
    html = with_base(html)
    html = html.replace('class="lead"', f'class="lead" data-mailto="{c.get("email", "")}"')
    for k, v in (CFG.get("social") or {}).items():
        if v: html = html.replace(f'href="#" aria-label="{k.capitalize() if k != "youtube" else "YouTube"}"'.replace("Linkedin", "LinkedIn"), f'href="{v}" target="_blank" rel="noopener" aria-label="{"LinkedIn" if k == "linkedin" else "YouTube" if k == "youtube" else "Instagram"}"')
    return html


def main():
    if os.path.isdir(DIST): shutil.rmtree(DIST)
    shutil.copytree(os.path.join(ROOT, "static"), DIST)
    shutil.copytree(os.path.join(ROOT, "data", "img"), os.path.join(DIST, "assets", "img"))
    IMG_MAP.update(normalize_images(os.path.join(DIST, "assets", "img")))
    for p in PRODUCTS:
        p["img"] = IMG_MAP.get(p["img"], p["img"])
    for x in TOOLING:
        x["img"] = img_ref(x.get("img"))
    jobs = [("home", None, None), ("products", None, None)] + [("cat", c, None) for c in CATS] + [("product", None, p) for p in PRODUCTS] + \
           [("oem", None, None), ("quality", None, None), ("downloads", None, None), ("guide", None, None)] + \
           [("article", None, g) for g in GUIDES] + [("privacy", None, None), ("cookies", None, None), ("imprint", None, None)]
    urls = []
    for key, cat, p in jobs:
        for L, _, _ in LANGS:
            here = render(L, key, cat, p)
        if not (key == "cat" and not any(x["cat"] == cat for x in PRODUCTS)):
            urls.append((here, key))
    # sitemap with hreflang alternates
    today = date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for here, key in urls:
        pr = {"home": "1.0", "products": "0.9", "cat": "0.8", "product": "0.7", "guide": "0.7", "article": "0.7", "privacy": "0.2", "cookies": "0.2", "imprint": "0.2"}.get(key, "0.6")
        for L, _, _ in LANGS:
            sm.append(f"<url><loc>{SITE}{here[L]}</loc><lastmod>{today}</lastmod><priority>{pr}</priority>")
            for lg, _, _ in LANGS:
                sm.append(f'<xhtml:link rel="alternate" hreflang="{lg}" href="{SITE}{here[lg]}"/>')
            sm.append(f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{here[DEFAULT]}"/></url>')
    sm.append("</urlset>")
    open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm))
    open(os.path.join(DIST, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: {BASE}/admin/\n" + (f"\nSitemap: {SITE}/sitemap.xml\n" if INDEXING else ""))
    # admin panel config
    os.makedirs(os.path.join(DIST, "admin"), exist_ok=True)
    adm = open(os.path.join(ROOT, "templates", "admin_config.yml"), encoding="utf-8").read()
    adm = adm.replace("__REPO__", CFG.get("github_repo", "OWNER/serafix-site")).replace("__SITE__", SITE).replace("public_folder: /assets/img", f"public_folder: {BASE}/assets/img")
    open(os.path.join(DIST, "admin", "config.yml"), "w", encoding="utf-8").write(adm)
    # root language chooser (x-default)
    root = open(os.path.join(ROOT, "templates", "root.html"), encoding="utf-8").read().replace("{{SITE}}", SITE)
    root = with_base(root).replace("location.replace('/' + pick", f"location.replace('{BASE}/' + pick")
    p404 = os.path.join(DIST, "404.html")
    open(p404, "w", encoding="utf-8").write(with_base(open(p404, encoding="utf-8").read()))
    open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(root)
    if "--no-pdf" not in sys.argv:
        try:
            import pdfs
            pdfs.generate(PRODUCTS, I18N, EXTRA, LANGS, CATS, CAT_SLUG, CFG, DIST, pdf_url, path, SITE)
        except ImportError as e:
            print("PDF step skipped:", e)
    n = sum(len(f) for _, _, f in os.walk(DIST) if True)
    print(f"built {len(urls) * len(LANGS)} pages, {n} files -> dist/")


if __name__ == "__main__":
    main()
