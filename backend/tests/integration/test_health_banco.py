import pytest

pytestmark = pytest.mark.integracao


def test_health_com_postgres_de_verdade(client, banco_disponivel):
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json()["banco"] == "ok"
