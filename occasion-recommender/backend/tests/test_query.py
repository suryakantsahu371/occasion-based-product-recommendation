import pytest

from app.query import normalize, parse_query


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Valentine's Day!", "valentine day"),
        ("  DIWALI  ", "diwali"),
        ("Valentine’s", "valentine"),
        ("office-party", "office party"),
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize(
    "raw,key",
    [
        ("shaadi", "wedding"),
        ("vivah", "wedding"),
        ("bday", "birthday"),
        ("rakhi", "raksha_bandhan"),
        ("deepawali", "diwali"),
        ("Deepavali", "diwali"),
        ("office party", "corporate"),
        ("team", "corporate"),
        ("saalgirah", "anniversary"),
        ("godh bharai", "baby_shower"),
        ("griha pravesh", "housewarming"),
        ("Valentine's Day", "valentines_day"),
        ("Mother's Day", "mothers_day"),
        ("Kids birthday", "kids_birthday"),  # longest phrase wins over "birthday"
        ("wedding anniversary", "anniversary"),
        ("diwali gifts for family", "diwali"),
    ],
)
def test_synonyms_map_to_taxonomy(raw, key):
    parsed = parse_query(raw)
    assert parsed.occasion is not None and parsed.occasion.key == key
    assert parsed.match_type == "exact"


@pytest.mark.parametrize(
    "raw,key", [("diwaali", "diwali"), ("valentin", "valentines_day"), ("weding", "wedding")]
)
def test_typos_are_fuzzy_matched(raw, key):
    parsed = parse_query(raw)
    assert parsed.occasion is not None and parsed.occasion.key == key
    assert parsed.match_type == "fuzzy"


@pytest.mark.parametrize("raw", ["xyzqwerty", "retirement party", "holy", "ab"])
def test_unknown_queries_are_open_ended(raw):
    parsed = parse_query(raw)
    assert parsed.occasion is None
    assert parsed.match_type == "open_ended"
    assert parsed.text == parsed.normalized


def test_matched_queries_are_expanded():
    parsed = parse_query("Diwali")
    assert "dry fruit hampers" in parsed.text and "diyas" in parsed.text
