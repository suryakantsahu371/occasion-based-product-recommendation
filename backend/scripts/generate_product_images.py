"""
Generate a realistic product photo for EVERY product in data/products.json (Pollinations, free,
no API key) and wire them into the app.

Run from backend/:
    python scripts/generate_product_images.py

- Images are saved to  frontend/public/product-images/<SKU>_<name>.jpg   (served by Vite/nginx at /product-images/...)
- data/products.json is rewritten in place (backup: products.json.bak) with
  mainImage = "/product-images/<file>"
- Safe to re-run: already generated images are skipped.
Then run `make index` so the API serves the new image paths.
"""

import json
import os
import re
import shutil
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMG_DIR = os.path.join(ROOT, "frontend", "public", "product-images")
PRODUCTS = os.path.join(ROOT, "backend", "data", "products.json")
WEB_PREFIX = "/product-images/"

# product name (lowercase) -> subject used in the prompt
Q = {
    "arts & craft kits": "kids craft supplies",
    "bike and car printed": "printed t-shirt",
    "baby shower & newborn gifts": "newborn baby gift basket",
    "baggy jeans": "baggy jeans denim",
    "bamboo lifestyle products": "bamboo kitchen products",
    "black t shirt": "black t-shirt folded",
    "black watch": "black wrist watch",
    "body oils": "body oil bottle",
    "cargos": "cargo pants",
    "cherry blossom candle": "pink scented candle",
    "chocolate": "chocolate bar",
    "christmas dry fruits hampers": "christmas dry fruits nuts gift",
    "christmas luxury gift hampers": "christmas gift hamper",
    "couple mugs": "two coffee mugs",
    "couple perfumes": "two perfume bottles",
    "custom star map": "framed star map poster",
    "diy slime kits": "colorful slime",
    "dj & music mixer toys": "dj mixer",
    "dark chocolate": "dark chocolate",
    "digital gift cards": "gift card phone",
    "diwali dry fruits hampers": "dry fruits almonds cashews",
    "diwali luxury gift hampers": "diwali gift box",
    "drop pearl bracelet": "pearl bracelet",
    "drums & percussion sets": "toy drum set kids",
    "engagement gift": "engagement ring box gift",
    "executive pens": "luxury pen",
    "floria perfume": "floral perfume bottle",
    "floria soap": "handmade floral soap",
    "floria solid perfume": "solid perfume tin",
    "frese perfume": "fresh perfume bottle",
    "frese perfume soap": "handmade soap bar",
    "frese solid perfume": "lip balm tin",
    "flower": "flower bouquet",
    "forever rose": "preserved rose glass dome",
    "fountain pens": "fountain pen",
    "gift boxes": "gift box ribbon",
    "gift sets & bundles": "gift set box",
    "gift wrapping": "gift wrapping paper ribbon",
    "gold choker necklave": "gold choker necklace",
    "gold drop earrings": "gold earrings",
    "gold stacked bracelet": "gold bracelets",
    "gretting cards": "greeting cards",
    "health & fitness gifts": "water bottle dumbbells fitness",
    "herbal teas & infusions": "herbal tea",
    "holi dry fruits hampers": "dry fruits bowl",
    "holi luxury gift hampers": "festive gift hamper",
    "housewarming gifts": "home decor gift",
    "indoor plants & planters": "indoor plant pot",
    "kashmiri suits": "indian embroidered suit",
    "keychain plushies": "plush keychain",
    "lavender candle": "lavender candle",
    "luxury chocolates": "chocolate truffles box",
    "marigold": "marigold flowers",
    "mental wellness gifts": "journal candle self care",
    "metal pens": "metal pen",
    "metallic gold watch": "gold wrist watch",
    "metallic silver watch": "silver wrist watch",
    "milk chocolate": "milk chocolate",
    "multicolor choker necklace": "colorful indian necklace",
    "natural fiber décor items": "jute basket decor",
    "office wears": "formal shirt",
    "open when letters": "letters envelopes",
    "open-value gift cards": "gift card",
    "organic bath salts & scrubs": "bath salt jar",
    "organic skincare products": "natural skincare bottles",
    "print": "printed t-shirt",
    "painting & coloring kits": "kids paint set",
    "pants": "trousers",
    "personalized story book": "children story book",
    "physical gift cards": "gift card envelope",
    "plant based candles": "soy candle",
    "polo neck tshirts(men)": "men polo shirt",
    "polo neck tshirts(women)": "women polo shirt",
    "premium fresh flower bouquet – rose & peony 50ml eau de parfum": "rose perfume bottle",
    "ready to wear sarees": "saree",
    "recycled & upcycled gifts": "upcycled decor",
    "recycled paper notebooks & journals": "kraft paper notebook",
    "rollerball pens": "rollerball pen",
    "rose gold watch": "rose gold watch",
    "rosegold necklace": "rose gold necklace",
    "rosegold studs earrings": "stud earrings",
    "rosegold watch": "rose gold women watch",
    "round neck tshirts": "plain t-shirts",
    "seasonal gift cards": "festive gift card",
    "self-care kits": "self care kit spa",
    "shirts": "men shirt",
    "silver layered nacklace": "silver layered necklace",
    "silver oxidized earings": "oxidised silver earrings",
    "silver stone bracelet": "silver bracelet",
    "snacks box": "snack box",
    "soft toys & plushies": "plush toys",
    "straigh fit kurtis": "kurti",
    "teddy bears": "teddy bear",
    "touch bracelets": "couple bracelets",
    "toy guitars": "toy guitar",
    "tulips": "tulip bouquet",
    "upcycled fabric bags & pouches": "fabric tote bag",
    "vintage watch": "vintage watch",
    "woodé perfume": "woody perfume bottle",
    "woodé soap": "natural soap bar",
    "woodé solid perfumes": "solid perfume",
    "wax seals & stickers": "wax seal envelope",
    "white chocolates": "white chocolate",
    "xylophones": "toy xylophone",
    "for jewellery": "gold jewellery",
    "lilies": "lily flowers",
    "rose": "red roses bouquet",
}


def _norm(s):
    s = re.sub(r"\s+", " ", s.strip().lower())
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


_QN = {_norm(k): v for k, v in Q.items()}

UA = {"User-Agent": "gift-recs-demo/1.0 (local project)"}
API = "https://commons.wikimedia.org/w/api.php?"
USED = set()


def search_photos(query):
    qs = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": 6,
            "gsrlimit": 15,
            "gsrsearch": query + " filetype:bitmap",
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": 800,
        }
    )
    req = urllib.request.Request(API + qs, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        pages = json.load(r).get("query", {}).get("pages", {})
    out = []
    for pg in sorted(pages.values(), key=lambda x: x.get("index", 0)):
        i = (pg.get("imageinfo") or [{}])[0]
        if i.get("mime") == "image/jpeg" and i.get("width", 0) >= 600 and i.get("thumburl"):
            out.append(i["thumburl"])
    return out


def get(url, tries=4):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
                if len(data) > 5000:
                    return data
        except Exception as e:
            print("   retry", t + 1, "-", e, flush=True)
        time.sleep(3 * (t + 1))
    return None


def fetch_for(p):
    subject = _QN.get(_norm(p["name"]), p["name"].lower())
    for q in (subject, subject.split()[-1]):
        try:
            urls = [u for u in search_photos(q) if u not in USED]
        except Exception as e:
            print("   search error -", e, flush=True)
            time.sleep(5)
            continue
        for u in urls[:3]:
            data = get(u)
            if data:
                USED.add(u)
                return data
    return None


def main():
    products = json.load(open(PRODUCTS, encoding="utf-8"))
    os.makedirs(IMG_DIR, exist_ok=True)
    if not os.path.exists(PRODUCTS + ".bak"):
        shutil.copyfile(PRODUCTS, PRODUCTS + ".bak")
    failed = []
    for i, p in enumerate(products, 1):
        safe = re.sub(r"[^\w]+", "_", p["name"]).strip("_")
        fname = f"{p['sku']}_{safe}.jpg"
        path = os.path.join(IMG_DIR, fname)
        print(f"[{i}/{len(products)}] {p['name']}", flush=True)
        if not os.path.exists(path):
            data = fetch_for(p)
            if not data:
                failed.append(p["name"])
                continue
            open(path, "wb").write(data)
            time.sleep(1)
        p["mainImage"] = WEB_PREFIX + fname
        # checkpoint so a crash / Ctrl+C doesn't lose progress
        json.dump(products, open(PRODUCTS, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print("\nDone. Now run: make index")
    if failed:
        print("Failed (re-run the script to retry):", failed)


if __name__ == "__main__":
    main()
