"""Test helpers for common mocking patterns."""

from unittest.mock import Mock


def make_context_manager() -> Mock:
    """Create a mock that supports context manager protocol."""
    cm = Mock()
    cm.__enter__ = Mock(return_value=cm)
    cm.__exit__ = Mock(return_value=None)
    return cm


def mock_streamlit_columns(spec: int | list[float]) -> list[Mock]:
    """Mock st.columns() to return correct number of context managers.

    Args:
        spec: Either an int (number of columns) or list of relative widths

    Returns:
        List of mock context managers
    """
    n = spec if isinstance(spec, int) else len(spec)
    return [make_context_manager() for _ in range(n)]


def mock_locator_count(count: int) -> Mock:
    """Create a mock locator with a count method returning an int.

    Args:
        count: The count to return

    Returns:
        Mock locator with count() -> int
    """
    locator = Mock()
    locator.count = lambda: count
    return locator


def mock_playwright_page(logged_in: bool = False) -> Mock:
    """Create a mock Playwright page with common methods.
    
    Args:
        logged_in: Whether is_logged_in() should return True
        
    Returns:
        Mock page with locator, goto, etc.
    """
    page = Mock()

    # Mock locator for login check
    locator = mock_locator_count(1 if logged_in else 0)
    page.locator.return_value = locator
    page.get_by_label = Mock(return_value=locator)
    page.get_by_text = Mock(return_value=locator)
    page.get_by_role = Mock(return_value=locator)

    # Mock navigation
    page.goto = Mock()

    return page
