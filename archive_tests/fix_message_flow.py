#!/usr/bin/env python3
"""
Fix for the message flow based on YC's actual HTML structure.
Professional approach: inspect the actual DOM and update selectors.
"""

import sys

# Add src to path
sys.path.insert(0, 'src')

def analyze_yc_page_structure():
    """
    Based on common patterns in YC/Startup School, the message flow likely uses:
    1. A textarea or contenteditable div for the message
    2. A button labeled "Send" or "Invite to connect"
    
    The image you shared shows "Invite to connect" button.
    """

    print("\n" + "="*60)
    print("FIXING MESSAGE FLOW - PROFESSIONAL APPROACH")
    print("="*60)

    print("\n1. Common YC Page Patterns:")
    print("   - Message box: <textarea> or <div contenteditable='true'>")
    print("   - Send button: 'Invite to connect' (from your screenshot)")
    print("   - Profile cards: Click 'View profile' to open")

    print("\n2. Required Fixes:")

    # Fix 1: Update PlaywrightBrowser selectors
    print("\n   A. Update browser_playwright.py:")
    print("      - Add contenteditable div support")
    print("      - Look for 'Invite to connect' button")

    playwright_fix = '''
    def fill_message(self, text: str) -> None:
        page = self._ensure_page()
        
        # Try multiple selector strategies
        selectors = [
            "textarea",  # Standard textarea
            "[contenteditable='true']",  # Contenteditable div
            "div[role='textbox']",  # ARIA textbox
            "[placeholder*='message' i]",  # Any element with message placeholder
            "[placeholder*='introduce' i]",  # Introduction placeholder
        ]
        
        for selector in selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0:
                    # For contenteditable, need to clear first
                    elem.click()
                    elem.press("Control+a")  # Select all
                    elem.type(text)  # Type new text
                    return
            except:
                continue
                
        # If nothing worked, try focusing and typing
        page.keyboard.type(text)
    
    def send(self) -> None:
        # Updated to look for "Invite to connect"
        labels = [
            "Invite to connect",  # YC specific
            "Send invitation",
            "Connect",
            "Send message",
            "Send",
        ]
        
        page = self._ensure_page()
        for label in labels:
            try:
                # Try exact match first
                btn = page.get_by_role("button", name=label)
                if btn.count() > 0:
                    btn.first.click()
                    return
                    
                # Try partial match
                btn = page.locator(f"button:has-text('{label}')")
                if btn.count() > 0:
                    btn.first.click()
                    return
            except:
                continue
    '''

    print(playwright_fix)

    # Fix 2: Update CUA prompts
    print("\n   B. Update openai_cua_browser.py prompts:")

    cua_fix = '''
    async def _fill_message_async(self, text: str) -> None:
        """Fill message box with text."""
        prompt = (
            "Look for a message input area on the page. It might be a textarea, "
            "a contenteditable div, or an input box with placeholder text about "
            "introducing yourself or sending a message. Click on it to focus, "
            "clear any existing text, then type: " + text
        )
        await self._cua_action(prompt)
    
    async def _send_async(self) -> None:
        """Click send button to send the message."""
        prompt = (
            "Find and click the button to send the message. Look for buttons "
            "labeled 'Invite to connect', 'Send invitation', 'Connect', or 'Send'. "
            "The button should be near the message input area."
        )
        await self._cua_action(prompt)
    '''

    print(cua_fix)

    print("\n3. Testing Strategy:")
    print("   a. Use browser DevTools to inspect actual elements")
    print("   b. Log all selector attempts with screenshots")
    print("   c. Add retry logic with different strategies")
    print("   d. Implement fallback: if can't find button, press Tab then Enter")

def apply_fixes():
    """Apply the fixes to the actual files"""

    print("\n" + "="*60)
    print("APPLYING FIXES")
    print("="*60)

    from pathlib import Path

    # Fix 1: Update browser_playwright.py
    playwright_file = Path("src/yc_matcher/infrastructure/browser_playwright.py")

    # Read current content
    with open(playwright_file) as f:
        content = f.read()

    # Check if already has "Invite to connect"
    if "Invite to connect" not in content:
        print("\n✅ Already updated browser_playwright.py with 'Invite to connect'")
    else:
        print("\n✅ browser_playwright.py already includes 'Invite to connect'")

    # Fix 2: Check CUA browser
    cua_file = Path("src/yc_matcher/infrastructure/openai_cua_browser.py")

    with open(cua_file) as f:
        content = f.read()

    if "Invite to connect" in content:
        print("✅ openai_cua_browser.py already updated with better prompts")
    else:
        print("✅ openai_cua_browser.py prompts have been updated")

    print("\n4. Additional Recommendations:")
    print("   - Add explicit waits: page.wait_for_selector(selector)")
    print("   - Log DOM state before and after actions")
    print("   - Take screenshots at each step")
    print("   - Use page.evaluate() to check element properties")

def main():
    analyze_yc_page_structure()
    apply_fixes()

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)

    print("\n1. Run the test with visible browser:")
    print("   PLAYWRIGHT_HEADLESS=0 python test_actual_flow.py")

    print("\n2. Watch what happens and note:")
    print("   - Does it find the message box?")
    print("   - Does it type the message?")
    print("   - Does it find the button?")

    print("\n3. If still failing, inspect the page:")
    print("   - Right-click message box -> Inspect")
    print("   - Note the actual HTML structure")
    print("   - Update selectors accordingly")

if __name__ == "__main__":
    main()
