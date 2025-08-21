#!/usr/bin/env python
"""Test CUA browser initialization and basic operations."""

import asyncio
import os

# Set up environment
os.environ["ENABLE_CUA"] = "1"
os.environ["ENABLE_PLAYWRIGHT"] = "1"
os.environ["PLAYWRIGHT_HEADLESS"] = "0"  # VISIBLE browser
os.environ["CUA_MODEL"] = os.getenv("CUA_MODEL", "gpt-4")  # Fallback if not set

print("🧪 Testing CUA Browser...")
print("=" * 50)


async def test_cua():
    """Test CUA browser operations."""

    # Test 1: Import and create browser
    print("\n1️⃣ Creating CUA browser...")
    try:
        from src.yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser

        browser = OpenAICUABrowser()
        print(f"✅ Created browser: {type(browser).__name__}")
        print(f"   - Model: {browser.model}")
        print(f"   - Fallback enabled: {browser.fallback_enabled}")
    except Exception as e:
        print(f"❌ Failed to create browser: {e}")
        return

    # Test 2: Open a URL
    print("\n2️⃣ Opening YC cofounder matching...")
    try:
        url = "https://www.startupschool.org/cofounder-matching"
        await browser.open(url)
        print(f"✅ Opened: {url}")
    except Exception as e:
        print(f"❌ Failed to open URL: {e}")
        import traceback

        traceback.print_exc()

    # Test 3: Take a screenshot
    print("\n3️⃣ Taking screenshot...")
    try:
        if browser.page:
            await browser.page.screenshot(path="test_cua_browser.png")
            print("✅ Screenshot saved to test_cua_browser.png")
        else:
            print("⚠️  No page available for screenshot")
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")

    # Test 4: Close browser
    print("\n4️⃣ Closing browser...")
    try:
        await browser.close()
        print("✅ Browser closed")
    except Exception as e:
        print(f"❌ Failed to close: {e}")

    print("\n" + "=" * 50)
    print("✨ CUA Browser test complete!")


if __name__ == "__main__":
    asyncio.run(test_cua())
