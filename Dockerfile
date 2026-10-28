# Immagine unica: API FastAPI + frontend compilato (ADR 0009).

# --- Frontend: compilazione dei file statici --------------------------------
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-fund --no-audit
COPY frontend/ ./
RUN npm run build

# --- Backend: ambiente virtuale con le sole dipendenze di produzione --------
FROM python:3.12-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY backend/src ./src
RUN uv sync --locked --no-dev --no-editable

# --- Immagine finale ---------------------------------------------------------
FROM python:3.12-slim AS runtime

# Librerie di sistema di WeasyPrint (Pango, HarfBuzz) e font incorporati (ADR 0008);
# sqlite3 per i backup coerenti con `.backup` (ADR 0003).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz-subset0 \
        fonts-dejavu-core \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --system --uid 10001 --user-group --home-dir /app --no-create-home app \
    && mkdir -p /data \
    && chown app:app /data

WORKDIR /app
COPY --from=backend /app/.venv /app/.venv
COPY --from=frontend /build/dist /app/static
COPY docker/entrypoint.sh /app/entrypoint.sh

ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    GSP_DATABASE_URL=sqlite:////data/gym_split_planner.db \
    GSP_STATIC_DIR=/app/static

USER app
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"]

ENTRYPOINT ["/app/entrypoint.sh"]

ARG VERSION=dev
LABEL org.opencontainers.image.title="Gym Split Planner" \
      org.opencontainers.image.description="Banca dati degli esercizi e creazione di schede di allenamento" \
      org.opencontainers.image.source="https://github.com/Cruciat/gym_split_planner" \
      org.opencontainers.image.licenses="NOASSERTION" \
      org.opencontainers.image.version="${VERSION}"
