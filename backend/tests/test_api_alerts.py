def test_list_and_get_alert(client, mock_llm):
    create = client.post("/api/analyze", json={"text": "phishing campaign via evil.example.com"})
    alert_id = create.get_json()["id"]

    listed = client.get("/api/alerts")
    assert listed.status_code == 200
    assert any(a["id"] == alert_id for a in listed.get_json())

    detail = client.get(f"/api/alerts/{alert_id}")
    assert detail.status_code == 200
    assert detail.get_json()["id"] == alert_id


def test_get_alert_404(client):
    assert client.get("/api/alerts/does-not-exist").status_code == 404


def test_delete_alert(client, mock_llm):
    create = client.post("/api/analyze", json={"text": "some threat text"})
    alert_id = create.get_json()["id"]
    assert client.delete(f"/api/alerts/{alert_id}").status_code == 204
    assert client.get(f"/api/alerts/{alert_id}").status_code == 404


def test_delete_alert_404(client):
    assert client.delete("/api/alerts/does-not-exist").status_code == 404
