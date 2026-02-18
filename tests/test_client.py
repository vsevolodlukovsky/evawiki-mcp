"""Tests for EvaWikiClient (no real HTTP)."""

from evawiki_mcp.evawiki_client import EvaApiError, EvaWikiClient


def test_build_payload_minimal():
    """_build_payload with only method produces jsonrpc 2.2 and callid."""
    client = EvaWikiClient(base_url="https://x/api/", token="t")
    payload = client._build_payload("Some.method")
    assert payload["jsonrpc"] == "2.2"
    assert payload["method"] == "Some.method"
    assert "callid" in payload
    assert len(payload) == 3


def test_build_payload_with_kwargs():
    """_build_payload includes kwargs when provided."""
    client = EvaWikiClient(base_url="https://x/api/", token="t")
    payload = client._build_payload("CmfDocument.get", kwargs={"filter": ["code", "==", "DOC-1"]})
    assert payload["kwargs"] == {"filter": ["code", "==", "DOC-1"]}


def test_build_payload_with_args():
    """_build_payload includes args when provided."""
    client = EvaWikiClient(base_url="https://x/api/", token="t")
    payload = client._build_payload("CmfDocument.update", args=[123], kwargs={"text_draft": "Hi"})
    assert payload["args"] == [123]
    assert payload["kwargs"] == {"text_draft": "Hi"}


def test_build_payload_with_fields_and_no_meta():
    """_build_payload includes fields and no_meta when provided."""
    client = EvaWikiClient(base_url="https://x/api/", token="t")
    payload = client._build_payload(
        "CmfDocument.list",
        kwargs={"slice": [0, 10]},
        fields=["code", "name"],
        no_meta=True,
    )
    assert payload["fields"] == ["code", "name"]
    assert payload["no_meta"] is True


def test_eva_api_error():
    """EvaApiError exposes method, code, message."""
    err = EvaApiError(method="CmfDocument.get", code=-32000, message="Not found")
    assert err.method == "CmfDocument.get"
    assert err.code == -32000
    assert err.message == "Not found"
    assert "CmfDocument.get" in str(err)
