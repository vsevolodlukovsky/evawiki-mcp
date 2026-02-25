from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from .evawiki_client import EvaApiError, EvaWikiClient


mcp = FastMCP("EVA Wiki MCP")


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_client() -> EvaWikiClient:
    """
    Initialize EVA Wiki client from environment variables.

    EVAWIKI_API_URL   - full URL to /api/, e.g. https://eva.example.com/api/
    EVAWIKI_API_TOKEN - Bearer token.
    EVAWIKI_VERIFY_SSL - true/false, default true.
    EVAWIKI_TIMEOUT    - HTTP request timeout in seconds, default 30.
    """
    base_url = os.environ.get("EVAWIKI_API_URL")
    if not base_url:
        raise RuntimeError("EVAWIKI_API_URL is not set")

    token = os.environ.get("EVAWIKI_API_TOKEN")
    if not token:
        raise RuntimeError("EVAWIKI_API_TOKEN is not set")

    verify_ssl = _env_bool("EVAWIKI_VERIFY_SSL", True)
    timeout = _env_float("EVAWIKI_TIMEOUT", 30.0)

    return EvaWikiClient(base_url=base_url, token=token, verify_ssl=verify_ssl, timeout=timeout)


def _handle_eva_error(exc: EvaApiError) -> None:
    # Re-raise as RuntimeError with clear message for MCP client
    raise RuntimeError(f"EVA API error in {exc.method}: {exc.code} {exc.message}") from exc


@mcp.tool()
def evawiki_get_document_by_code(code: str) -> Dict[str, Any]:
    """
    Get document by code (DOC-000066 etc.), including text and basic fields.
    """
    client = get_client()
    try:
        kwargs = {"filter": ["code", "==", code]}
        data = client.call("CmfDocument.get", kwargs=kwargs, fields=["code", "name", "text"])
        return {"document": data.get("result")}
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_get_document_text(code: str) -> Dict[str, Any]:
    """
    Get document text only by code.
    """
    client = get_client()
    try:
        kwargs = {"filter": ["code", "==", code], "fields": ["text"]}
        # fields can be passed via kwargs as in EVA examples
        data = client.call("CmfDocument.get", kwargs=kwargs)
        result = data.get("result") or {}
        return {"code": code, "text": result.get("text")}
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_list_documents(
    filter_json: Optional[Union[str, List, Dict]] = None,
    fields_comma: Optional[Union[str, List[str]]] = None,
    slice_start: int = 0,
    slice_limit: int = 50,
) -> Dict[str, Any]:
    """
    List documents by BQL filter.

    filter_json — JSON string or object for BQL filter, e.g. ["name","LIKE","%text%"].
    fields_comma — comma-separated fields or empty for code,name.
    slice_start, slice_limit — pagination.
    """
    client = get_client()
    try:
        kwargs: Dict[str, Any] = {"slice": [slice_start, slice_start + slice_limit]}
        if filter_json is not None:
            if isinstance(filter_json, (list, dict)):
                kwargs["filter"] = filter_json
            elif isinstance(filter_json, str) and filter_json.strip():
                s = filter_json.strip()
                if s.startswith("[") or s.startswith("{"):
                    try:
                        kwargs["filter"] = json.loads(s)
                    except json.JSONDecodeError:
                        raise RuntimeError(f"filter_json: invalid JSON: {s[:50]}...")
                else:
                    # Simple format: field,op,value → ["field","op","value"]
                    parts = [p.strip().strip("\"'") for p in s.split(",", 2)]
                    if len(parts) >= 3:
                        kwargs["filter"] = parts
        effective_fields = ["code", "name"]
        if fields_comma is not None:
            if isinstance(fields_comma, str) and fields_comma.strip():
                effective_fields = [f.strip() for f in fields_comma.split(",")]
            elif isinstance(fields_comma, list):
                effective_fields = list(fields_comma)

        data = client.call("CmfDocument.list", kwargs=kwargs, fields=effective_fields, no_meta=True)
        return {"items": data.get("result", [])}
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_search_documents(
    query: str,
    project_code: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Search documents by name substring.

    Builds BQL filter ['name', 'LIKE', '%query%'].
    Optionally filter by project_code if your setup supports it.
    """
    client = get_client()
    try:
        # Base name filter
        name_filter: Any = ["name", "LIKE", f"%{query}%"]
        combined_filter: Any = name_filter

        # Project filter can be added if config supports project.code
        # if project_code:
        #     combined_filter = [[name_filter], ["project.code", "==", project_code]]

        kwargs: Dict[str, Any] = {
            "filter": combined_filter,
            "slice": [offset, offset + limit],
        }

        data = client.call("CmfDocument.list", kwargs=kwargs, fields=["code", "name"], no_meta=True)
        return {"items": data.get("result", [])}
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_update_document_text(code: str, new_text: str, publish: bool = False) -> Dict[str, Any]:
    """
    Update document text (draft) and optionally publish.
    """
    client = get_client()
    try:
        # 1. Get document by code to get id
        doc_data = client.call(
            "CmfDocument.get",
            kwargs={"filter": ["code", "==", code]},
        )
        doc = doc_data.get("result")
        if not doc:
            raise RuntimeError(f"Document with code {code} not found")
        doc_id = doc.get("id")

        # 2. Update draft text
        client.call(
            "CmfDocument.update",
            args=[doc_id],
            kwargs={"text_draft": new_text},
        )

        published = False
        if publish:
            client.call(
                "CmfDocument.do_publish",
                args=[doc_id],
            )
            published = True

        return {"code": code, "id": doc_id, "published": published}
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_download_all_attachments(doc_code: str, admin_mode: bool = False) -> Dict[str, Any]:
    """
    Get link to zip archive with all document attachments.

    Returns relative and full URL of .zip file.
    admin_mode — if True, request uses admin rights (may be required for some attachments).
    """
    client = get_client()
    try:
        # 1. Get document id by code
        doc_data = client.call(
            "CmfDocument.get",
            kwargs={"filter": ["code", "==", doc_code]},
        )
        doc = doc_data.get("result")
        if not doc:
            raise RuntimeError(f"Document with code {doc_code} not found")
        doc_id = doc.get("id")

        # 2. Request download_all_attachment
        flags = {"admin_mode": True} if admin_mode else None
        data = client.call(
            "CmfDocument.download_all_attachment",
            args=[doc_id],
            flags=flags,
        )
        zip_url = data.get("result")

        # base_url is usually https://domain/api/, strip /api/ to get domain
        base_url = client.base_url
        if base_url.rstrip("/").endswith("/api"):
            domain = base_url.rstrip("/")[:-4]
        else:
            domain = base_url.rstrip("/")

        full_url = f"{domain}/{zip_url.lstrip('/')}" if zip_url else None
        return {"zip_url": zip_url, "full_url": full_url}
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_list_projects(
    filter_json: Optional[Union[str, List, Dict]] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List projects (code, name) with optional BQL filter.
    filter_json — JSON string for BQL filter, e.g. ["code","!=",null].
    """
    client = get_client()
    try:
        if filter_json is None:
            effective_filter = ["code", "!=", None]
        elif isinstance(filter_json, (list, dict)):
            effective_filter = filter_json
        elif isinstance(filter_json, str) and filter_json.strip():
            effective_filter = json.loads(filter_json)
        else:
            effective_filter = ["code", "!=", None]
        kwargs: Dict[str, Any] = {
            "filter": effective_filter,
            "slice": [offset, offset + limit],
        }
        data = client.call("CmfProject.list", kwargs=kwargs, fields=["code", "name"], no_meta=True)
        return {"items": data.get("result", [])}
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_find_user(login_or_email: str) -> Dict[str, Any]:
    """
    Find user by login.
    """
    client = get_client()
    try:
        kwargs = {"filter": ["login", "==", login_or_email], "fields": ["name", "login", "email"]}
        data = client.call("CmfPerson.get", kwargs=kwargs)
        return {"user": data.get("result")}
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_ping() -> Dict[str, Any]:
    """
    Check EVA API availability and token validity.

    Performs lightweight CmfPerson.list with small slice.
    """
    client = get_client()
    try:
        kwargs = {
            "filter": ["login", "!=", None],
            "fields": ["id"],
            "slice": [0, 1],
        }
        data = client.call("CmfPerson.list", kwargs=kwargs, no_meta=True)
        return {"ok": True, "sample": data.get("result", [])}
    except EvaApiError as exc:
        _handle_eva_error(exc)


# ---------------------------------------------------------------------------
# Hierarchy / tree tools
# ---------------------------------------------------------------------------


@mcp.tool()
def evawiki_get_document_tree(
    project_code: Optional[str] = None,
    max_depth: int = 10,
) -> Dict[str, Any]:
    """
    Build full document tree (folders + documents) for a project.

    project_code — if given, scope to one project; otherwise all accessible projects.
    max_depth — max nesting depth (default 10).

    Returns a list of root nodes, each with nested children.
    Node: {type: "folder"|"document", code, name, children: [...]}.
    """
    client = get_client()
    try:
        project_id: Optional[str] = None
        if project_code:
            pdata = client.call(
                "CmfProject.get",
                kwargs={"filter": ["code", "==", project_code]},
                fields=["id", "code", "name"],
            )
            proj = pdata.get("result")
            if not proj:
                raise RuntimeError(f"Project with code {project_code} not found")
            project_id = proj["id"]

        tree = client.build_tree(project_id=project_id, max_depth=max_depth)
        return {"tree": tree, "project_code": project_code}
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_list_sections(
    project_code: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List all folders (sections) — flat list with parent info.

    project_code — optional, scope to one project.
    Returns [{code, name, parent_id, project_id, id}, ...].
    """
    client = get_client()
    try:
        project_id: Optional[str] = None
        if project_code:
            pdata = client.call(
                "CmfProject.get",
                kwargs={"filter": ["code", "==", project_code]},
                fields=["id"],
            )
            proj = pdata.get("result")
            if not proj:
                raise RuntimeError(f"Project with code {project_code} not found")
            project_id = proj["id"]

        kwargs: Dict[str, Any] = {"slice": [offset, offset + limit]}
        if project_id:
            kwargs["filter"] = ["project_id", "==", project_id]

        fields = ["code", "name", "parent_id", "project_id", "id"]
        data = client.call("CmfFolder.list", kwargs=kwargs, fields=fields, no_meta=True)
        items = [r for r in (data.get("result") or []) if r.get("_acl_obj") != "deny"]
        return {"items": items, "count": len(items)}
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_get_section(code: str) -> Dict[str, Any]:
    """
    Get one folder (section) by code, with its direct children (sub-folders + documents).

    Returns the folder info plus lists of child_folders and child_documents.
    """
    client = get_client()
    try:
        fdata = client.call(
            "CmfFolder.get",
            kwargs={"filter": ["code", "==", code]},
            fields=["code", "name", "parent_id", "project_id", "id"],
        )
        folder = fdata.get("result")
        if not folder:
            raise RuntimeError(f"Folder with code {code} not found")
        folder_id = folder["id"]

        child_folders = client._list_all(
            "CmfFolder.list",
            ["code", "name", "parent_id", "id"],
            extra_filter=["parent_id", "==", folder_id],
        )
        child_docs = client._list_all(
            "CmfDocument.list",
            ["code", "name", "parent_id", "id"],
            extra_filter=["parent_id", "==", folder_id],
        )

        return {
            "folder": folder,
            "child_folders": child_folders,
            "child_documents": child_docs,
        }
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_move_document(doc_code: str, target_parent_id: str) -> Dict[str, Any]:
    """
    Move a document to another parent (folder, document, or project).

    doc_code — code of the document to move (e.g. DOC-000066).
    target_parent_id — full id of the new parent
        (e.g. "CmfFolder:uuid..." or "CmfProject:uuid..." or "CmfDocument:uuid...").
    """
    client = get_client()
    try:
        doc_data = client.call(
            "CmfDocument.get",
            kwargs={"filter": ["code", "==", doc_code]},
            fields=["id", "parent_id"],
        )
        doc = doc_data.get("result")
        if not doc:
            raise RuntimeError(f"Document with code {doc_code} not found")
        doc_id = doc["id"]
        old_parent = doc.get("parent_id")

        client.call(
            "CmfDocument.update",
            args=[doc_id],
            kwargs={"parent_id": target_parent_id},
        )

        return {
            "doc_code": doc_code,
            "doc_id": doc_id,
            "old_parent_id": old_parent,
            "new_parent_id": target_parent_id,
        }
    except EvaApiError as exc:
        _handle_eva_error(exc)


@mcp.tool()
def evawiki_get_document_with_context(code: str) -> Dict[str, Any]:
    """
    Get document together with its breadcrumb path and sibling documents.

    Returns:
    - document: basic document fields
    - breadcrumb: list from root project down to the document's parent
    - siblings: other documents/folders sharing the same parent
    """
    client = get_client()
    try:
        doc_data = client.call(
            "CmfDocument.get",
            kwargs={"filter": ["code", "==", code]},
            fields=["code", "name", "parent_id", "project_id", "id"],
        )
        doc = doc_data.get("result")
        if not doc:
            raise RuntimeError(f"Document with code {code} not found")

        parent_id = doc.get("parent_id", "")
        breadcrumb = client.get_breadcrumb(parent_id) if parent_id else []

        siblings_docs = client._list_all(
            "CmfDocument.list",
            ["code", "name", "id"],
            extra_filter=["parent_id", "==", parent_id],
        ) if parent_id else []
        siblings_folders = client._list_all(
            "CmfFolder.list",
            ["code", "name", "id"],
            extra_filter=["parent_id", "==", parent_id],
        ) if parent_id else []

        sibling_docs_filtered = [s for s in siblings_docs if s.get("id") != doc["id"]]

        return {
            "document": doc,
            "breadcrumb": breadcrumb,
            "sibling_documents": sibling_docs_filtered,
            "sibling_folders": siblings_folders,
        }
    except EvaApiError as exc:
        _handle_eva_error(exc)


def _parse_json_param(val: Optional[Union[str, Dict, List]]) -> Any:
    """Accept JSON string or already-parsed dict/list."""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str) and val.strip():
        return json.loads(val)
    return None


@mcp.tool()
def evawiki_raw_call(
    method: str,
    kwargs_json: Optional[Any] = None,
    args_json: Optional[Any] = None,
    fields_json: Optional[Any] = None,
    filter_json: Optional[Any] = None,
    flags_json: Optional[Any] = None,
    no_meta: bool = False,
) -> Dict[str, Any]:
    """
    Low-level call to any EVA API method.

    kwargs_json, args_json, fields_json, filter_json, flags_json — JSON strings or objects.
    admin_mode is NOT added by default; pass it explicitly in flags_json if needed.
    """
    client = get_client()
    try:
        kwargs = _parse_json_param(kwargs_json)
        args = _parse_json_param(args_json)
        fields = _parse_json_param(fields_json)
        filter_val = _parse_json_param(filter_json)
        flags = _parse_json_param(flags_json)

        data = client.call(
            method,
            kwargs=kwargs,
            args=args,
            fields=fields,
            filter=filter_val,
            flags=flags,
            no_meta=no_meta if no_meta else None,
        )
        return {"raw": data}
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in parameter: {e}") from e
    except EvaApiError as exc:
        _handle_eva_error(exc)


if __name__ == "__main__":
    # Run MCP server via stdio
    mcp.run()
