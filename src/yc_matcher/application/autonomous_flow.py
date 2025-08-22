"""Autonomous flow orchestrator for CUA-driven browsing.

Following Clean Code principles:
- Single Responsibility: Orchestrates the flow, delegates to use cases
- Dependency Inversion: Depends on ports, not implementations
- Open/Closed: Easy to extend without modifying
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any

from ..application.ports import (
    BrowserPort,
    LoggerPort,
    QuotaPort,
    SeenRepo,
    StopController,
)
from ..application.use_cases import EvaluateProfile, SendMessage
from ..domain.entities import Criteria, Profile


def hash_profile_text(text: str) -> str:
    """Generate hash for profile text for deduplication."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


@dataclass
class AutonomousFlow:
    """CUA-driven autonomous browsing and matching orchestrator.

    This class follows the Facade pattern, providing a simple interface
    to complex subsystem interactions.

    Attributes:
        browser: Browser automation (CUA or Playwright)
        evaluate: Profile evaluation use case
        send: Message sending use case
        seen: Repository for tracking seen profiles
        logger: Event logging
        stop: Stop flag controller
        quota: Quota management
    """

    browser: BrowserPort
    evaluate: EvaluateProfile
    send: SendMessage
    seen: SeenRepo
    logger: LoggerPort
    stop: StopController
    quota: QuotaPort

    def run(
        self,
        your_profile: str,
        criteria: str,
        template: str,
        mode: str = "hybrid",
        limit: int = 20,
        shadow_mode: bool = False,
        threshold: float = 0.7,
        alpha: float = 0.5,
    ) -> dict[str, Any]:
        """Execute autonomous browsing and matching flow.

        This implements the Template Method pattern - defines the skeleton
        of the algorithm, with specific steps delegated to other methods.

        Args:
            your_profile: User's profile description
            criteria: Match criteria text
            template: Message template
            mode: Decision mode (advisor|rubric|hybrid)
            limit: Maximum profiles to process
            shadow_mode: If True, evaluate only without sending
            threshold: Auto-send threshold for rubric/hybrid modes
            alpha: Weight for hybrid mode (0=all rubric, 1=all AI)

        Returns:
            Dictionary with results summary
        """
        self.logger.emit(
            {
                "event": "autonomous_start",
                "mode": mode,
                "limit": limit,
                "shadow": shadow_mode,
                "criteria_len": len(criteria),
                "template_len": len(template),
            }
        )

        # CRITICAL: Login preflight gate
        has_credentials = bool(os.getenv("YC_EMAIL") and os.getenv("YC_PASSWORD"))

        # Check if already logged in or can auto-login
        if hasattr(self.browser, "is_logged_in"):
            if not self.browser.is_logged_in():
                if has_credentials and hasattr(self.browser, "ensure_logged_in"):
                    self.logger.emit({"event": "auto_login_attempt"})
                    try:
                        self.browser.ensure_logged_in()
                        self.logger.emit({"event": "auto_login_success"})
                    except Exception as e:
                        self.logger.emit({"event": "auto_login_failed", "error": str(e)})
                        return {"error": "Auto-login failed", "evaluated": 0, "sent": 0}
                else:
                    self.logger.emit(
                        {"event": "login_required", "has_credentials": has_credentials}
                    )
                    return {
                        "error": "Manual login required - no credentials in .env",
                        "evaluated": 0,
                        "sent": 0,
                    }

        # Navigate to YC matching page
        yc_url = os.getenv("YC_MATCH_URL", "https://www.startupschool.org/cofounder-matching")
        self.browser.open(yc_url)

        # Verify login after navigation
        if hasattr(self.browser, "is_logged_in") and not self.browser.is_logged_in():
            self.logger.emit({"event": "login_lost_after_navigation"})
            return {"error": "Login required after navigation", "evaluated": 0, "sent": 0}

        results = []
        sent_count = 0
        skipped_count = 0

        # Process profiles up to limit
        for i in range(limit):
            # Check stop flag (Safety First principle)
            if self.stop.is_stopped():
                self.logger.emit({"event": "stopped", "at_profile": i, "reason": "stop_flag"})
                break

            # Skip quota check here - will be checked in SendMessage use case

            try:
                # Click view profile
                if not self.browser.click_view_profile():
                    self.logger.emit({"event": "no_more_profiles", "at_profile": i})
                    break

                # Extract profile text
                import time
                extract_start = time.time()
                profile_text = self.browser.read_profile_text()
                extract_ms = int((time.time() - extract_start) * 1000)
                
                # Determine engine type
                engine = "unknown"
                if hasattr(self.browser, "__class__"):
                    class_name = self.browser.__class__.__name__
                    if "CUA" in class_name:
                        engine = "cua"
                    elif "Playwright" in class_name:
                        engine = "playwright"
                
                if not profile_text:
                    self.logger.emit({
                        "event": "empty_profile", 
                        "at_profile": i,
                        "engine": engine,
                        "skip_reason": "No profile text extracted",
                        "extract_ms": extract_ms
                    })
                    self.browser.skip()
                    skipped_count += 1
                    continue
                
                # Log extraction metrics
                self.logger.emit({
                    "event": "profile_extracted",
                    "profile": i,
                    "extracted_len": len(profile_text),
                    "engine": engine,
                    "extract_ms": extract_ms
                })

                # Check if seen (DRY - reuse deduplication)
                profile_hash = hash_profile_text(profile_text)
                if self.seen.is_seen(profile_hash):
                    self.logger.emit({"event": "duplicate", "hash": profile_hash})
                    self.browser.skip()
                    skipped_count += 1
                    continue

                # Mark as seen
                self.seen.mark_seen(profile_hash)

                # Create profile entity
                profile = Profile(raw_text=profile_text)
                criteria_obj = Criteria(text=criteria)

                # Evaluate profile (delegates to use case)
                evaluation = self.evaluate(profile, criteria_obj)
                
                # Check for evaluation errors
                if evaluation.get("decision") == "ERROR":
                    error_msg = evaluation.get("error", "Unknown error")
                    self.logger.emit(
                        {
                            "event": "evaluation_error",
                            "profile": i,
                            "error": error_msg,
                            "error_type": evaluation.get("error_type", "Unknown"),
                            "rationale": evaluation.get("rationale", ""),
                            "skip_reason": f"Decision error: {error_msg[:100]}",
                            "engine": engine,
                            "extracted_len": len(profile_text),
                        }
                    )
                    # Store error in results for UI visibility
                    results.append(
                        {
                            "profile_num": i,
                            "hash": profile_hash,
                            "decision": "ERROR",
                            "rationale": evaluation.get("rationale"),
                            "error": error_msg,
                            "sent": False,
                            "mode": mode,
                        }
                    )
                    # Skip to next profile
                    self.browser.skip()
                    continue

                # Log decision event (only for successful evaluations)
                self.logger.emit(
                    {
                        "event": "decision",
                        "profile": i,
                        "decision": evaluation.get("decision"),
                        "mode": mode,
                        "rationale": evaluation.get("rationale", ""),
                        "score": evaluation.get("score"),
                        "auto_send": evaluation.get("auto_send", False),
                        "engine": engine,
                        "extracted_len": len(profile_text),
                        "decision_json_ok": evaluation.get("decision") in ["YES", "NO"],
                    }
                )

                # Determine if should send (ignoring shadow mode for now)
                would_send = self._should_auto_send(dict(evaluation), mode, False, threshold)

                # Send message if appropriate
                if would_send and evaluation.get("decision") == "YES":
                    draft = evaluation.get("draft", "")
                    if draft and not shadow_mode:
                        # Use send use case with quota
                        success = self.send(draft, 1)
                        if success:
                            sent_count += 1
                            self.logger.emit(
                                {
                                    "event": "sent",
                                    "profile": i,
                                    "ok": True,
                                    "mode": "auto",
                                    "verified": True,
                                }
                            )
                    elif draft and shadow_mode:
                        self.logger.emit({"event": "shadow_send", "profile": i, "would_send": True})

                # Store result
                results.append(
                    {
                        "profile_num": i,
                        "hash": profile_hash,
                        "decision": evaluation.get("decision"),
                        "rationale": evaluation.get("rationale"),
                        "sent": would_send and not shadow_mode,
                        "mode": mode,
                    }
                )

                # Move to next profile
                if evaluation.get("decision") == "NO" or shadow_mode:
                    self.browser.skip()

            except Exception as e:
                # Log detailed error for debugging
                error_detail = {
                    "event": "profile_processing_error",
                    "profile": i,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": str(e.__traceback__) if hasattr(e, "__traceback__") else None,
                }
                self.logger.emit(error_detail)
                
                # Add to results for UI visibility
                results.append(
                    {
                        "profile_num": i,
                        "hash": "error",
                        "decision": "ERROR",
                        "rationale": f"Processing error: {str(e)[:200]}",
                        "error": str(e),
                        "sent": False,
                        "mode": mode,
                    }
                )
                
                # Try to continue
                try:
                    self.browser.skip()
                except Exception:
                    pass

        # Summary
        summary = {
            "total_evaluated": len(results),
            "total_sent": sent_count,
            "total_skipped": skipped_count,
            "mode": mode,
            "shadow": shadow_mode,
            "results": results,
        }

        self.logger.emit({"event": "autonomous_complete", **summary})

        return summary

    def _should_auto_send(
        self, evaluation: dict[str, Any], mode: str, shadow_mode: bool, threshold: float
    ) -> bool:
        """Determine if message should be sent automatically.

        Strategy Pattern: Different logic per mode.

        Args:
            evaluation: Decision result
            mode: Decision mode
            shadow_mode: If True, never send
            threshold: Minimum score/confidence for auto-send

        Returns:
            True if should auto-send
        """
        if shadow_mode:
            return False

        if evaluation.get("decision") != "YES":
            return False

        if mode == "advisor":
            # Advisor mode never auto-sends (requires HIL approval)
            return False

        elif mode == "rubric":
            # Rubric auto-sends if score exceeds threshold
            score = evaluation.get("score", 0)
            return bool(score >= threshold)

        elif mode == "hybrid":
            # Hybrid checks both score and confidence
            score = evaluation.get("score", 0)
            confidence = evaluation.get("confidence", 0)
            # Could use alpha weighting here
            return bool(score >= threshold and confidence >= 0.5)

        return False
