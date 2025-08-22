from typing import Any

from yc_matcher.domain.entities import Criteria, Profile
from yc_matcher.infrastructure.openai_decision import OpenAIDecisionAdapter


class FakeResp:
    def __init__(self, output: dict[str, Any], usage: dict[str, int] | None = None) -> None:
        self.output = output
        self.usage = usage or {"input_tokens": 123, "output_tokens": 456}
        # For chat.completions API
        self.choices = [
            type(
                "obj",
                (object,),
                {
                    "message": type(
                        "obj",
                        (object,),
                        {
                            "content": '{"decision": "YES", "rationale": "fits", "draft": "Hello [Name]", "score": 0.9, "confidence": 0.95}'
                        },
                    )()
                },
            )()
        ]


class FakeClient:
    class _ChatCompletions:
        def create(self, **_: Any) -> FakeResp:
            # Return a chat completion response
            return FakeResp(
                {
                    "decision": "YES",
                    "rationale": "fits",
                    "draft": "Hello [Name]",
                    "extracted": {"name": "Alex"},
                }
            )

    class _Chat:
        def __init__(self) -> None:
            self.completions = FakeClient._ChatCompletions()

    def __init__(self) -> None:
        self.chat = FakeClient._Chat()
        # Keep old responses for backward compatibility if needed
        self.responses = None


class LoggerList:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, ev: dict[str, Any]) -> None:
        self.events.append(ev)


def test_openai_decision_adapter_returns_schema_like_payload_and_logs_usage():
    client = FakeClient()
    log = LoggerList()
    adapter = OpenAIDecisionAdapter(
        client=client, logger=log, model="gpt-test", prompt_ver="vX", rubric_ver="rY"
    )
    out = adapter.evaluate(
        Profile(raw_text="John Doe\nProjects..."), Criteria(text="python,fastapi")
    )
    assert out["decision"] == "YES"
    assert out["draft"].startswith("Hello ")
    assert out.get("prompt_ver") == "vX"
    assert out.get("rubric_ver") == "rY"
    kinds = [e.get("event") for e in log.events]
    assert "model_usage" in kinds
