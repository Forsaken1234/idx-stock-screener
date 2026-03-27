def test_get_market(client):
    resp = client.get("/market")
    assert resp.status_code == 200
    data = resp.json()
    assert "ihsg_price" in data
    assert "history" in data
    assert len(data["history"]) == 1
    assert data["history"][0]["close"] == 7284.0


def test_get_market_fallback_to_most_recent_day(client):
    """When no data exists for today, falls back to most recent day's data."""
    # The conftest seeds ihsg data for a past date (2026-03-27T09:00:00)
    # So the "today" filter returns nothing, triggering the fallback
    resp = client.get("/market")
    assert resp.status_code == 200
    data = resp.json()
    # Fallback should still return the seeded data
    assert len(data["history"]) >= 1
    assert data["ihsg_price"] == 7284.0
