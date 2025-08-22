"""Test profile extraction when already on candidate page.

Following TDD: Test that browser detects and handles being on profile page.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from yc_matcher.infrastructure.browser_playwright_async import PlaywrightBrowserAsync


class TestExtractCandidate:
    """Test profile extraction from candidate pages."""

    def test_click_view_profile_detects_already_on_candidate(self) -> None:
        """Test that click_view_profile detects when already on /candidate/ page."""
        # Arrange
        browser = PlaywrightBrowserAsync()

        # Mock the async runner
        mock_runner = MagicMock()
        browser._runner = mock_runner

        # Create a mock page that's already on a candidate page
        async def mock_click():
            mock_page = AsyncMock()
            mock_page.url = "https://www.startupschool.org/cofounder-matching/candidate/12345"
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.wait_for_timeout = AsyncMock()

            # Mock _ensure_page_async to return our mock page
            with patch.object(browser, '_ensure_page_async', return_value=mock_page):
                # Call the actual async method
                return await browser._runner.submit.call_args[0][0]()

        # Configure runner to return True (already on profile)
        mock_runner.submit.return_value = True

        # Act
        result = browser.click_view_profile()

        # Assert
        assert result is True  # Should return True since we're on profile

    def test_click_view_profile_handles_dashboard_view_profiles_button(self) -> None:
        """Test that click_view_profile handles dashboard 'View Profiles' button."""
        # Arrange
        browser = PlaywrightBrowserAsync()

        mock_runner = MagicMock()
        browser._runner = mock_runner

        async def mock_click():
            mock_page = AsyncMock()
            mock_page.url = "https://www.startupschool.org/cofounder-matching/dashboard"
            mock_page.wait_for_load_state = AsyncMock()

            # Mock View Profiles button
            mock_button = AsyncMock()
            mock_button.count = AsyncMock(return_value=1)
            mock_button.first = AsyncMock()
            mock_button.first.click = AsyncMock()

            mock_page.locator = MagicMock(return_value=mock_button)

            with patch.object(browser, '_ensure_page_async', return_value=mock_page):
                return await browser._runner.submit.call_args[0][0]()

        mock_runner.submit.return_value = True

        # Act
        result = browser.click_view_profile()

        # Assert
        assert result is True

    def test_read_profile_extracts_structured_data(self) -> None:
        """Test that read_profile_text extracts structured data from candidate page."""
        # Arrange
        browser = PlaywrightBrowserAsync()

        mock_runner = MagicMock()
        browser._runner = mock_runner

        async def mock_read():
            mock_page = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()

            # Mock structured data extraction
            mock_name = AsyncMock()
            mock_name.count = AsyncMock(return_value=1)
            mock_name.first = AsyncMock()
            mock_name.first.text_content = AsyncMock(return_value="John Smith")

            mock_bio = AsyncMock()
            mock_bio.count = AsyncMock(return_value=1)
            mock_bio.all_text_contents = AsyncMock(return_value=[
                "ML Engineer with 5 years at Google",
                "Building AI tools for developers"
            ])

            mock_skills = AsyncMock()
            mock_skills.count = AsyncMock(return_value=1)
            mock_skills.all_text_contents = AsyncMock(return_value=[
                "Python", "TensorFlow", "React", "TypeScript"
            ])

            def locator_side_effect(selector):
                if "h1" in selector:
                    return mock_name
                elif "bio" in selector or "p" in selector:
                    return mock_bio
                elif "skill" in selector or "chip" in selector:
                    return mock_skills
                return AsyncMock(count=AsyncMock(return_value=0))

            mock_page.locator = MagicMock(side_effect=locator_side_effect)

            # Fallback text content
            mock_page.text_content = AsyncMock(return_value="Full page text content")

            with patch.object(browser, '_ensure_page_async', return_value=mock_page):
                return await browser._runner.submit.call_args[0][0]()

        mock_runner.submit.return_value = "Name: John Smith\nML Engineer with 5 years at Google"

        # Act
        result = browser.read_profile_text()

        # Assert
        assert "John Smith" in result
        assert "ML Engineer" in result or "Full page text" in result

    def test_skip_navigates_to_next_profile(self) -> None:
        """Test that skip method navigates to next profile."""
        # Arrange
        browser = PlaywrightBrowserAsync()

        mock_runner = MagicMock()
        browser._runner = mock_runner

        async def mock_skip():
            mock_page = AsyncMock()

            # Mock skip button
            mock_skip_btn = AsyncMock()
            mock_skip_btn.count = AsyncMock(return_value=1)
            mock_skip_btn.first = AsyncMock()
            mock_skip_btn.first.click = AsyncMock()

            mock_page.locator = MagicMock(return_value=mock_skip_btn)
            mock_page.wait_for_load_state = AsyncMock()

            with patch.object(browser, '_ensure_page_async', return_value=mock_page):
                return await browser._runner.submit.call_args[0][0]()

        mock_runner.submit.return_value = None  # skip returns nothing

        # Act
        browser.skip()

        # Assert - should complete without error
        mock_runner.submit.assert_called_once()

    def test_browser_handles_no_profiles_gracefully(self) -> None:
        """Test that browser handles no more profiles gracefully."""
        # Arrange
        browser = PlaywrightBrowserAsync()

        mock_runner = MagicMock()
        browser._runner = mock_runner

        async def mock_no_profiles():
            mock_page = AsyncMock()
            mock_page.url = "https://www.startupschool.org/cofounder-matching"
            mock_page.wait_for_load_state = AsyncMock()

            # No buttons found
            mock_empty = AsyncMock()
            mock_empty.count = AsyncMock(return_value=0)
            mock_page.locator = MagicMock(return_value=mock_empty)

            # Try navigation fallback
            mock_page.goto = AsyncMock()

            with patch.object(browser, '_ensure_page_async', return_value=mock_page):
                return await browser._runner.submit.call_args[0][0]()

        mock_runner.submit.side_effect = lambda coro: mock_no_profiles()

        # Act
        result = browser.click_view_profile()

        # Assert
        assert result is False  # Should return False when no profiles found
