from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ExecucaoColeta(Base):
    __tablename__ = "execucoes_coleta"

    id: Mapped[int] = mapped_column(primary_key=True)
    coletor: Mapped[str] = mapped_column(String(50), index=True)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_coletadas: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    novas: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    duplicadas: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    erro: Mapped[str | None] = mapped_column(Text)
