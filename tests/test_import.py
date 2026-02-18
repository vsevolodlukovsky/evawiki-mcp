"""Test package import."""


def test_import_evawiki_mcp():
    """Package evawiki_mcp can be imported."""
    import evawiki_mcp

    assert evawiki_mcp.__doc__


def test_import_client_and_server():
    """EvaWikiClient and server components are importable."""
    from evawiki_mcp import evawiki_client
    from evawiki_mcp.evawiki_client import EvaApiError, EvaWikiClient

    assert EvaWikiClient is not None
    assert EvaApiError is not None
    assert evawiki_client.EvaWikiClient is EvaWikiClient
