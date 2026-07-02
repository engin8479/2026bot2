import os
import json
import time
import random
import re
import requests
import threading
from urllib.parse import urlparse, parse_qs, urlencode
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# =====================================================================
# 1. AYARLAR
# =====================================================================
BASE_DIR = os.getcwd()
DATA_FILE = os.path.join(BASE_DIR, "urunler.json")

SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

MAX_SAYFA = int(os.environ.get("MAX_SAYFA", "420"))
ARDISIK_BOS_SAYFA_LIMIT = 2
SAYFA_DENEME_SAYISI = 3
KAYIT_ARALIGI_SAYFA = 10
MAX_PARALEL_ISTEK = 5

# YENİ OPTİMİZASYON 1: İsteklerin darboğaz yapmaması için Session ve Bağlantı Havuzu
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=MAX_PARALEL_ISTEK, pool_maxsize=MAX_PARALEL_ISTEK)
session.mount('https://', adapter)
session.mount('http://', adapter)

# =====================================================================
# 2. TARANACAK KATEGORİLER (TABAN LİNKLER)
# =====================================================================
ARAMALAR = [
    {
        "etiket": "Elektronik - 12466496031 (popülerlik)",
        "url": "https://www.amazon.com.tr/s?i=electronics&rh=n:12466496031,p_6:A1UNQM1SR2CHM&s=popularity-rank&fs=true",
    },
]

# =====================================================================
# 3. VERİTABANI YÜKLEME
# =====================================================================
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            veritabani = json.load(f)
    except Exception:
        veritabani = {}
else:
    veritabani = {}

KAMPANYA_ROZETI_SINIFLARI = [
    "coupon",
    "kupon",
    "trade-in",
    "tradein",
    "degis-tokus",
    "değiş-tokuş",
]

# =====================================================================
# 4. YARDIMCI FONKSİYONLAR
# =====================================================================
def telegram_mesaj_gonder(mesaj):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram mesajı gönderilemedi: {e}")

# YENİ OPTİMİZASYON 2: Ana programı bekletmemek için Telegram mesajlarını arka planda yolla
def telegram_arkaplan(mesaj):
    threading.Thread(target=telegram_mesaj_gonder, args=(mesaj,)).start()

def sayfa_url_olustur(taban_url, sayfa_no):
    parsed = urlparse(taban_url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    qs["page"] = [str(sayfa_no)]
    flat = {k: v[0] for k, v in qs.items()}
    query = urlencode(flat, safe="%,:|")
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{query}"

def amazon_sayfa_tara(url):
    scraper_url = "https://api.scraperapi.com/"
    params = {"api_key": SCRAPER_API_KEY, "url": url, "country_code": "tr", "render": "false"}
    try:
        # requests.get yerine Session kullanılıyor
        response = session.get(scraper_url, params=params, timeout=60)
        if response.status_code == 200:
            return response.text
        print(f"  Uyarı: HTTP {response.status_code} -> {url[:90]}...")
        return None
    except Exception as e:
        print(f"  Uyarı: İstek hatası ({e}) -> {url[:90]}...")
        return None

def veriyi_isle(html_icerik):
    bulunan_urunler = []
    soup = BeautifulSoup(html_icerik, "html.parser")
    kartlar = soup.select('div[data-component-type="s-search-result"]')

    for kart in kartlar:
        asin = (kart.get("data-asin") or "").strip()
        if not re.fullmatch(r"[A-Z0-9]{10}", asin):
            continue

        baslik_elem = kart.select_one("h2 span") or kart.select_one("h2")
        if not baslik_elem:
            continue
        baslik = baslik_elem.get_text(strip=True)[:80]
        if not baslik:
            continue

        fiyat = kart_gercek_fiyati_bul(kart)
        if fiyat is None:
            continue

        bulunan_urunler.append({"asin": asin, "baslik": baslik, "fiyat": fiyat})

    return bulunan_urunler

def kart_gercek_fiyati_bul(kart):
    for fiyat_span in kart.select("span.a-price"):
        siniflar = fiyat_span.get("class", [])
        if "a-text-price" in siniflar:
            continue

        if _kampanya_rozeti_icinde_mi(fiyat_span):
            continue

        offscreen = fiyat_span.select_one(".a-offscreen")
        if not offscreen:
            continue
        fiyat_metni = offscreen.get_text(strip=True)
        if not fiyat_metni:
            continue

        return _fiyat_metnini_sayiya_cevir(fiyat_metni)
    return None

def _kampanya_rozeti_icinde_mi(eleman):
    guncel = eleman.parent
    for _ in range(6):
        if guncel is None or not hasattr(guncel, "get"):
            break
        siniflar = " ".join(guncel.get("class", []) or []).lower()
        id_degeri = (guncel.get("id") or "").lower()
        if any(k in siniflar or k in id_degeri for k in KAMPANYA_ROZETI_SINIFLARI):
            return True
        guncel = guncel.parent
    return False

def _fiyat_metnini_sayiya_cevir(metin):
    try:
        sadece_rakam = re.sub(r"[^\d,.]", "", metin)
        sadece_rakam = sadece_rakam.replace(".", "").replace(",", ".")
        fiyat = float(sadece_rakam)
        return fiyat if fiyat > 0 else None
    except Exception:
        return None

def veritabanini_kaydet():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(veritabani, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"  Uyarı: veritabanı diske yazılamadı: {e}")

def sayfayi_getir(url, sayfa_no):
    print(f"  🚀 Sayfa {sayfa_no} aranıyor...")
    for deneme in range(1, SAYFA_DENEME_SAYISI + 1):
        html = amazon_sayfa_tara(url)
        if html:
            return veriyi_isle(html)
        if deneme < SAYFA_DENEME_SAYISI:
            # YENİ OPTİMİZASYON 3: Hata durumundaki aşırı bekleme süresi 1 saniyeye düşürüldü
            time.sleep(1)
    return None

# =====================================================================
# 5. ANA PROGRAM
# =====================================================================
def ana_program():
    global veritabani
    toplam_yeni = 0
    toplam_indirim = 0
    toplam_sayfa_istegi = 0

    print(f"Tarama başlatılıyor. {len(ARAMALAR)} kategori kontrol edilecek (kategori başına en fazla {MAX_SAYFA} sayfa).")
    print(f"Veritabanı dosyası: {DATA_FILE}")
    print(f"Başlangıçta hafızada kayıtlı ürün sayısı: {len(veritabani)}")
    print(f"Paralel Çalışma Modu: Aynı anda maksimum {MAX_PARALEL_ISTEK} sayfa işlenecek.")

    for arama in ARAMALAR:
        etiket = arama["etiket"]
        taban_url = arama["url"]
        bos_sayac = 0

        print(f"\n>> Kategori: {etiket}")
        kategori_bitti = False

        for sayfa_grubu_baslangic in range(1, MAX_SAYFA + 1, MAX_PARALEL_ISTEK):
            hedef_sayfalar = []
            for i in range(MAX_PARALEL_ISTEK):
                s_no = sayfa_grubu_baslangic + i
                if s_no <= MAX_SAYFA:
                    hedef_sayfalar.append(s_no)

            with ThreadPoolExecutor(max_workers=MAX_PARALEL_ISTEK) as executor:
                sonuclar = list(executor.map(lambda sn: (sn, sayfayi_getir(sayfa_url_olustur(taban_url, sn), sn)), hedef_sayfalar))

            for sayfa_no, urunler in sonuclar:
                sayfa_url = sayfa_url_olustur(taban_url, sayfa_no)
                toplam_sayfa_istegi += 1

                if urunler is None:
                    print(f"  Sayfa {sayfa_no}: çekilemedi, atlanıyor.")
                elif len(urunler) == 0:
                    bos_sayac += 1
                    print(f"  Sayfa {sayfa_no}: ürün bulunamadı ({bos_sayac}/{ARDISIK_BOS_SAYFA_LIMIT}).")
                    if bos_sayac >= ARDISIK_BOS_SAYFA_LIMIT:
                        print(f"  Kategori bitti kabul edildi, sayfa {sayfa_no}'de durduruldu -> sonraki kategoriye geçiliyor.")
                        kategori_bitti = True
                        break 
                else:
                    bos_sayac = 0
                    print(f"  Sayfa {sayfa_no}: {len(urunler)} ürün bulundu.")

                    for urun in urunler:
                        asin = urun["asin"]
                        fiyat = urun["fiyat"]
                        baslik = urun["baslik"]
                        link = f"https://www.amazon.com.tr/dp/{asin}"

                        if asin not in veritabani:
                            veritabani[asin] = {
                                "baslik": baslik,
                                "fiyat": fiyat,
                                "en_dusuk_fiyat": fiyat,
                            }
                            toplam_yeni += 1
                            # YENİ: Beklememek için telegram_arkaplan kullanılıyor
                            telegram_arkaplan(
                                f"🆕 *YENİ ÜRÜN TAKİBE ALINDI*\n"
                                f"📦 {baslik}\n"
                                f"💰 Fiyat: {fiyat:.2f} TL\n"
                                f"🔗 {link}"
                            )
                        else:
                            eski_fiyat = veritabani[asin]["fiyat"]
                            if fiyat < eski_fiyat:
                                fark = eski_fiyat - fiyat
                                yuzde = (fark / eski_fiyat) * 100 if eski_fiyat else 0
                                en_dusuk = min(fiyat, veritabani[asin].get("en_dusuk_fiyat", fiyat))
                                veritabani[asin]["fiyat"] = fiyat
                                veritabani[asin]["en_dusuk_fiyat"] = en_dusuk
                                veritabani[asin]["baslik"] = baslik
                                toplam_indirim += 1
                                # YENİ: Beklememek için telegram_arkaplan kullanılıyor
                                telegram_arkaplan(
                                    f"📉 *FİYAT DÜŞTÜ*\n"
                                    f"📦 {baslik}\n"
                                    f"❌ Eski Fiyat: {eski_fiyat:.2f} TL\n"
                                    f"✅ Yeni Fiyat: {fiyat:.2f} TL\n"
                                    f"🔻 İndirim: %{yuzde:.1f} ({fark:.2f} TL)\n"
                                    f"🏆 Tarihi En Düşük: {en_dusuk:.2f} TL\n"
                                    f"🔗 {link}"
                                )
                            elif fiyat != eski_fiyat:
                                veritabani[asin]["fiyat"] = fiyat
                                veritabani[asin]["baslik"] = baslik

                if sayfa_no % KAYIT_ARALIGI_SAYFA == 0:
                    veritabanini_kaydet()

            if kategori_bitti:
                break 
                
            if not kategori_bitti:
                # YENİ OPTİMİZASYON 4: Gruplar arası gereksiz bekleme süresi 0.1 saniyeye düşürüldü
                time.sleep(0.1)
                
        veritabanini_kaydet()
        print(f"Kategori sonu kaydı yapıldı: {DATA_FILE}")

    print(
        f"\nİşlem tamamlandı. Toplam istek: {toplam_sayfa_istegi} | "
        f"Yeni ürün: {toplam_yeni} | İndirim bildirimi: {toplam_indirim}"
    )

if __name__ == "__main__":
    try:
        ana_program()
    except Exception as e:
        print(f"HATA: {e}")
        veritabanini_kaydet()
        print("Hata sonrası mevcut ilerleme diske kaydedildi.")
        raise
