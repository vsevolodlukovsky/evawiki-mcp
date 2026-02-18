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
            raise EvaApiError(method=method, code=error.get("code"), message=error.get("message", ""))

        return data


__all__ = ["EvaWikiClient", "EvaApiError"]
