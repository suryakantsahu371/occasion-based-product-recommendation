from app.adapter import clean_text, extract_shop, normalize_payload, published


def test_brief_payload_shape():
    p = normalize_payload(
        {
            "productId": 42,
            "vendorId": "v1",
            "vendor_category": "gifts",
            "vendor_category_desc": "Gift Sets",
            "title": "Birthday Box",
            "description": "A box of treats",
            "files": ["https://img/a.png", {"url": "https://img/b.png"}],
        }
    )
    assert (p.product_id, p.vendor_id, p.vendor_category) == ("42", "v1", "gifts")
    assert p.vendor_category_desc == "Gift Sets"
    assert p.title == "Birthday Box"
    assert p.files == ["https://img/a.png", "https://img/b.png"]
    assert p.is_published  # no status/stock in the brief's schema -> treated as available


def test_catalog_payload_shape():
    p = normalize_payload(
        {
            "id": "abc",
            "shopId": "shop1",
            "categoryId": "cat1",
            "name": "Forever Rose",
            "slug": "forever-rose-Petal & Oak",
            "description": "A symbol\r\nof love",
            "shortDescription": "Wrapped in romance, and meant to be remembered forever",
            "mainImage": "https://img/rose.png",
            "price": "1099",
            "discountPercentage": "10",
            "stock": 150,
            "status": "ACTIVE",
            "isApproved": True,
            "deletedAt": None,
            "productGroupId": "g1",
        }
    )
    assert (p.product_id, p.vendor_id, p.vendor_category) == ("abc", "shop1", "cat1")
    assert p.title == "Forever Rose"
    assert p.description == "A symbol of love"  # \r\n collapsed
    assert p.files == ["https://img/rose.png"]
    assert p.shop == "Petal & Oak"
    assert p.price == 1099.0 and p.final_price == 989.1
    assert p.group_key == "g1"


def test_short_description_only_kept_when_it_adds_words():
    base = {"id": "1", "name": "Pen", "description": "Sleek refined premium pen for office"}
    dup = normalize_payload({**base, "shortDescription": "Sleek refined premium pen"})
    new = normalize_payload({**base, "shortDescription": "Ideal for corporate gifting and teams."})
    assert dup.extra_description == ""
    assert new.extra_description == "Ideal for corporate gifting and teams."


def test_truncated_short_description_is_trimmed_to_last_sentence():
    p = normalize_payload(
        {
            "id": "1",
            "name": "x",
            "description": "d",
            "shortDescription": "First sentence here. Second dangling frag, ",
        }
    )
    assert p.extra_description == "First sentence here."


def test_missing_id_is_rejected():
    import pytest

    with pytest.raises(ValueError):
        normalize_payload({"name": "no id"})


def test_extract_shop_variants():
    assert extract_shop({"slug": "gift-wrapping-The Gift Atelier"}) == "The Gift Atelier"
    assert extract_shop({"slug": "dark-chocolate-bloom by the hour"}) == "bloom by the hour"
    assert extract_shop({"slug": "flower-bloom by the hour-t7duskal"}) == "bloom by the hour"
    assert extract_shop({"slug": "pen-Gifftery Corporate Gifts"}) == "Gifftery Corporate Gifts"
    assert extract_shop({"slug": "polo-neck-tshirts-Threads 'n' Thoughts"}) == "Threads 'n' Thoughts"
    assert extract_shop({"slug": "plain", "brand": "Acme"}) == "Acme"


def test_clean_text():
    assert clean_text("  a\r\n\r\n b\t c ") == "a b c"
    assert clean_text(None) == ""


def test_unpublished_products_are_filtered(all_products):
    live = published(all_products)
    assert 0 < len(live) < len(all_products)
    assert all(p.status == "ACTIVE" and p.is_approved and p.stock > 0 for p in live)
    excluded = {p.title for p in all_products if not p.is_published}
    assert "Black T Shirt" in excluded and "Milk chocolate" in excluded


def test_catalog_loads_with_expected_counts(all_products):
    assert len(all_products) == 110
    assert sum(p.is_published for p in all_products) == 104
