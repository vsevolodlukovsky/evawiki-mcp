# EVA Wiki MCP (Python)

MCP server for integration with EVA Wiki / EVA Team via their JSON-RPC 2.2 API (`/api/`).
Implemented in Python using the official `mcp` Python SDK.

## Quickstart

### Install

```bash
pipx install evawiki-mcp
```

Or: `pip install evawiki-mcp`, or install from GitHub:

```bash
pip install git+https://github.com/vsevolodlukovsky/evawiki-mcp.git
pipx install git+https://github.com/vsevolodlukovsky/evawiki-mcp.git
```

### Run

Verify it runs:

```bash
evawiki-mcp --help
evawiki-mcp
```

Without arguments the server runs in stdio mode for an MCP client.

### Config for MCP client

In your MCP client (Cursor, etc.) configure the `evawiki-mcp` command and environment variables. See [examples/mcp.json](examples/mcp.json) for a template.

```json
{
  "mcpServers": {
    "evawiki": {
      "command": "evawiki-mcp",
      "env": {
        "EVAWIKI_API_URL": "https://eva.example.com/api/",
        "EVAWIKI_API_TOKEN": "YOUR_TOKEN",
        "EVAWIKI_VERIFY_SSL": "false"
      }
    }
  }
}
```

Alternative (without installing the package): `"command": "python", "args": ["-m", "evawiki_mcp.server"]` with the same `env`.

### Troubleshooting

- **Python:** requires 3.10+.
- **Command not found:** after `pipx install` or `pip install`, make sure `evawiki-mcp` is on PATH (restart the terminal or run `pipx ensurepath`).
- **EVAWIKI_API_URL / EVAWIKI_API_TOKEN missing:** the server will fail on the first tool call if they are not set — configure them in your MCP client.
- **Stdio:** the server communicates over stdin/stdout; do not run it interactively and type into the same terminal.

### Docker / HTTP mode

The server supports two transports: **stdio** (default, for local MCP clients) and **streamable-http** (for running as a network service in Docker or a VM).

> **Heads up — stdio vs HTTP env vars.** In **stdio** mode the MCP client (Cursor, etc.) starts the server process itself, so the `env` block from the client config is propagated to the server. In **HTTP** mode the server is a separate process (typically a Docker container), and the client only talks to it via `url`. The client-side `env` block is **ignored**. `EVAWIKI_API_URL` / `EVAWIKI_API_TOKEN` must be set on the server side — via `.env` for Compose, `--env-file` for `docker run`, or exported shell env for a bare `evawiki-mcp --transport http`. If they are missing, the server logs a `[WARN]` to stderr on startup and every tool call fails with `EVAWIKI_API_URL is not set`.

#### Quick start with Docker Compose

```bash
cp .env.example .env
# edit .env — set EVAWIKI_API_URL and EVAWIKI_API_TOKEN
docker compose up -d --build
```

The server listens on `http://localhost:8000/mcp`.

#### Quick start with docker run

```bash
docker build -t evawiki-mcp .
docker run --rm -p 127.0.0.1:8000:8000 --env-file .env evawiki-mcp
```

#### HTTP mode without Docker

```bash
evawiki-mcp --transport http
# or via env vars:
MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8000 evawiki-mcp
```

#### MCP client config (HTTP)

```json
{
  "mcpServers": {
    "evawiki": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

#### CLI options

| Flag | Env var | Default | Description |
|------|---------|---------|-------------|
| `--transport` | `MCP_TRANSPORT` | `stdio` | `stdio` or `http` |
| `--host` | `MCP_HOST` | `127.0.0.1` | Listen address (HTTP mode) |
| `--port` | `MCP_PORT` | `8000` | Listen port (HTTP mode) |
| `--path` | `MCP_PATH` | `/mcp` | HTTP endpoint path |

#### Security notes

The HTTP transport has **no built-in authentication**. Do not expose it to the public internet directly. Recommended options:

- Bind to `127.0.0.1` and access via SSH tunnel.
- Place behind a reverse proxy (nginx / traefik) with basic auth or OAuth.
- For single-user local use, prefer stdio mode.

---

## Features

- Read documents/articles by code (`CmfDocument.get`).
- Get document text only.
- Search documents by name (BQL filter + `CmfDocument.list`).
- Update document text + optional publish (`CmfDocument.update` + `CmfDocument.do_publish`).
- Download attachments (based on official EVA KB examples).
- List projects and user info.
- Raw EVA API call (`evawiki_raw_call`).
- Ping to check API availability and token validity (`evawiki_ping`).
- **Document tree and hierarchy:** get full tree (`evawiki_get_document_tree`), list sections/folders (`evawiki_list_sections`), get one section with children (`evawiki_get_section`), move document (`evawiki_move_document`), document with breadcrumb and siblings (`evawiki_get_document_with_context`).

## Installation (from source)

```bash
git clone https://github.com/vsevolodlukovsky/evawiki-mcp.git
cd evawiki-mcp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Configuration (environment variables)

The server reads connection parameters from environment:

- `EVAWIKI_API_URL` — full URL to EVA JSON-RPC API, e.g. `https://eva.example.com/api/`.
- `EVAWIKI_API_TOKEN` — Bearer token for auth (from user profile in EVA).
- `EVAWIKI_VERIFY_SSL` — `true`/`false` (default `true`). Set `false` to disable TLS cert verification.
- `EVAWIKI_TIMEOUT` — HTTP request timeout in seconds (default `30`).

## MCP client config (Cursor / OpenAI Agents)

Use `evawiki-mcp` as command, or copy [examples/mcp.json](examples/mcp.json) and fill in your URL and token.

Example `mcpServers` block:

```json
{
  "mcpServers": {
    "evawiki": {
      "command": "evawiki-mcp",
      "env": {
        "EVAWIKI_API_URL": "https://eva.example.com/api/",
        "EVAWIKI_API_TOKEN": "YOUR_TOKEN",
        "EVAWIKI_VERIFY_SSL": "false"
      }
    }
  }
}
```

## Code structure

- `src/evawiki_mcp/evawiki_client.py` — low-level EVA client (`EvaWikiClient`) over JSON-RPC 2.2.
- `src/evawiki_mcp/server.py` — MCP server (FastMCP) with tools:
  - `evawiki_get_document_by_code`, `evawiki_get_document_text`
  - `evawiki_list_documents` / search by name
  - `evawiki_update_document_text`, `evawiki_download_all_attachments`
  - `evawiki_list_projects`, `evawiki_find_user`, `evawiki_ping`, `evawiki_raw_call`
  - **Tree/hierarchy:** `evawiki_get_document_tree`, `evawiki_list_sections`, `evawiki_get_section`, `evawiki_move_document`, `evawiki_get_document_with_context`

All tools use `EvaWikiClient`, which:

- Adds `jsonrpc: "2.2"` and `callid` (UUID).
- Sends `args`, `kwargs`, `fields`, `filter`, `flags`, `no_meta` per EVA docs.
- Raises clear exceptions when EVA returns `error`.

---

# EVA Wiki MCP (Python) — русский

MCP‑сервер для интеграции с EVA Wiki/EVA Team через их JSON‑RPC 2.2 API (`/api/`).
Реализован на Python с использованием официального `mcp` Python SDK.

## Возможности

- Чтение документов/статей по коду (`CmfDocument.get`).
- Получение только текста документа.
- Поиск документов по имени (BQL‑фильтр и `CmfDocument.list`).
- Обновление текста документа + (опционально) публикация (`CmfDocument.update` + `CmfDocument.do_publish`).
- Загрузка и скачивание вложений (по мотивам примеров из официальных KB EVA).
- Получение списка проектов и информации о пользователях.
- Универсальный «сырой» вызов EVA API (`evawiki_raw_call`).
- Проверка доступности API и валидности токена (`evawiki_ping`).
- **Дерево документов и иерархия:** полное дерево (`evawiki_get_document_tree`), список разделов (`evawiki_list_sections`), один раздел с содержимым (`evawiki_get_section`), перемещение документа (`evawiki_move_document`), документ с хлебными крошками и соседями (`evawiki_get_document_with_context`).

## Установка

```bash
pipx install evawiki-mcp
# или: pip install git+https://github.com/vsevolodlukovsky/evawiki-mcp.git
```

Из исходников: клонировать репозиторий, `pip install -e ".[dev]"`.

## Конфигурация (переменные окружения)

Сервер читает параметры подключения из окружения:

- `EVAWIKI_API_URL` — полный URL до JSON‑RPC API EVA, например `https://eva.example.com/api/`.
- `EVAWIKI_API_TOKEN` — Bearer‑токен для авторизации (из личной карточки пользователя EVA).
- `EVAWIKI_VERIFY_SSL` — `true`/`false` (по умолчанию `true`). При `false` отключает проверку TLS‑сертификата.
- `EVAWIKI_TIMEOUT` — таймаут HTTP‑запросов в секундах (по умолчанию `30`).

## Пример client‑конфига MCP (Cursor / OpenAI Agents)

Используйте команду `evawiki-mcp` и переменные окружения. Пример в [examples/mcp.json](examples/mcp.json).

## Docker / HTTP‑режим

Сервер поддерживает два транспорта: **stdio** (по умолчанию, для локальных MCP‑клиентов) и **streamable‑http** (для работы как сетевой сервис в Docker или на VM).

> **Важно — env переменные в stdio vs HTTP.** В **stdio** клиент (Cursor и т.п.) сам запускает процесс сервера, поэтому блок `env` из конфига клиента пробрасывается в сервер. В **HTTP** сервер — это отдельный процесс (обычно Docker‑контейнер), клиент ходит к нему только по `url`. Блок `env` в клиент‑конфиге **игнорируется**. `EVAWIKI_API_URL` / `EVAWIKI_API_TOKEN` нужно задавать на стороне сервера: через `.env` (Compose), `--env-file` (`docker run`) или обычный экспорт для `evawiki-mcp --transport http`. Если переменные не заданы, сервер печатает `[WARN]` в stderr при старте, а каждый tool‑call падает с `EVAWIKI_API_URL is not set`.

### Быстрый старт с Docker Compose

```bash
cp .env.example .env
# отредактируйте .env — укажите EVAWIKI_API_URL и EVAWIKI_API_TOKEN
docker compose up -d --build
```

Сервер слушает `http://localhost:8000/mcp`.

### Быстрый старт с docker run

```bash
docker build -t evawiki-mcp .
docker run --rm -p 127.0.0.1:8000:8000 --env-file .env evawiki-mcp
```

### HTTP‑режим без Docker

```bash
evawiki-mcp --transport http
# или через переменные окружения:
MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8000 evawiki-mcp
```

### Конфиг MCP‑клиента (HTTP)

```json
{
  "mcpServers": {
    "evawiki": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Параметры CLI

| Флаг | Переменная | По умолчанию | Описание |
|------|------------|--------------|----------|
| `--transport` | `MCP_TRANSPORT` | `stdio` | `stdio` или `http` |
| `--host` | `MCP_HOST` | `127.0.0.1` | Адрес прослушивания (HTTP) |
| `--port` | `MCP_PORT` | `8000` | Порт (HTTP) |
| `--path` | `MCP_PATH` | `/mcp` | Путь HTTP‑эндпоинта |

### Безопасность

HTTP‑транспорт **не имеет встроенной авторизации**. Не выставляйте его в открытый интернет напрямую. Рекомендации:

- Слушайте на `127.0.0.1` и ходите через SSH‑туннель.
- Ставьте reverse‑proxy (nginx / traefik) с basic auth или OAuth.
- Для одного пользователя локально — используйте stdio.

## Структура кода

- `src/evawiki_mcp/evawiki_client.py` — низкоуровневый клиент EVA (`EvaWikiClient`) поверх JSON-RPC 2.2.
- `src/evawiki_mcp/server.py` — MCP‑сервер на базе `FastMCP` с инструментами (в т.ч. дерево и иерархия — см. выше).
