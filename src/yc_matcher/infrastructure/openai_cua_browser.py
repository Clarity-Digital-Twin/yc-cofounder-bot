"""OpenAI Computer Use adapter for browser automation via Agents SDK."""

from __future__ import annotations

import os
import time
from typing import Dict, List, Optional

try:
    from agents import Agent, ComputerTool, Session
except ImportError:
    # Fallback for when SDK not installed
    Agent = None
    ComputerTool = None
    Session = None


class OpenAICUABrowser:
    """Browser automation using OpenAI's Computer Use tool via Agents SDK.
    
    This is the PRIMARY adapter, implementing ComputerUsePort via OpenAI's
    Computer Use tool. Falls back to Playwright when CUA unavailable.
    """
    
    def __init__(self) -> None:
        """Initialize OpenAI CUA browser adapter."""
        if Agent is None:
            raise RuntimeError(
                "Agents SDK not installed. Run: pip install openai-agents"
            )
        
        # Get model from env (check Models endpoint for your account)
        self.model = os.getenv("CUA_MODEL")
        if not self.model:
            raise ValueError(
                "CUA_MODEL environment variable not set. "
                "Check your Models endpoint at platform.openai.com/account/models"
            )
        
        # Initialize agent with Computer Use tool
        self.agent = Agent(
            model=self.model,
            tools=[ComputerTool()],
            temperature=float(os.getenv("CUA_TEMPERATURE", "0.3"))
        )
        
        # Session for maintaining context
        self.session = Session()
        self._profile_text_cache = ""
    
    def open(self, url: str) -> None:
        """Navigate to URL using Computer Use."""
        result = self.agent.run(
            messages=[
                {
                    "role": "system",
                    "content": "You are navigating YC cofounder matching site. Be precise with actions."
                },
                {
                    "role": "user",
                    "content": f"Navigate to {url} and wait for the page to fully load"
                }
            ],
            tools=[ComputerTool()],
            session=self.session
        )
    
    def click_view_profile(self) -> bool:
        """Click on profile view button using Computer Use."""
        result = self.agent.run(
            messages=[
                {
                    "role": "user",
                    "content": "Find and click on 'View profile' button or link"
                }
            ],
            tools=[ComputerTool()],
            session=self.session
        )
        # Check if action was successful
        return "clicked" in str(result).lower()
    
    def read_profile_text(self) -> str:
        """Extract profile text using Computer Use."""
        result = self.agent.run(
            messages=[
                {
                    "role": "user",
                    "content": "Extract all visible profile text including name, skills, location, bio, and any other relevant information"
                }
            ],
            tools=[ComputerTool()],
            session=self.session
        )
        
        # Parse extracted text from result
        if hasattr(result, 'text'):
            self._profile_text_cache = result.text
        elif isinstance(result, dict) and 'text' in result:
            self._profile_text_cache = result['text']
        else:
            self._profile_text_cache = str(result)
        
        return self._profile_text_cache
    
    def focus_message_box(self) -> None:
        """Focus on message input box using Computer Use."""
        self.agent.run(
            messages=[
                {
                    "role": "user",
                    "content": "Click on the message input box to focus it"
                }
            ],
            tools=[ComputerTool()],
            session=self.session
        )
    
    def fill_message(self, text: str) -> None:
        """Fill message box with text using Computer Use."""
        self.agent.run(
            messages=[
                {
                    "role": "user",
                    "content": f"Type the following message in the focused text box: {text}"
                }
            ],
            tools=[ComputerTool()],
            session=self.session
        )
    
    def send(self) -> None:
        """Click send button using Computer Use."""
        self.agent.run(
            messages=[
                {
                    "role": "user",
                    "content": "Find and click the Send or Invite button"
                }
            ],
            tools=[ComputerTool()],
            session=self.session
        )
    
    def skip(self) -> None:
        """Click skip button using Computer Use."""
        self.agent.run(
            messages=[
                {
                    "role": "user",
                    "content": "Find and click the Skip button"
                }
            ],
            tools=[ComputerTool()],
            session=self.session
        )
    
    def verify_sent(self) -> bool:
        """Verify message was sent using Computer Use."""
        result = self.agent.run(
            messages=[
                {
                    "role": "user",
                    "content": "Check if the message was sent successfully. Look for confirmation text or empty message box."
                }
            ],
            tools=[ComputerTool()],
            session=self.session
        )
        
        # Check for success indicators
        result_str = str(result).lower()
        return "sent" in result_str or "success" in result_str or "empty" in result_str
    
    def close(self) -> None:
        """Clean up session."""
        # Session cleanup if needed
        self.session = Session()
        self._profile_text_cache = ""
    
    def __enter__(self) -> OpenAICUABrowser:
        """Context manager entry."""
        return self
    
    def __exit__(self, *_: object) -> None:
        """Context manager exit."""
        self.close()


def create_cua_browser() -> OpenAICUABrowser:
    """Factory function to create OpenAI CUA browser instance."""
    return OpenAICUABrowser()