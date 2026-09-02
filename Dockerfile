# Python 3.13 runtime; digest is pinned after the P0-02 verification run.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN python -m pip install --no-cache-dir "uv==0.10.0"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY manage.py ./
COPY palvelut ./palvelut

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn_worker.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2", "palvelut.asgi:application"]
