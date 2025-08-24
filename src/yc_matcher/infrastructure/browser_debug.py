"""
Browser debugging utilities for systematic troubleshooting.
Professional teams would add this level of instrumentation.
"""

import json
import time
from pathlib import Path
from typing import Any

from .time_utils import utc_isoformat, utc_now


class BrowserDebugger:
    """Comprehensive browser action debugger"""

    def __init__(self, log_dir: str = ".runs/debug"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.session_id = utc_now().strftime("%Y%m%d_%H%M%S")
        self.action_log = []

    def log_action(self, action: str, details: dict) -> None:
        """Log every browser action with full context"""
        entry = {
            "timestamp": utc_isoformat(),
            "action": action,
            "details": details,
            "stack_trace": self._get_stack_trace()
        }
        self.action_log.append(entry)

        # Write immediately to file
        log_file = self.log_dir / f"browser_debug_{self.session_id}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def screenshot(self, page: Any, label: str) -> None:
        """Take screenshot at critical points"""
        try:
            screenshot_path = self.log_dir / f"{self.session_id}_{label}.png"
            if hasattr(page, 'screenshot'):
                page.screenshot(path=str(screenshot_path))
                self.log_action("screenshot", {"label": label, "path": str(screenshot_path)})
        except Exception as e:
            self.log_action("screenshot_failed", {"label": label, "error": str(e)})

    def check_element(self, page: Any, selector: str) -> dict:
        """Check if element exists and its properties"""
        try:
            if hasattr(page, 'locator'):
                elem = page.locator(selector)
                count = elem.count()

                if count > 0:
                    # Get element properties
                    props = page.evaluate(f"""
                        () => {{
                            const elem = document.querySelector('{selector}');
                            if (!elem) return null;
                            return {{
                                tagName: elem.tagName,
                                id: elem.id,
                                className: elem.className,
                                value: elem.value || '',
                                textContent: elem.textContent || '',
                                isVisible: elem.offsetParent !== null,
                                isEnabled: !elem.disabled,
                                rect: elem.getBoundingClientRect()
                            }};
                        }}
                    """)

                    result = {
                        "selector": selector,
                        "found": True,
                        "count": count,
                        "properties": props
                    }
                else:
                    result = {
                        "selector": selector,
                        "found": False,
                        "count": 0
                    }

                self.log_action("check_element", result)
                return result
        except Exception as e:
            error_result = {
                "selector": selector,
                "error": str(e)
            }
            self.log_action("check_element_error", error_result)
            return error_result

    def _get_stack_trace(self) -> list:
        """Get simplified stack trace for debugging"""
        import traceback
        stack = traceback.extract_stack()[:-2]  # Exclude this function
        return [
            {
                "file": frame.filename.split("/")[-1],
                "line": frame.lineno,
                "function": frame.name
            }
            for frame in stack[-5:]  # Last 5 frames
        ]

    def dump_page_info(self, page: Any) -> dict:
        """Dump comprehensive page information"""
        try:
            info = page.evaluate("""
                () => {
                    // Find all potential message inputs
                    const textareas = Array.from(document.querySelectorAll('textarea'));
                    const inputs = Array.from(document.querySelectorAll('input[type="text"]'));
                    const editables = Array.from(document.querySelectorAll('[contenteditable="true"]'));

                    // Find all buttons
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const submitButtons = Array.from(document.querySelectorAll('[type="submit"]'));

                    return {
                        url: window.location.href,
                        title: document.title,
                        textareas: textareas.map(e => ({
                            id: e.id,
                            className: e.className,
                            placeholder: e.placeholder,
                            value: e.value
                        })),
                        inputs: inputs.map(e => ({
                            id: e.id,
                            className: e.className,
                            placeholder: e.placeholder,
                            value: e.value
                        })),
                        editables: editables.map(e => ({
                            id: e.id,
                            className: e.className,
                            textContent: e.textContent
                        })),
                        buttons: buttons.map(e => ({
                            id: e.id,
                            className: e.className,
                            textContent: e.textContent,
                            disabled: e.disabled
                        }))
                    };
                }
            """)

            self.log_action("page_info", info)
            return info
        except Exception as e:
            self.log_action("page_info_error", {"error": str(e)})
            return {}


def wrap_browser_for_debugging(browser_instance, debugger: BrowserDebugger):
    """Wrap browser instance with debugging"""

    original_fill = browser_instance.fill_message
    original_send = browser_instance.send
    original_focus = browser_instance.focus_message_box

    def debug_fill_message(text: str) -> None:
        debugger.log_action("fill_message_start", {"text": text})

        # Get page state before
        if hasattr(browser_instance, '_page'):
            debugger.dump_page_info(browser_instance._page)
            debugger.screenshot(browser_instance._page, "before_fill")

        try:
            result = original_fill(text)
            debugger.log_action("fill_message_success", {"text": text})

            # Get page state after
            if hasattr(browser_instance, '_page'):
                time.sleep(1)  # Wait for DOM update
                debugger.dump_page_info(browser_instance._page)
                debugger.screenshot(browser_instance._page, "after_fill")

            return result
        except Exception as e:
            debugger.log_action("fill_message_error", {"text": text, "error": str(e)})
            raise

    def debug_send() -> None:
        debugger.log_action("send_start", {})

        if hasattr(browser_instance, '_page'):
            debugger.screenshot(browser_instance._page, "before_send")

        try:
            result = original_send()
            debugger.log_action("send_success", {})

            if hasattr(browser_instance, '_page'):
                time.sleep(1)
                debugger.screenshot(browser_instance._page, "after_send")

            return result
        except Exception as e:
            debugger.log_action("send_error", {"error": str(e)})
            raise

    def debug_focus() -> None:
        debugger.log_action("focus_start", {})
        try:
            result = original_focus()
            debugger.log_action("focus_success", {})
            return result
        except Exception as e:
            debugger.log_action("focus_error", {"error": str(e)})
            raise

    # Replace methods with debug versions
    browser_instance.fill_message = debug_fill_message
    browser_instance.send = debug_send
    browser_instance.focus_message_box = debug_focus

    return browser_instance
