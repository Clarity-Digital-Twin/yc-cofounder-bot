"""Pre-flight check system to validate everything works before running the app.

Professional approach: Test everything before the user starts.
"""

from __future__ import annotations

import os
import json
from typing import Any
from pathlib import Path

from .. import config
from ..domain.entities import Profile, Criteria


class PreflightChecker:
    """Systematic pre-flight checks before running the app."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def check_environment(self) -> bool:
        """Check environment variables."""
        print("\n🔍 Checking environment variables...")
        
        # Critical variables
        if not config.get_openai_api_key():
            self.errors.append("❌ OPENAI_API_KEY not set")
            return False
        else:
            self.info.append(f"✅ API Key: ...{config.get_openai_api_key()[-8:]}")
        
        # YC credentials
        email, password = config.get_yc_credentials()
        if email and password:
            self.info.append("✅ YC credentials configured")
        else:
            self.warnings.append("⚠️ YC credentials not set (manual login required)")
        
        # Model configuration
        model = config.get_decision_model()
        self.info.append(f"✅ Decision model: {model}")
        
        # CUA configuration
        if config.is_cua_enabled():
            cua_model = config.get_cua_model()
            if cua_model:
                self.info.append(f"✅ CUA model: {cua_model}")
            else:
                self.warnings.append("⚠️ CUA enabled but no model configured")
        
        return True

    def check_openai_api(self) -> bool:
        """Test OpenAI API connectivity and model access."""
        print("\n🔍 Testing OpenAI API...")
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=config.get_openai_api_key())
            
            # List available models
            models = client.models.list()
            available = [m.id for m in models.data]
            
            # Check for GPT-5
            if "gpt-5" in available:
                self.info.append("✅ GPT-5 available")
            else:
                self.warnings.append("⚠️ GPT-5 not available (will use fallback)")
            
            # Check for GPT-4
            gpt4_models = [m for m in available if m.startswith("gpt-4")]
            if gpt4_models:
                self.info.append(f"✅ GPT-4 models: {', '.join(gpt4_models[:3])}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"❌ OpenAI API error: {e}")
            return False

    def test_gpt5_response(self) -> bool:
        """Test GPT-5 Responses API if available."""
        print("\n🔍 Testing GPT-5 decision flow...")
        
        model = config.get_decision_model()
        if not model.startswith("gpt-5"):
            self.info.append(f"✅ Using {model} (GPT-5 not configured)")
            return True
        
        try:
            from openai import OpenAI
            from ..infrastructure.openai_decision import OpenAIDecisionAdapter
            
            client = OpenAI(api_key=config.get_openai_api_key())
            adapter = OpenAIDecisionAdapter(client=client, model=model)
            
            # Test with minimal profile
            test_profile = Profile(raw_text="Test profile with Python experience")
            test_criteria = Criteria(text="Looking for Python developer")
            
            result = adapter.evaluate(test_profile, test_criteria)
            
            if result.get("decision") in ["YES", "NO"]:
                self.info.append(f"✅ GPT-5 decision working: {result['decision']}")
                return True
            elif result.get("decision") == "ERROR":
                self.errors.append(f"❌ GPT-5 evaluation error: {result.get('error')}")
                return False
            else:
                self.warnings.append(f"⚠️ Unexpected decision: {result.get('decision')}")
                return False
                
        except Exception as e:
            self.errors.append(f"❌ GPT-5 test failed: {e}")
            return False

    def check_directories(self) -> bool:
        """Check required directories exist."""
        print("\n🔍 Checking directories...")
        
        runs_dir = Path(".runs")
        if not runs_dir.exists():
            runs_dir.mkdir(exist_ok=True)
            self.info.append("✅ Created .runs directory")
        else:
            self.info.append("✅ .runs directory exists")
        
        # Check for stop flag
        stop_flag = runs_dir / "stop.flag"
        if stop_flag.exists():
            self.warnings.append("⚠️ STOP flag is set - browsing will halt immediately")
        
        return True

    def check_browser_setup(self) -> bool:
        """Check Playwright browser setup."""
        print("\n🔍 Checking browser setup...")
        
        if not config.is_playwright_enabled():
            self.info.append("✅ Playwright disabled (CUA-only mode)")
            return True
        
        browsers_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH", ".ms-playwright")
        browsers_dir = Path(browsers_path)
        
        if browsers_dir.exists():
            self.info.append(f"✅ Browsers installed at {browsers_path}")
        else:
            self.errors.append(f"❌ Browsers not installed. Run: make browsers")
            return False
        
        # Check headless mode
        if config.is_headless():
            self.info.append("✅ Running in headless mode")
        else:
            self.info.append("✅ Running in headful mode (browser visible)")
        
        return True

    def run_all_checks(self) -> bool:
        """Run all pre-flight checks."""
        print("\n" + "="*60)
        print("🚀 PRE-FLIGHT CHECKS")
        print("="*60)
        
        checks = [
            ("Environment", self.check_environment),
            ("OpenAI API", self.check_openai_api),
            ("GPT-5 Response", self.test_gpt5_response),
            ("Directories", self.check_directories),
            ("Browser Setup", self.check_browser_setup),
        ]
        
        all_passed = True
        for name, check_func in checks:
            try:
                passed = check_func()
                if not passed:
                    all_passed = False
            except Exception as e:
                self.errors.append(f"❌ {name} check crashed: {e}")
                all_passed = False
        
        # Print summary
        print("\n" + "="*60)
        print("📊 PRE-FLIGHT SUMMARY")
        print("="*60)
        
        if self.info:
            print("\n✅ PASSED:")
            for msg in self.info:
                print(f"  {msg}")
        
        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for msg in self.warnings:
                print(f"  {msg}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for msg in self.errors:
                print(f"  {msg}")
        
        if all_passed and not self.errors:
            print("\n✅ ALL CHECKS PASSED - READY TO RUN!")
        else:
            print("\n❌ SOME CHECKS FAILED - FIX ERRORS BEFORE RUNNING")
        
        return all_passed and not self.errors


def run_preflight_checks() -> bool:
    """Run pre-flight checks and return success status."""
    checker = PreflightChecker()
    return checker.run_all_checks()


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
    success = run_preflight_checks()
    sys.exit(0 if success else 1)