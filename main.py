import os
import json
import time
import random
import re
import requests
from urllib.parse import urlparse, parse_qs, urlencode
from bs4 import BeautifulSoup

# =====================================================================
# 1. AYARLAR
# =====================================================================
BASE_DIR = os.getcwd()
DATA_FILE = os.path.join(BASE_DIR, "urunler.json")

# Ortam değişkenleri (GitHub Secrets üzerinden gelir)
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Her arama/kategori en fazla kaç sayfa taransın? (güvenlik tavanı)
# Not: Bot her kategoriyi 1. sayfadan başlatıp, üst üste boş sayfa
# görene kadar otomatik ilerletir. Gerçek sayfa sayısı genelde bundan
# çok daha azdır; bu sadece "asla bu sayının üzerine çıkma" tavanıdır.
MAX_SAYFA = int(os.environ.get("MAX_SAYFA", "420"))

# Üst üste kaç boş sayfa görülürse "bu kategori bitti" kabul edilsin
ARDISIK_BOS_SAYFA_LIMIT = 2

# Bir sayfa çekilemezse (ağ/API hatası) kaç kez tekrar denensin
SAYFA_DENEME_SAYISI = 3


# =====================================================================
# 2. TARANACAK KATEGORİLER (TABAN LİNKLER)
# =====================================================================
# ÖNEMLİ: Buraya "page=1", "page=2"... diye tek tek link EKLEMİYORUZ.
# Her arama/filtre kombinasyonu için sadece 1 TABAN link veriyoruz.
# Bot, her taban linkin sonuna otomatik olarak &page=1, &page=2, ...
# ekleyerek o kategori bitene kadar ilerler, bitince bir sonraki
# kategoriye geçer.
#
# Not: Amazon'un "qid", "xpid", "crid" gibi parametreleri oturuma
# özeldir ve zamanla geçersiz olur; bu yüzden taban linklerden
# bilerek çıkarıldı. Kategori (rh=, bbn=, i=, k= gibi filtre
# parametreleri) kalıcıdır ve sorun çıkarmaz.
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


# Bir elemanın class/id isminde bu kelimelerden biri geçiyorsa, bu
# elemanın (ve içindeki her şeyin) bir kampanya/kupon/değiş-tokuş
# rozeti olduğu kabul edilir; içindeki fiyat gerçek satış fiyatı
# olarak KABUL EDİLMEZ.
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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram mesajı gönderilemedi: {e}")


def sayfa_url_olustur(taban_url, sayfa_no):
    """Taban linkin sonuna &page=N ekler (mevcut page varsa günceller)."""
    parsed = urlparse(taban_url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    qs["page"] = [str(sayfa_no)]
    flat = {k: v[0] for k, v in qs.items()}
    query = urlencode(flat, safe="%,:|")
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{query}"


def amazon_sayfa_tara(url):
    scraper_url = "https://api.scraperapi.com/"
    params = {"api_key": SCRAPER_API_KEY, "url": url, "country_code": "tr"}
    try:
        response = requests.get(scraper_url, params=params, timeout=60)
        if response.status_code == 200:
            return response.text
        print(f"  Uyarı: HTTP {response.status_code} -> {url[:90]}...")
        return None
    except Exception as e:
        print(f"  Uyarı: İstek hatası ({e}) -> {url[:90]}...")
        return None


def veriyi_isle(html_icerik):
    """
    Her ürün kartını kendi HTML sınırları içinde ayrı ayrı işler.
    Bu sayede:
      - Bir kartta başlık/fiyat eksikse bir SONRAKİ kartın verisi
        yanlışlıkla önceki ürüne bağlanmaz (ürün çakışması önlenir).
      - "Kupon", "sepette indirim", "değiş tokuş" gibi kampanya
        rozetlerindeki sahte fiyatlar gerçek satış fiyatıyla
        karıştırılmaz.
    """
    bulunan_urunler = []
    soup = BeautifulSoup(html_icerik, "html.parser")

    # Sadece gerçek arama sonucu kartlarını al (carousel, "ilginizi
    # çekebilir" gibi ilgisiz widget'ları hariç tutar)
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
    """
    Bir ürün kartı içinden GERÇEK satış fiyatını bulur.
    Şunları eler:
      - Üstü çizili eski fiyat (class="a-text-price")
      - Kupon / sepette indirim / değiş-tokuş rozetlerinin İÇİNDE yer
        alan fiyatlar (yapısal olarak, ata elemanların class/id
        isimlerine bakarak tespit edilir)
    """
    for fiyat_span in kart.select("span.a-price"):
        siniflar = fiyat_span.get("class", [])
        if "a-text-price" in siniflar:
            # Üstü çizili "eski fiyat" gösterimi, gerçek satış fiyatı değil
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
    """
    Fiyat elemanının bir kupon/kampanya/değiş-tokuş rozetinin İÇİNDE
    olup olmadığını, üst (ata) elemanların class/id isimlerine bakarak
    kontrol eder. SADECE yapısal (class/id) kontrol yapar; kartın geri
    kalanındaki alakasız metinlerden etkilenmez, bu yüzden yan yana
    duran gerçek fiyatı yanlışlıkla elemez.
    """
    guncel = eleman.parent
    for _ in range(6):  # en fazla 6 seviye yukarı çık
        if guncel is None or not hasattr(guncel, "get"):
            break
        siniflar = " ".join(guncel.get("class", []) or []).lower()
        id_degeri = (guncel.get("id") or "").lower()
        if any(k in siniflar or k in id_degeri for k in KAMPANYA_ROZETI_SINIFLARI):
            return True
        guncel = guncel.parent
    return False


def _fiyat_metnini_sayiya_cevir(metin):
    """'1.234,56 TL' gibi bir metni 1234.56 float'a çevirir."""
    try:
        sadece_rakam = re.sub(r"[^\d,.]", "", metin)
        # TR biçimi: binlik ayraç nokta, ondalık ayraç virgül
        sadece_rakam = sadece_rakam.replace(".", "").replace(",", ".")
        fiyat = float(sadece_rakam)
        return fiyat if fiyat > 0 else None
    except Exception:
        return None


def sayfayi_getir(url, sayfa_no):
    """
    Sayfayı çeker. Ağ/API hatasında birkaç kez tekrar dener.
    Dönüş:
      None  -> sayfa hiç çekilemedi (geçici hata, bu ayrı bir durumdur)
      []    -> sayfa çekildi ama hiç ürün yok (kategori muhtemelen bitti)
      [...] -> bulunan ürünler
    """
    for deneme in range(1, SAYFA_DENEME_SAYISI + 1):
        html = amazon_sayfa_tara(url)
        if html:
            return veriyi_isle(html)
        if deneme < SAYFA_DENEME_SAYISI:
            time.sleep(random.uniform(4, 8))
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

    for arama in ARAMALAR:
        etiket = arama["etiket"]
        taban_url = arama["url"]
        bos_sayac = 0

        print(f"\n>> Kategori: {etiket}")

        for sayfa_no in range(1, MAX_SAYFA + 1):
            sayfa_url = sayfa_url_olustur(taban_url, sayfa_no)
            toplam_sayfa_istegi += 1

            urunler = sayfayi_getir(sayfa_url, sayfa_no)

            if urunler is None:
                # Sayfa hiç çekilemedi -> geçici hata, bu sayfayı atla ama
                # kategori taramasına devam et (kategori bitti anlamına gelmez)
                print(f"  Sayfa {sayfa_no}: çekilemedi, atlanıyor.")
                time.sleep(random.uniform(3, 6))
                continue

            if len(urunler) == 0:
                bos_sayac += 1
                print(f"  Sayfa {sayfa_no}: ürün bulunamadı ({bos_sayac}/{ARDISIK_BOS_SAYFA_LIMIT}).")
                if bos_sayac >= ARDISIK_BOS_SAYFA_LIMIT:
                    print(f"  Kategori bitti kabul edildi, sayfa {sayfa_no}'de durduruldu -> sonraki kategoriye geçiliyor.")
                    break
                time.sleep(random.uniform(3, 6))
                continue

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
                    telegram_mesaj_gonder(
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
                        telegram_mesaj_gonder(
                            f"📉 *FİYAT DÜŞTÜ*\n"
                            f"📦 {baslik}\n"
                            f"❌ Eski Fiyat: {eski_fiyat:.2f} TL\n"
                            f"✅ Yeni Fiyat: {fiyat:.2f} TL\n"
                            f"🔻 İndirim: %{yuzde:.1f} ({fark:.2f} TL)\n"
                            f"🏆 Tarihi En Düşük: {en_dusuk:.2f} TL\n"
                            f"🔗 {link}"
                        )
                    elif fiyat != eski_fiyat:
                        # Fiyat arttı: bildirim atmıyoruz ama veritabanını
                        # güncel tutuyoruz ki bir sonraki düşüş doğru
                        # kıyaslansın.
                        veritabani[asin]["fiyat"] = fiyat
                        veritabani[asin]["baslik"] = baslik

            # API'yi patlatmamak ve bloklanmamak için sayfalar arası bekleme
            time.sleep(random.uniform(3, 7))

        # Her kategori sonrası veritabanını diske yaz (uzun taramada
        # bir hata/timeout olursa o ana kadarki ilerleme kaybolmasın)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(veritabani, f, ensure_ascii=False, indent=4)

    print(
        f"\nİşlem tamamlandı. Toplam istek: {toplam_sayfa_istegi} | "
        f"Yeni ürün: {toplam_yeni} | İndirim bildirimi: {toplam_indirim}"
    )


if __name__ == "__main__":
    ana_program()
