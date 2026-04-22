# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-04-22

### Added

- `streamable-http` transport alongside stdio. CLI accepts `--transport {stdio,http}`, `--host`, `--port`, `--path` with env fallbacks `MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`, `MCP_PATH`. Default endpoint is `/mcp`.
- `Dockerfile` (python:3.12-slim-bookworm), non-root user, socket-based healthcheck that honors `MCP_PORT`. Image defaults to HTTP on `0.0.0.0:8000/mcp`.
- `docker-compose.yml` bound to `127.0.0.1:8000` for safe local defaults, `.env`-driven configuration, `.env.example` template, `.dockerignore`.
- README sections (EN + RU) covering Docker Compose / `docker run` / HTTP-without-Docker workflows, MCP client HTTP config, CLI options table, and security notes.

### Changed

- Default transport remains `stdio` — backward compatible with existing `pipx`/`pip` installations.
- `MCP_TRANSPORT` and `MCP_PORT` env values are validated on startup with clear error messages (invalid transport no longer silently falls back to stdio; invalid port no longer crashes with a bare `ValueError`).

## [0.2.1] - 2026-02-25

### Fixed

- `build_tree` now uses correct wiki navigation tree (`tree_parent_id`) instead of EVA object hierarchy (`parent_id`). Previously returned incorrect flat structure for documents with `parent_id == project_id`.

### Added

- `EvaWikiClient.list_wiki_roots(project_id)` — fetch root-level wiki tree nodes (`tree_parent_id == null`).
- `EvaWikiClient.list_wiki_children(parent_id, project_id)` — fetch direct wiki children via `tree_parent_id` filter.
- MCP tool `evawiki_get_wiki_children(node_id, project_code)` — navigate wiki tree node by node without loading the full tree.
- `evawiki_get_section` now also returns `wiki_children` (via `tree_parent_id`) alongside existing `child_documents` (via `parent_id`).

## [0.2.0] - 2025-02-25

### Added

- Document tree and hierarchy tools: `evawiki_get_document_tree`, `evawiki_list_sections`, `evawiki_get_section`, `evawiki_move_document`, `evawiki_get_document_with_context`.
- Client helpers: `list_folders`, `list_documents_for_tree`, `build_tree`, `get_breadcrumb`, `_list_all` (paginated fetch).

## [0.1.0] - 2025-02-18

### Added

- Initial release: MCP server for EVA Wiki / EVA Team.
- Tools: get document by code, document text, list/search documents, update text, download attachments, list projects, find user, ping, raw API call.
- CLI entry point `evawiki-mcp` (stdio).
- Configuration via environment: `EVAWIKI_API_URL`, `EVAWIKI_API_TOKEN`, `EVAWIKI_VERIFY_SSL`, `EVAWIKI_TIMEOUT`.
