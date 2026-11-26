from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vagas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fonte", sa.String(length=50), nullable=False),
        sa.Column("tipo", sa.String(length=20), server_default="estagio", nullable=False),
        sa.Column("titulo", sa.String(length=300), nullable=False),
        sa.Column("empresa", sa.String(length=200), nullable=True),
        sa.Column("cidade", sa.String(length=120), nullable=True),
        sa.Column("remoto", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("descricao", sa.Text(), server_default="", nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("url_canonica", sa.String(length=2000), nullable=False),
        sa.Column("chave_conteudo", sa.String(length=64), nullable=False),
        sa.Column("publicada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "coletada_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("tipo IN ('estagio', 'edital')", name=op.f("ck_vagas_tipo")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vagas")),
        sa.UniqueConstraint("chave_conteudo", name=op.f("uq_vagas_chave_conteudo")),
        sa.UniqueConstraint("url_canonica", name=op.f("uq_vagas_url_canonica")),
    )
    op.create_index(op.f("ix_vagas_coletada_em"), "vagas", ["coletada_em"], unique=False)

    op.create_table(
        "execucoes_coleta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("coletor", sa.String(length=50), nullable=False),
        sa.Column(
            "inicio", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_coletadas", sa.Integer(), server_default="0", nullable=False),
        sa.Column("novas", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duplicadas", sa.Integer(), server_default="0", nullable=False),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_execucoes_coleta")),
    )
    op.create_index(
        op.f("ix_execucoes_coleta_coletor"), "execucoes_coleta", ["coletor"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_execucoes_coleta_coletor"), table_name="execucoes_coleta")
    op.drop_table("execucoes_coleta")
    op.drop_index(op.f("ix_vagas_coletada_em"), table_name="vagas")
    op.drop_table("vagas")
