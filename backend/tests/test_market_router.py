def test_get_market(client):
    resp = client.get("/market")
    assert resp.status_code == 200
    data = resp.json()
    assert "ihsg_price" in data
    assert "history" in data
    assert len(data["history"]) == 1
    assert data["history"][0]["close"] == 7284.0
