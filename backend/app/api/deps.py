"""Dependências compartilhadas pelas rotas.

As rotas recebem o banco via `Depends(get_db)`. Nos testes, trocamos essa
dependência com `app.dependency_overrides[get_db] = ...` e não precisamos de Postgres.
`get_usuario_atual` entra aqui na issue #18.
"""

from app.db import get_session

get_db = get_session

__all__ = ["get_db"]
