from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Vaga(Base):
    __tablename__ = "vagas"
    __table_args__ = (CheckConstraint("tipo IN ('estagio', 'edital')", name="tipo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fonte: Mapped[str] = mapped_column(String(50))
    tipo: Mapped[str] = mapped_column(String(20), default="estagio", server_default="estagio")
    titulo: Mapped[str] = mapped_column(String(300))
    empresa: Mapped[str | None] = mapped_column(String(200))
    cidade: Mapped[str | None] = mapped_column(String(120))
    remoto: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    descricao: Mapped[str] = mapped_column(Text, default="", server_default="")
    url: Mapped[str] = mapped_column(String(2000))
    url_canonica: Mapped[str] = mapped_column(String(2000), unique=True)
    chave_conteudo: Mapped[str] = mapped_column(String(64), unique=True)
    publicada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    coletada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<Vaga {self.id} {self.fonte} {self.titulo!r}>"
