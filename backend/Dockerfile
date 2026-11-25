FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1) Só o pyproject primeiro: as dependências ficam numa camada em cache e só
#    são reinstaladas quando o pyproject muda, não a cada linha de código alterada.
COPY pyproject.toml ./
RUN mkdir app && touch app/__init__.py && pip install -e ".[dev]"

# 2) Depois o código. Em desenvolvimento o compose monta ./backend por cima disto.
COPY . .

# Usuário sem privilégios: o container não roda como root
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
