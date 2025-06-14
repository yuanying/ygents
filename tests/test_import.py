"""Basic import tests."""


def test_import_main_package():
    """Test that main package can be imported."""
    import ygents

    assert ygents.__version__ == "0.1.0"


def test_import_submodules():
    """Test that all submodules can be imported."""
    import ygents.agent  # noqa: F401
    import ygents.cli  # noqa: F401
    import ygents.config  # noqa: F401
    import ygents.mcp  # noqa: F401

    # Note: ygents.llm module is not implemented (using LiteLLM directly)
