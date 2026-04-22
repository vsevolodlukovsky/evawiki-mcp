FROM python:3.12-slim-bookworm

RUN useradd --create-home app

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_COLOR=1 \
    PIP_PROGRESS_BAR=off

RUN pip install --no-cache-dir .

ENV MCP_TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    MCP_PATH=/mcp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import socket,sys; s=socket.create_connection(('127.0.0.1',8000),2); s.close()" || exit 1

USER app

ENTRYPOINT ["evawiki-mcp"]
