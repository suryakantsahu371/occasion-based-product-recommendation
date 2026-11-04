def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["indexes_loaded"] is True and body["products"] == 104


def test_occasions_endpoint(client):
    data = client.get("/api/occasions").json()
    keys = {o["key"] for o in data}
    assert len(data) == 16 and {"diwali", "kids_birthday", "corporate"} <= keys
    assert all({"key", "label", "icon"} == set(o) for o in data)


def test_recommend_response_shape(client):
    r = client.post("/api/recommend", json={"occasion": "Diwali", "top_k": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == {
        "raw": "Diwali",
        "matched_occasion": "diwali",
        "matched_label": "Diwali",
        "match_type": "exact",
    }
    assert len(body["results"]) == 5 and body["latency_ms"] > 0
    first = body["results"][0]
    assert {
        "product_id",
        "title",
        "category",
        "description_snippet",
        "image",
        "price",
        "final_price",
        "score",
        "reasons",
        "breakdown",
    } <= set(first)
    assert first["image"].startswith("https://")


def test_empty_results_are_http_200(client):
    r = client.post("/api/recommend", json={"occasion": "xyzqwerty"})
    assert r.status_code == 200 and r.json()["results"] == []


def test_validation(client):
    assert client.post("/api/recommend", json={"occasion": ""}).status_code == 422
    assert client.post("/api/recommend", json={"occasion": "   "}).status_code == 422
    assert client.post("/api/recommend", json={"occasion": "x" * 101}).status_code == 422
    assert client.post("/api/recommend", json={"occasion": "Diwali", "top_k": 0}).status_code == 422
    assert (
        client.post("/api/recommend", json={"occasion": "Diwali", "keyword_method": "nope"}).status_code
        == 422
    )
    assert client.post("/api/recommend", json={}).status_code == 422


def test_max_price_and_method(client):
    r = client.post(
        "/api/recommend", json={"occasion": "Wedding", "max_price": 2000, "keyword_method": "tfidf"}
    )
    body = r.json()
    assert r.status_code == 200 and body["keyword_method"] == "tfidf"
    assert all(p["final_price"] <= 2000 for p in body["results"])


def test_cors_header_for_dev_frontend(client):
    r = client.options(
        "/api/recommend",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
