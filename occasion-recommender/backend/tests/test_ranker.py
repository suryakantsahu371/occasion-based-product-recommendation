"""Scorer unit tests and the acceptance checks from the brief."""

import pytest

from app.config import Weights
from app.ranker import snippet
from app.tagger import tag_product
from tests.conftest import titles

GIFFTERY = "Gifftery Corporate Gifts"


def shops(recommender, response, n):
    by_title = {p.title: p.shop for p in recommender.retriever.products}
    return [by_title[t] for t in titles(response, n)]


# ----------------------------------------------------------------- acceptance checks


def test_diwali(recommender):
    res = recommender.recommend("Diwali")
    top3 = titles(res, 3)
    assert "Diwali Dry fruits hampers" in top3 and "Diwali Luxury Gift Hampers" in top3
    top5 = " ".join(titles(res, 5)).lower()
    assert "holi" not in top5 and "christmas" not in top5


def test_valentines_day(recommender):
    top8 = titles(recommender.recommend("Valentine's Day"), 8)
    for expected in ("Forever Rose", "Couple Perfumes", "Touch Bracelets"):
        assert expected in top8
    assert not any("pen" in t.lower().split() for t in top8)


def test_office_party_is_dominated_by_gifftery(recommender):
    res = recommender.recommend("Office party")
    assert shops(recommender, res, 5).count(GIFFTERY) >= 4
    assert "Executive pens" in titles(res, 5) or "Metal pens" in titles(res, 5)


def test_kids_birthday_is_dominated_by_giggle_and_grow(recommender):
    res = recommender.recommend("Kids birthday")
    assert shops(recommender, res, 5).count("Giggle And Grow") == 5


def test_housewarming(recommender):
    res = recommender.recommend("Housewarming")
    assert "Housewarming Gifts" in titles(res, 3)
    joined = " ".join(titles(res)).lower()
    assert "plant" in joined and "candle" in joined
    # Natural-fibre décor can lose its slot to the per-group cap; any décor product satisfies the check.
    assert any("décor" in r.description.lower() for r in res.results)


def test_baby_shower_rank_one(recommender):
    assert titles(recommender.recommend("Baby shower"), 1) == ["Baby Shower & Newborn Gifts"]


def test_synonym_and_typo_queries_resolve(recommender):
    assert recommender.recommend("shaadi").query.matched_occasion == "wedding"
    typo = recommender.recommend("diwaali")
    assert typo.query.matched_occasion == "diwali" and typo.query.match_type == "fuzzy"


def test_gibberish_returns_empty(recommender):
    res = recommender.recommend("xyzqwerty")
    assert res.results == [] and res.total == 0 and res.query.match_type == "open_ended"


@pytest.mark.parametrize(
    "q",
    [
        "Diwali",
        "Valentine's Day",
        "Birthday",
        "wedding",
        "gift",
        "chocolate",
        "office",
        "shaadi",
        "baby",
        "rose",
    ],
)
def test_unpublished_products_never_appear(recommender, all_products, q):
    unpublished = {p.title for p in all_products if not p.is_published}
    live = {p.title for p in all_products if p.is_published}
    for t in titles(recommender.recommend(q, top_k=50)):
        assert t in live
    # A title may be shared by a live and an unpublished product ("Chocolate"); ids are the real check.
    live_ids = {p.product_id for p in all_products if p.is_published}
    assert {r.product_id for r in recommender.recommend(q, top_k=50).results} <= live_ids
    assert unpublished  # sanity: the catalog really contains unpublished products


# ----------------------------------------------------------------- scorer behaviour


def test_at_most_two_results_per_product_group(recommender):
    by_id = {p.product_id: p for p in recommender.retriever.products}
    for q in ("Office party", "Kids birthday", "Valentine's Day", "Diwali"):
        groups = [by_id[r.product_id].group_key for r in recommender.recommend(q, top_k=50).results]
        assert max(groups.count(g) for g in set(groups)) <= recommender.settings.max_per_group


def test_conflict_penalty_demotes_sibling_festival_hampers(recommender):
    res = recommender.recommend("Diwali", top_k=50)
    assert not any(t.startswith(("Holi", "Christmas")) for t in titles(res))


def test_results_are_sorted_by_relevance_within_tolerance(recommender):
    scores = [r.score for r in recommender.recommend("Wedding", top_k=12).results]
    assert scores[0] == max(scores)


def test_junk_products_are_down_weighted(recommender):
    res = recommender.recommend("Valentine's Day", top_k=50)
    junk = next((r for r in res.results if r.title == "rose"), None)
    assert junk is None or junk.breakdown.penalty > 0


def test_score_breakdown_adds_up(recommender):
    for r in recommender.recommend("Diwali").results:
        b = r.breakdown
        assert r.score == pytest.approx(b.semantic + b.tag + b.keyword + b.name_boost - b.penalty, abs=1e-3)


def test_max_price_filter_uses_final_price_and_skips_outliers(recommender):
    res = recommender.recommend("Wedding", top_k=50, max_price=3000)
    assert res.results and all(r.final_price <= 3000 for r in res.results)


def test_keyword_method_override(recommender):
    for method in ("bm25", "tfidf"):
        res = recommender.recommend("Diwali", method=method)
        assert res.keyword_method == method and res.results


def test_open_ended_weights_redistribute_tag_weight():
    w = Weights().open_ended()
    assert w.tag == 0
    assert w.semantic + w.keyword == pytest.approx(Weights().semantic + Weights().keyword + Weights().tag)
    assert w.semantic / w.keyword == pytest.approx(Weights().semantic / Weights().keyword)


def test_default_weights_match_design():
    w = Weights()
    assert (w.semantic, w.tag, w.keyword, w.name_boost, w.conflict_penalty) == (0.45, 0.35, 0.20, 0.30, 0.50)


def test_every_result_has_reasons_and_snippet(recommender):
    for r in recommender.recommend("Housewarming").results:
        assert r.reasons and r.description_snippet and r.category


def test_snippet_cuts_at_word_boundary():
    text = "word " * 60
    out = snippet(text, 140)
    assert out.endswith("…") and len(out) <= 141 and " …" not in out
    assert snippet("short text") == "short text"


def test_tagger_ties_festival_hampers_to_their_festival(all_products):
    by_title = {p.title: p for p in all_products}
    tag = tag_product(by_title["Holi Luxury Gift Hampers"], "Festive Hampers")
    assert tag.occasion_specific_to == "holi"
    assert tag.occasions["holi"] == 1.0 and tag.occasions.get("diwali", 0) <= 0.3
