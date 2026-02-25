from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


class EvaApiError(Exception):
    """Top-level exception for EVA JSON-RPC errors."""

    def __init__(self, method: str, code: Any, message: str) -> None:
        self.method = method
        self.code = code
        self.message = message
        super().__init__(f"EVA API error in {method}: {code} {message}")


@dataclass
class EvaWikiClient:
    """
    EVA Wiki client over JSON-RPC 2.2.

    Handles:
    - payload format per EVA API docs;
    - headers (Content-Type, Authorization);
    - HTTP errors and `error` field in response;
    - options: fields, filter, flags, no_meta.
    """

    base_url: str
    token: str
    verify_ssl: bool = True
    timeout: float = 30.0

    def _build_payload(
        self,
        method: str,
        *,
        kwargs: Optional[Dict[str, Any]] = None,
        args: Optional[List[Any]] = None,
        fields: Optional[List[Any]] = None,
        filter: Optional[Any] = None,
        flags: Optional[Dict[str, Any]] = None,
        no_meta: Optional[bool] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "jsonrpc": "2.2",
            "method": method,
            "callid": str(uuid.uuid4()),
        }

        if args is not None:
            payload["args"] = args
        if kwargs is not None:
            # EVA docs use kwargs for named arguments
            payload["kwargs"] = kwargs
        if fields is not None:
            payload["fields"] = fields
        if filter is not None:
            payload["filter"] = filter
        if flags is not None:
            payload["flags"] = flags
        if no_meta is not None:
            payload["no_meta"] = no_meta

        return payload

    def call(
        self,
        method: str,
        *,
        kwargs: Optional[Dict[str, Any]] = None,
        args: Optional[List[Any]] = None,
        fields: Optional[List[Any]] = None,
        filter: Optional[Any] = None,
        flags: Optional[Dict[str, Any]] = None,
        no_meta: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Generic EVA JSON-RPC call.

        Returns full JSON response (result, meta, etc.).
        Raises EvaApiError when response contains `error`.
        """
        payload = self._build_payload(
            method,
            kwargs=kwargs,
            args=args,
            fields=fields,
            filter=filter,
            flags=flags,
            no_meta=no_meta,
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        response = requests.post(
            self.base_url,
            json=payload,
            headers=headers,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        # HTTP errors (4xx, 5xx) raise requests exceptions
        response.raise_for_status()

        data: Dict[str, Any] = response.json()

        error = data.get("error")
        if error:
            raise EvaApiError(
                method=method, code=error.get("code"), message=error.get("message", "")
            )

        return data


    # ------------------------------------------------------------------
    # Hierarchy helpers (folders / documents tree)
    # ------------------------------------------------------------------

    def _list_all(
        self,
        method: str,
        fields: List[str],
        *,
        extra_filter: Optional[Any] = None,
        page_size: int = 200,
    ) -> List[Dict[str, Any]]:
        """Paginated fetch of all items matching *extra_filter*."""
        items: List[Dict[str, Any]] = []
        offset = 0
        while True:
            kwargs: Dict[str, Any] = {"slice": [offset, offset + page_size]}
            if extra_filter is not None:
                kwargs["filter"] = extra_filter
            data = self.call(method, kwargs=kwargs, fields=fields, no_meta=True)
            batch = data.get("result") or []
            accessible = [r for r in batch if r.get("_acl_obj") != "deny"]
            items.extend(accessible)
            if len(batch) < page_size:
                break
            offset += page_size
        return items

    def list_folders(
        self,
        project_id: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Return all CmfFolder items, optionally scoped to *project_id*."""
        f = fields or ["code", "name", "parent_id", "project_id", "id"]
        flt = ["project_id", "==", project_id] if project_id else None
        return self._list_all("CmfFolder.list", f, extra_filter=flt)

    def list_documents_for_tree(
        self,
        project_id: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Return all CmfDocument items (lightweight) for tree building."""
        f = fields or ["code", "name", "parent_id", "project_id", "id"]
        flt = ["project_id", "==", project_id] if project_id else None
        return self._list_all("CmfDocument.list", f, extra_filter=flt)

    def list_wiki_roots(
        self,
        project_id: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Return root-level wiki tree nodes (tree_parent_id is null)."""
        f = fields or ["code", "name", "id", "project_id"]
        flt: Any = ["tree_parent_id", "==", None]
        if project_id:
            flt = {"and": [flt, ["project_id", "==", project_id]]}
        return self._list_all("CmfDocument.list", f, extra_filter=flt)

    def list_wiki_children(
        self,
        parent_id: str,
        project_id: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Return direct wiki tree children of *parent_id* (tree_parent_id == parent_id)."""
        f = fields or ["code", "name", "id", "project_id"]
        flt: Any = ["tree_parent_id", "==", parent_id]
        if project_id:
            flt = {"and": [flt, ["project_id", "==", project_id]]}
        return self._list_all("CmfDocument.list", f, extra_filter=flt)

    def build_tree(
        self,
        project_id: Optional[str] = None,
        max_depth: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Build wiki navigation tree using tree_parent_id top-down traversal.

        Starts from root nodes (tree_parent_id == null), then recursively
        fetches children via tree_parent_id filter for each branch node.

        Each node: {type, id, code, name, children: [...]}
        At max_depth, children_count is returned instead of children list.
        """
        doc_fields = ["code", "name", "id", "project_id"]

        def _fetch_children(parent_id: Optional[str], depth: int) -> List[Dict[str, Any]]:
            if depth > max_depth:
                return []
            if parent_id is None:
                nodes = self.list_wiki_roots(project_id=project_id, fields=doc_fields)
            else:
                nodes = self.list_wiki_children(parent_id, project_id=project_id, fields=doc_fields)

            result = []
            for node in nodes:
                node_id = node.get("id", "")
                entry: Dict[str, Any] = {
                    "type": "document",
                    "id": node_id,
                    "code": node.get("code"),
                    "name": node.get("name"),
                }
                if depth < max_depth:
                    children = _fetch_children(node_id, depth + 1)
                    if children:
                        entry["children"] = children
                else:
                    # At max depth, probe for children existence with a small query
                    probe = self.list_wiki_children(node_id, project_id=project_id, fields=["id"])
                    if probe:
                        entry["children_count"] = len(probe)
                result.append(entry)
            return result

        return _fetch_children(None, 0)

    def get_wiki_parent(
        self,
        node_id: str,
        fields: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find the wiki tree parent of *node_id* using tree_nodes.id reverse lookup.

        Uses filter ["tree_nodes.id", "==", node_id] which returns the document
        that has node_id in its tree_nodes (i.e. its wiki tree children).
        Returns None if the node is a root (no wiki parent).
        """
        f = fields or ["code", "name", "id", "project_id"]
        data = self.call(
            "CmfDocument.list",
            kwargs={"slice": [0, 1], "filter": ["tree_nodes.id", "==", node_id]},
            fields=f,
            no_meta=True,
        )
        results = data.get("result") or []
        return results[0] if results else None

    def get_wiki_breadcrumb(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Build wiki navigation breadcrumb by walking tree_nodes.id chain upward.

        Returns list from root to the node's immediate parent:
        [{id, code, name, project_id}, ...]
        """
        crumbs: List[Dict[str, Any]] = []
        visited: set = set()
        current_id = node_id

        while current_id and current_id not in visited:
            visited.add(current_id)
            parent = self.get_wiki_parent(current_id)
            if not parent:
                break
            crumbs.append(parent)
            current_id = parent.get("id", "")

        crumbs.reverse()
        return crumbs

    def get_breadcrumb(self, node_id: str) -> List[Dict[str, str]]:
        """
        Walk parent_id chain upward to build breadcrumb list (root → leaf).
        Returns [{type, id, code, name}, ...].
        """
        crumbs: List[Dict[str, str]] = []
        visited: set = set()
        current_id = node_id

        while current_id and current_id not in visited:
            visited.add(current_id)
            class_name = current_id.split(":")[0] if ":" in current_id else ""
            if class_name == "CmfProject":
                try:
                    data = self.call(
                        "CmfProject.get",
                        kwargs={"filter": ["id", "==", current_id]},
                        fields=["code", "name", "id"],
                    )
                    r = data.get("result") or {}
                    crumbs.append({"type": "project", "id": current_id, "code": r.get("code", ""), "name": r.get("name", "")})
                except EvaApiError:
                    crumbs.append({"type": "project", "id": current_id, "code": "", "name": ""})
                break
            elif class_name == "CmfFolder":
                method = "CmfFolder.get"
            elif class_name == "CmfDocument":
                method = "CmfDocument.get"
            else:
                break
            try:
                data = self.call(
                    method,
                    kwargs={"filter": ["id", "==", current_id]},
                    fields=["code", "name", "parent_id", "id"],
                )
                r = data.get("result") or {}
                crumbs.append({
                    "type": "folder" if class_name == "CmfFolder" else "document",
                    "id": current_id,
                    "code": r.get("code", ""),
                    "name": r.get("name", ""),
                })
                current_id = r.get("parent_id", "")
            except EvaApiError:
                break

        crumbs.reverse()
        return crumbs


__all__ = ["EvaWikiClient", "EvaApiError"]
