# EVA Wiki MCP (Python)

MCP server for integration with EVA Wiki / EVA Team via their JSON-RPC 2.2 API (`/api/`).
Implemented in Python using the official `mcp` Python SDK.

## Features

- Read documents/articles by code (`CmfDocument.get`).
- Get document text only.
- Search documents by name (BQL filter + `CmfDocument.list`).
- Update document text + optional publish (`CmfDocument.update` + `CmfDocument.do_publish`).
- Download attachments (based on official EVA KB examples).
- List projects and user info.
- Raw EVA API call (`evawiki_raw_call`).
- Ping to check API availability and token validity (`evawiki_ping`).

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration (environment variables)

The server reads connection parameters from environment:

- `EVAWIKI_API_URL` — full URL to EVA JSON-RPC API, e.g. `https://eva.example.com/api/`.
- `EVAWIKI_API_TOKEN` — Bearer token for auth (from user profile in EVA).
- `EVAWIKI_VERIFY_SSL` — `true`/`false` (default `true`). Set `false` to disable TLS cert verification.
- `EVAWIKI_TIMEOUT` — HTTP request timeout in seconds (default `30`).

## MCP client config (Cursor / OpenAI Agents)

Copy `mcp.json.example` to `mcp.json` and fill in your URL and token. `mcp.json` is gitignored (contains secrets).

Example `mcpServers` block:

```json
{
  "mcpServers": {
    "evawiki": {
      "command": "python",
      "args": ["-m", "evawiki_mcp.server"],
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

- `evawiki_mcp/evawiki_client.py` — low-level EVA client (`EvaWikiClient`) over JSON-RPC 2.2.
- `evawiki_mcp/server.py` — MCP server (FastMCP) with tools:
  - `evawiki_get_document_by_code`
  - `evawiki_get_document_text`
  - `evawiki_list_documents` / search by name
  - `evawiki_update_document_text`
  - `evawiki_download_all_attachments`
  - `evawiki_list_projects`
  - `evawiki_find_user`
  - `evawiki_ping`
  - `evawiki_raw_call`

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

## Установка

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Конфигурация (переменные окружения)

Сервер читает параметры подключения из окружения:

- `EVAWIKI_API_URL` — полный URL до JSON‑RPC API EVA, например `https://eva.example.com/api/`.
- `EVAWIKI_API_TOKEN` — Bearer‑токен для авторизации (из личной карточки пользователя EVA).
- `EVAWIKI_VERIFY_SSL` — `true`/`false` (по умолчанию `true`). При `false` отключает проверку TLS‑сертификата.
- `EVAWIKI_TIMEOUT` — таймаут HTTP‑запросов в секундах (по умолчанию `30`).

## Пример client‑конфига MCP (Cursor / OpenAI Agents)

Скопируйте `mcp.json.example` в `mcp.json` и подставьте свои URL и токен. Файл `mcp.json` не попадает в git (содержит секреты).

Ниже пример блока `mcpServers`:

```json
{
  "mcpServers": {
    "evawiki": {
      "command": "python",
      "args": ["-m", "evawiki_mcp.server"],
      "env": {
        "EVAWIKI_API_URL": "https://eva.example.com/api/",
        "EVAWIKI_API_TOKEN": "ВАШ_ТОКЕН",
        "EVAWIKI_VERIFY_SSL": "false"
      }
    }
  }
}
```

## Структура кода

- `evawiki_mcp/evawiki_client.py` — низкоуровневый клиент EVA (`EvaWikiClient`) поверх JSON-RPC 2.2.
- `evawiki_mcp/server.py` — MCP‑сервер на базе `FastMCP` с инструментами (см. выше).
