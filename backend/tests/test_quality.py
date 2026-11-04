from app.quality import assess, is_gibberish
from app.schemas import Product


def make(**kw) -> Product:
    base = dict(
        product_id="1", title="Thing", description="A thoughtfully curated gift set for everyone", price=500.0
    )
    return Product(**{**base, **kw})


def test_gibberish_detection():
    assert is_gibberish("gcdyuvdcbdjhbc")
    assert not is_gibberish("Sleek, refined, and built for everyday excellence")
    assert not is_gibberish("Shirts and snacks")


def test_clean_product_has_no_flags(settings):
    assert assess(make(), settings) == []


def test_flags(settings):
    assert "junk_text" in assess(make(description="gcdyuvdcbdjhbc"), settings)
    assert "placeholder_text" in assess(
        make(description="this group is created by Deepesh for clothes"), settings
    )
    assert "placeholder_text" in assess(make(description="deepesh created"), settings)
    assert "placeholder_text" in assess(make(description="wrist watch description"), settings)
    assert "thin_description" in assess(make(description="Chocolates"), settings)
    assert "price_outlier" in assess(make(price=1.0), settings)
    assert "price_outlier" in assess(make(price=100000.0), settings)


def test_normal_copy_with_the_word_created_is_not_flagged(settings):
    flags = assess(
        make(description="Created to be worn together, a pairing of two distinct scents."), settings
    )
    assert "placeholder_text" not in flags


def test_real_catalog_flags(all_products):
    by_title = {p.title: p for p in all_products}
    assert "junk_text" in by_title["rose"].quality_flags
    assert "price_outlier" in by_title["for jewellery"].quality_flags
    assert by_title["Forever Rose"].quality_flag is None
