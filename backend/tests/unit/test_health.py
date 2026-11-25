from sqlalchemy.exc import OperationalError


class SessaoOk:
    def execute(self, _sql):
        return None


class SessaoQuebrada:
    def execute(self, _sql):
        raise OperationalError("SELECT 1", {}, Exception("conexão recusada"))


def test_health_ok_quando_banco_responde(client, sobrescrever_db):
    sobrescrever_db(SessaoOk())

    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "banco": "ok"}


def test_health_503_quando_banco_cai(client, sobrescrever_db):
    sobrescrever_db(SessaoQuebrada())

    resp = client.get("/health")

    assert resp.status_code == 503
    assert resp.json() == {"status": "erro", "banco": "indisponivel"}


def test_health_aparece_na_documentacao(client):
    assert "/health" in client.get("/openapi.json").json()["paths"]
