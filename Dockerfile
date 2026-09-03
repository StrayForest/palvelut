# Frontend dependency builder. Reuse the already pinned Playwright image so Node/npm are immutable too.
FROM mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e AS frontend

WORKDIR /frontend
COPY frontend/package.json ./
COPY frontend/app.css ./app.css
COPY templates /templates
RUN npm install --omit=optional --ignore-scripts \
    && mkdir -p /frontend-dist/vendor /frontend-dist/css \
    && cp node_modules/htmx.org/dist/htmx.min.js /frontend-dist/vendor/htmx.min.js \
    && cp node_modules/alpinejs/dist/cdn.min.js /frontend-dist/vendor/alpine.min.js \
    && npx @tailwindcss/cli -i ./app.css -o /frontend-dist/css/app.css --minify

# Python 3.13 slim, resolved 2026-09-03; immutable digest is authoritative.
FROM python:3.13-slim@sha256:9d2e5553305c7c7b0097999bb17187c69b921ccd6bc9d40e4bb5ebe652c00285

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN python -m pip install --no-cache-dir "uv==0.10.0"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY manage.py ./
COPY palvelut ./palvelut
COPY templates ./templates
COPY locale ./locale
COPY --from=frontend /frontend-dist ./static

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn_worker.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2", "palvelut.asgi:application"]
