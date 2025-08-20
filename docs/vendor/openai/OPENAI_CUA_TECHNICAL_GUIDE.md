# OpenAI CUA Technical Implementation Guide

## Architecture Overview

### System Components
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  CUA Adapter │────▶│ Responses API   │
│   (3 inputs)    │     │   (OpenAI)   │     │ computer-use    │
└─────────────────┘     └──────────────┘     └─────────────────┘
                              │                       │
                              ▼                       ▼
                     ┌──────────────────┐    ┌────────────────┐
                     │ Browser Control  │◀───│ computer_calls │
                     │ (pyautogui/pw)   │    │ click/type/etc │
                     └──────────────────┘    └────────────────┘
```

## 1. Client Initialization

### Basic Setup
```python
from openai import OpenAI
from typing import List, Dict, Any
import base64
from PIL import Image
import io
import os

class OpenAICUAAdapter:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        # Configure via env to allow easy upgrades
        self.model = os.getenv("CUA_MODEL", "computer-use-preview")
        self.session_context = []
        
    def initialize_session(self):
        """Start a new CUA session"""
        self.session_context = []
        return self

### Model Selection
- Computer Use model is configured via `CUA_MODEL` (default `computer-use-preview`).
- Decision/reasoning model is configured separately via `DECISION_MODEL` and is used for Advisor/Hybrid mode prompts.
- Keep model names out of code; read from env/config to simplify upgrades (e.g., switching to a newer Computer Use model when available).
```

## 2. Screenshot Handling

### Capture and Encode
```python
import pyautogui
import numpy as np

class ScreenshotManager:
    @staticmethod
    def capture() -> str:
        """Capture screen and return base64 encoded image"""
        # Capture screenshot
        screenshot = pyautogui.screenshot()
        
        # Resize for optimal token usage (1280x800 recommended)
        screenshot = screenshot.resize((1280, 800), Image.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        
        return base64.b64encode(image_data).decode('utf-8')
    
    @staticmethod
    def prepare_for_api(base64_image: str) -> Dict:
        """Format screenshot for API"""
        return {
            "type": "image",
            "image": {
                "base64": base64_image,
                "detail": "high"  # or "low" for faster/cheaper
            }
        }
```

## 3. API Request Structure

### Making CUA Requests
```python
def request_action(self, instruction: str, screenshot: str) -> Dict:
    """Request next action from CUA"""
    
    # Prepare messages
    messages = [
        {
            "role": "system",
            "content": "You are navigating YC cofounder matching site. Be precise with actions."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": instruction
                },
                self.screenshot_manager.prepare_for_api(screenshot)
            ]
        }
    ]
    
    # Add session context
    messages.extend(self.session_context)
    
    # Make API call
    response = self.client.responses.create(
        model=self.model,
        messages=messages,
        tools=["computer_use"],
        temperature=0.3,  # Lower for more deterministic actions
        max_tokens=1000
    )
    
    return response
```

## 4. Action Execution

### Computer Call Format
```python
class ActionExecutor:
    """Execute computer_calls from CUA response"""
    
    ACTIONS = {
        "click": lambda x, y, button="left": pyautogui.click(x, y, button=button),
        "double_click": lambda x, y: pyautogui.doubleClick(x, y),
        "type": lambda text: pyautogui.typewrite(text),
        "scroll": lambda x, y, dx, dy: pyautogui.scroll(dy, x=x, y=y),
        "wait": lambda ms: time.sleep(ms / 1000),
        "move": lambda x, y: pyautogui.moveTo(x, y),
        "keypress": lambda keys: pyautogui.hotkey(*keys.split('+'))
    }
    
    @classmethod
    def execute(cls, computer_calls: List[Dict]) -> List[Dict]:
        """Execute a list of computer calls"""
        results = []
        
        for call in computer_calls:
            action = call.get("action")
            params = call.get("parameters", {})
            
            try:
                if action in cls.ACTIONS:
                    cls.ACTIONS[action](**params)
                    results.append({"action": action, "status": "success"})
                else:
                    results.append({"action": action, "status": "unknown_action"})
                    
            except Exception as e:
                results.append({
                    "action": action, 
                    "status": "failed",
                    "error": str(e)
                })
                
        return results
```

## 5. Complete Flow Example

### YC Profile Navigation
```python
class YCNavigator:
    def __init__(self, cua_adapter: OpenAICUAAdapter):
        self.cua = cua_adapter
        self.screenshot_mgr = ScreenshotManager()
        self.executor = ActionExecutor()
    
    async def navigate_to_profile(self, profile_number: int):
        """Navigate to a specific profile"""
        
        # Take screenshot
        screenshot = self.screenshot_mgr.capture()
        
        # Request navigation action
        instruction = f"Click on profile number {profile_number} in the list"
        response = self.cua.request_action(instruction, screenshot)
        
        # Extract computer_calls from response
        computer_calls = self.extract_computer_calls(response)
        
        # Execute actions
        results = self.executor.execute(computer_calls)
        
        # Verify success
        time.sleep(2)  # Wait for page load
        new_screenshot = self.screenshot_mgr.capture()
        
        # Confirm we're on profile page
        verification = self.cua.request_action(
            "Are we on a profile detail page? Return YES or NO",
            new_screenshot
        )
        
        return verification
    
    def extract_computer_calls(self, response) -> List[Dict]:
        """Extract computer_calls from API response"""
        # Response structure:
        # response.computer_calls = [
        #     {"action": "click", "parameters": {"x": 150, "y": 200}},
        #     {"action": "wait", "parameters": {"ms": 2000}}
        # ]
        return response.get("computer_calls", [])
```

## 6. Session Management

### Maintaining Context
```python
class SessionManager:
    def __init__(self):
        self.history = []
        self.state = {
            "current_page": "unknown",
            "profiles_viewed": [],
            "messages_sent": []
        }
    
    def update_context(self, action: str, result: Dict):
        """Update session context after each action"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "result": result
        })
        
        # Update state based on action
        if "profile" in action:
            self.state["profiles_viewed"].append(result)
        elif "message" in action:
            self.state["messages_sent"].append(result)
    
    def get_context_for_api(self) -> List[Dict]:
        """Format context for API messages"""
        # Keep last 5 actions for context
        recent = self.history[-5:] if len(self.history) > 5 else self.history
        
        return [
            {
                "role": "assistant",
                "content": f"Previous action: {h['action']} - Result: {h['result']}"
            }
            for h in recent
        ]
```

## 7. Error Handling & Retry

### Robust Action Execution
```python
class RobustExecutor:
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    @staticmethod
    async def execute_with_retry(
        cua: OpenAICUAAdapter,
        instruction: str,
        screenshot: str
    ) -> Dict:
        """Execute action with retry logic"""
        
        for attempt in range(RobustExecutor.MAX_RETRIES):
            try:
                response = cua.request_action(instruction, screenshot)
                
                if response.get("status") == "success":
                    return response
                    
                # If failed, wait and retry
                await asyncio.sleep(RobustExecutor.RETRY_DELAY)
                
            except Exception as e:
                if attempt == RobustExecutor.MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(RobustExecutor.RETRY_DELAY)
        
        return {"status": "failed", "error": "Max retries exceeded"}
```

## 8. Integration with YC Bot

### OpenAICUAAdapter Implementation
```python
from typing import Optional
from app.application.ports import ComputerUsePort

class OpenAICUAAdapter(ComputerUsePort):
    """OpenAI CUA implementation of ComputerUsePort"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.navigator = YCNavigator(self)
        self.session = SessionManager()
        
    def open(self, url: str) -> None:
        """Open URL using CUA"""
        screenshot = ScreenshotManager.capture()
        response = self.request_action(f"Navigate to {url}", screenshot)
        self.execute_computer_calls(response)
        
    def find_click(self, locator: str) -> None:
        """Find and click element"""
        screenshot = ScreenshotManager.capture()
        response = self.request_action(
            f"Find and click on element: {locator}", 
            screenshot
        )
        self.execute_computer_calls(response)
        
    def read_text(self, target: str) -> str:
        """Extract text from screen"""
        screenshot = ScreenshotManager.capture()
        response = self.request_action(
            f"Extract all text from {target} section", 
            screenshot
        )
        # Parse text from response
        return response.get("extracted_text", "")
        
    def fill(self, selector: str, text: str) -> None:
        """Fill form field"""
        screenshot = ScreenshotManager.capture()
        response = self.request_action(
            f"Fill the field '{selector}' with: {text}", 
            screenshot
        )
        self.execute_computer_calls(response)
        
    def press_send(self) -> None:
        """Click send/submit button"""
        screenshot = ScreenshotManager.capture()
        response = self.request_action(
            "Click the Send or Submit button", 
            screenshot
        )
        self.execute_computer_calls(response)
        
    def verify_sent(self) -> bool:
        """Verify message was sent"""
        time.sleep(2)  # Wait for action
        screenshot = ScreenshotManager.capture()
        response = self.request_action(
            "Was the message successfully sent? Look for confirmation", 
            screenshot
        )
        return "yes" in response.get("output_text", "").lower()
```

## 9. Cost Optimization

### Token Management
```python
class TokenOptimizer:
    @staticmethod
    def compress_screenshot(image: Image, quality: int = 85) -> str:
        """Compress screenshot to reduce tokens"""
        # Resize to optimal dimensions
        max_width = 1024
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.LANCZOS)
        
        # Compress
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=quality, optimize=True)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    @staticmethod
    def truncate_context(messages: List[Dict], max_messages: int = 10) -> List[Dict]:
        """Keep only recent context to save tokens"""
        if len(messages) <= max_messages:
            return messages
        
        # Keep system message + recent messages
        return [messages[0]] + messages[-(max_messages-1):]
```

## 10. Safety & Monitoring

### Action Safety Wrapper
```python
class SafetyWrapper:
    DANGEROUS_ACTIONS = ["delete", "remove", "uninstall", "format"]
    
    def __init__(self, executor: ActionExecutor):
        self.executor = executor
        self.stop_flag = False
        
    def check_stop_flag(self) -> bool:
        """Check if stop was requested"""
        return os.path.exists(".runs/stop.flag")
        
    def validate_action(self, action: Dict) -> bool:
        """Validate action is safe"""
        action_text = str(action).lower()
        
        for danger in self.DANGEROUS_ACTIONS:
            if danger in action_text:
                return False
                
        return True
        
    def execute_safe(self, computer_calls: List[Dict]) -> List[Dict]:
        """Execute with safety checks"""
        if self.check_stop_flag():
            return [{"status": "stopped", "reason": "stop_flag"}]
            
        safe_calls = [c for c in computer_calls if self.validate_action(c)]
        
        if len(safe_calls) < len(computer_calls):
            # Log blocked actions
            blocked = len(computer_calls) - len(safe_calls)
            print(f"Blocked {blocked} potentially dangerous actions")
            
        return self.executor.execute(safe_calls)
```

## Environment Setup

### Requirements
```txt
openai>=1.12.0
pillow>=10.0.0
pyautogui>=0.9.54
python-dotenv>=1.0.0
pydantic>=2.0.0
```

### Environment Variables
```bash
# .env file
OPENAI_API_KEY=sk-...
ENABLE_CUA=1
CUA_MODEL=computer-use-preview
CUA_TEMPERATURE=0.3
CUA_MAX_TOKENS=1000
SCREENSHOT_QUALITY=85
MAX_CONTEXT_MESSAGES=10
```

## Model Upgrade Checklist
- Verify the new Computer Use model is available to your account and supports Computer Use (per official OpenAI docs).
- Update environment variables: `CUA_MODEL` (and optionally `DECISION_MODEL`).
- Run contract tests for `ComputerUsePort` and end-to-end smoke tests.
- Canary test on a small batch; compare success rate, latency, and cost.
- If regressions occur, revert env vars to previous models.

## Performance Metrics

### Expected Performance
- **Response time**: 2-5 seconds per action
- **Token usage**: ~500-1500 per action (with screenshot)
- **Cost per action**: ~$0.002-0.005
- **Success rate**: ~85% for simple UI actions
- **Session cost (20 profiles)**: ~$0.40-0.60

## Troubleshooting

### Common Issues

1. **Screenshot too large**
   - Solution: Use compression and resizing
   
2. **Actions not executing**
   - Check pyautogui permissions
   - Verify screen resolution matches
   
3. **High token usage**
   - Reduce screenshot quality
   - Truncate context more aggressively
   
4. **CUA confused about UI**
   - Add more specific instructions
   - Use smaller, focused screenshots

## Best Practices

1. **Always verify critical actions** (like sending messages)
2. **Implement rate limiting** between actions
3. **Log all computer_calls** for debugging
4. **Use structured prompts** for consistent behavior
5. **Handle failures gracefully** with retries
6. **Monitor costs** in real-time
7. **Test in sandbox** before production
