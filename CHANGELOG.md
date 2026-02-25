# Changelog

All notable changes to this project will be documented in this file.

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
