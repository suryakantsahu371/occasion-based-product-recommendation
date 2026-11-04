"""
Fetch REAL product photos from Pexels for every product in data/products.json.

1. Free API key: https://www.pexels.com/api/
2. PEXELS_API_KEY=your_key python scripts/fetch_product_images.py   (run from backend/)
   -> rewrites data/products.json in place (mainImage = Pexels URL); backup in products.json.bak
3. make index   (re-enrich + rebuild so the API serves the new image URLs)
"""

import json
import os
import re
import shutil
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

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


def query_for(name):
    return _QN.get(_norm(name), re.sub(r"\s+", " ", name.strip().lower()))


def search(query, key):
    qs = urllib.parse.urlencode({"query": query, "per_page": 15, "orientation": "landscape"})
    req = urllib.request.Request(
        "https://api.pexels.com/v1/search?" + qs,
        headers={"Authorization": key, "User-Agent": "gift-recs/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get("photos", [])


def main():
    key = os.environ.get("PEXELS_API_KEY") or sys.exit("Set PEXELS_API_KEY")
    path = sys.argv[1] if len(sys.argv) > 1 else "data/products.json"
    products = json.load(open(path, encoding="utf-8"))
    shutil.copyfile(path, path + ".bak")
    used, cache = set(), {}
    for p in products:
        q = query_for(p["name"])
        if q not in cache:
            cache[q] = search(q, key)
            time.sleep(0.4)
        photos = cache[q]
        photo = next((x for x in photos if x["id"] not in used), photos[0] if photos else None)
        if not photo:
            print("No photo for:", p["name"])
            continue
        used.add(photo["id"])
        p["mainImage"] = photo["src"]["large"]
        print(f"{p['name']:<45} -> {p['mainImage']}")
    json.dump(products, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("\nDone. Now run: make index")


if __name__ == "__main__":
    main()
