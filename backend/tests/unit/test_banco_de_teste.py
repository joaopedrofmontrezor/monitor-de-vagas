from sqlalchemy.engine import make_url

from app.config import settings


def test_testes_usam_um_banco_proprio_e_nao_o_do_app(engine_teste):
    banco_do_app = make_url(settings.database_url).database

    assert engine_teste.url.database.endswith("_teste")
    if not banco_do_app.endswith("_teste"):
        assert engine_teste.url.database == f"{banco_do_app}_teste"
    assert engine_teste.url.host == make_url(settings.database_url).host
