def test_get_stocks_returns_list(client):
    resp = client.get("/stocks")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    stock = data[0]
    assert stock["ticker"] == "BBCA"
    assert stock["price"] == 9200
    assert "LQ45" in stock["indices"]

def test_get_stocks_filter_by_index(client):
    resp = client.get("/stocks?index=LQ45")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_get_stocks_filter_excludes_nonmatch(client):
    resp = client.get("/stocks?index=NONEXISTENT")
    assert resp.status_code == 200
    assert len(resp.json()) == 0

def test_get_stock_detail(client):
    resp = client.get("/stocks/BBCA")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "BBCA"
    assert len(data["price_history"]) == 1

def test_get_stock_detail_not_found(client):
    resp = client.get("/stocks/XXXX")
    assert resp.status_code == 404
