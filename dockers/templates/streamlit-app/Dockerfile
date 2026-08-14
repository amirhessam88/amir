# Multi-stage-ish Streamlit template — build from repo root:
#   docker build -f dockers/templates/streamlit-app/Dockerfile .
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_SYSTEM_PYTHON=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY libs ./libs
COPY apps ./apps
COPY projects ./projects
COPY assets/pdf/papers ./assets/pdf/papers

RUN uv sync --locked --all-groups --no-dev

EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "apps/papers-rag/src/papers_rag/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
