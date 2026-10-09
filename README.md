# SERAFIX web sitesi

4 dilli (TR, EN, RU, AR), SEO'su içine gömülü statik kurumsal site ve yönetim paneli.
`python build.py` komutu `dist/` klasörüne hazır siteyi üretir:

- 508 sayfa: ana sayfa, tüm ürünler, 9 kategori, 103 ürün, OEM, Kalite, İndirmeler,
  Sera Rehberi (6 yazı), Gizlilik/KVKK, Çerez politikası, Künye — her biri 4 dilde
- 452 PDF: her ürün için 4 dilde teknik föy, 4 dilde genel katalog, her kategori için katalog
- `sitemap.xml`, `robots.txt`, `/admin/` yönetim paneli

## Klasörler

| Klasör / dosya | Ne işe yarar |
|---|---|
| `site.json` | Alan adı, iletişim, form adresi, Analytics, sosyal medya, firma (yasal) bilgileri |
| `data/products/*.json` | Her ürün ayrı dosya: ad, açıklama, kodlar, ölçüler, malzeme, paketleme, MOQ (4 dil) |
| `data/guides/*.json` | Sera Rehberi yazıları (4 dil) |
| `data/img/` | Ürün görselleri |
| `data/i18n.json` | Sitedeki sabit yazılar (menü, başlıklar, butonlar) |
| `data/legal.json` | Gizlilik/KVKK, çerez ve künye metinleri — **yayından önce avukata kontrol ettirin** |
| `seo.py` | Sayfa başlıkları, Google açıklamaları, kategori tanıtım metinleri |
| `templates/` | Sayfa tasarımı |
| `pdfs.py`, `fonts-pdf/` | PDF teknik föy ve katalog üretimi |
| `static/` | Logo, favicon, fontlar, site.js, yönetim paneli |
| `.github/workflows/deploy.yml` | GitHub'a her kayıtta siteyi ve PDF'leri kurup yayınlar |

## Yayına alma (GitHub Pages)

1. GitHub'da depo açın (ör. `serafix-site`) ve bu klasörün içeriğini yükleyin.
2. `site.json` → `github_repo`: `KULLANICI/serafix-site`, `site_url`: sitenin adresi.
3. Depoda **Settings → Pages → Source: GitHub Actions**.
4. Kendi alan adınız: Settings → Pages → Custom domain; `site_url` = `https://www.serafix.com`.

## Google'dan gizleme (yayın öncesi)

`site.json` → `"indexing": false` iken tüm sayfalar `noindex` olur ve site haritası robots.txt'de bildirilmez.
Site hazır olunca `true` yapın.

## Yönetim paneli (`/admin/`)

Ürün ekleme/silme, fotoğraf yükleme, rehber yazıları ve site ayarları tarayıcıdan yapılır.
Kaydedilen her değişiklik GitHub'a yazılır, site 2–4 dakika içinde kendini yeniden kurar
(yeni ürünün 4 dildeki sayfası, PDF föyü ve SEO etiketleri kendiliğinden oluşur).

Giriş: GitHub → Settings → Developer settings → **Fine-grained token** oluşturun
(yalnızca `serafix-site` deposu, *Contents: Read and write*), panelde "Sign in with Token" ile girin.

## Formlar ve istatistik

- **Form:** Formspree (veya benzeri) üzerinden bir form adresi alıp `form_action` alanına yazın.
  Boş kalırsa form, ziyaretçinin e-posta uygulamasını açar.
- **Teklif listesi:** Ziyaretçi ürünleri listeye ekler; liste formla birlikte gönderilir.
  Liste yalnızca ziyaretçinin tarayıcısında tutulur.
- **Analytics:** `analytics_id` (G-XXXX) girilirse çerez onay bandı çıkar; Analytics yalnızca
  onay verilirse yüklenir.

## Yerel kurulum

```
pip install -r requirements.txt
python -m playwright install chromium
python build.py            # PDF'lerle birlikte
python build.py --no-pdf   # hızlı, PDF'siz
```
