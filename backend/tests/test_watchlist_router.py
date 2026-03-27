def test_get_empty_watchlist(client):
    resp = client.get("/watchlist")
    assert resp.status_code == 200
    assert resp.json()["tickers"] == []

def test_add_to_watchlist(client):
    resp = client.post("/watchlist/BBCA")
    assert resp.status_code == 200
    resp2 = client.get("/watchlist")
    assert "BBCA" in resp2.json()["tickers"]

def test_remove_from_watchlist(client):
    client.post("/watchlist/BBCA")
    resp = client.delete("/watchlist/BBCA")
    assert resp.status_code == 200
    assert "BBCA" not in client.get("/watchlist").json()["tickers"]
