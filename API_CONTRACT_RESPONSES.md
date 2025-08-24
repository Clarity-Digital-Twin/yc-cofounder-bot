# GPT-5 + Responses API – Contract for YC-Matcher

## 1) Models & selection (startup)

1. **Primary decision model**: `gpt-5` (or a concrete snapshot like `gpt-5-2025-08-07`). List models and pick the best available at startup; cache it for the run. ([OpenAI Platform][2])
2. **Tool/planning model** (optional): your CUA model (e.g., `"computer-use-preview"`). Use only via **Responses** with the Computer Use tool. ([OpenAI Platform][3])
3. **Fallback**: a Chat-Completions model (`gpt-4o` preferred, then `gpt-4o-mini`, lastly `gpt-4`) is okay *only* for the text-only decision call if GPT-5 is unavailable. **Do not** use Chat for tool use. ([OpenAI Platform][1])

---

## 2) Decision call (Responses API) – Request shape

> Purpose: score a candidate and produce `{decision,rationale,draft,score,confidence}`.

4. **Endpoint**: `client.responses.create(...)`. **Do not** use Chat for GPT-5. ([OpenAI Platform][1])
5. **Required params**

   * `model`: `"gpt-5"` (or your selected snapshot). ([OpenAI Platform][2])
   * `input`: array of messages (at least one system + one user), e.g.

     * `{"role":"system","content": system_instructions}`
     * `{"role":"user","content": user_payload_text}`
       (This is the Responses equivalent of chat messages.) ([OpenAI Platform][1])
   * `max_output_tokens`: **required** to control length. Use **≥ 600–800** to allow rationale + draft. ([OpenAI Platform][1])
6. **Structured output (preferred)**

   * `response_format: {"type":"json_schema","json_schema":{...,"strict":true}}`
   * Schema: object with exact keys: `"decision"` ∈ {YES,NO}, `"rationale"` string, `"draft"` string, `"score"` \[0..1], `"confidence"` \[0..1], no additional properties. ([OpenAI Platform][4])
   * NOTE: If your account/model revision ever errors on `response_format`, drop it and **instruct JSON in the prompt**, then parse text (see §4). (We’ve seen model/tenant variance—guard it.) ([OpenAI Platform][1])
7. **Optional params**

   * `temperature`: **Responses supports it**, but model families differ. Keep it **low (0.2–0.5)** for JSON reliability. If the model rejects `temperature`, omit it. Code must treat it as **optional**. ([OpenAI Platform][1])
   * (Streaming etc. is optional; not required for this app.) ([OpenAI Platform][1])

---

## 3) Decision call – Input assembly (your app)

8. **System**: durable rules (“You are an expert recruiter… Return a JSON object with keys decision, rationale, draft, score, confidence. Your entire response must be valid JSON.”).
9. **User**: one joined text block that includes:

   * **YOUR\_PROFILE** (who you are)
   * **MATCH\_CRITERIA** (what you want)
   * **CANDIDATE\_PROFILE\_TEXT** (full DOM-extracted text)
   * **MESSAGE\_TEMPLATE** (format/style constraints for the draft)
     (Put them under clear headings so the model can reference them cleanly.)
10. **Length control**: let the model decide draft length; your template should bound it (e.g., 40–100 words). Use `max_output_tokens` to enforce upper bound. ([OpenAI Platform][1])

---

## 4) Decision call – Response parsing (robust)

> Reasoning models can emit multiple items per response. Don’t “skip” when you only read one.

11. **Preferred**: if the SDK/object has `response.output_text`, use that string directly. It concatenates the textual parts for you. ([OpenAI Platform][5])
12. **Manual fallback**: iterate `response.output` **in order**:

    * Skip any item where `item.type == "reasoning"` (you may log it). ([OpenAI Platform][5])
    * For `item.type == "message"`, join all `content[*].text` (and/or content items whose `type == "output_text"`). The joined text should be your JSON document (with structured outputs) or your free-text answer (unstructured). ([OpenAI Platform][5])
13. **Validate JSON**: if using `json_schema`, the SDK should yield valid JSON. If you instructed JSON, run a strict parser and log schema errors. Emit events: `gpt5_parse_method`, `output_types`, `output_text_len`, `json_valid`(T/F). ([OpenAI Platform][4])
14. **Usage**: log `usage.input_tokens` and `usage.output_tokens` if present. ([OpenAI Platform][1])

---

## 5) Computer Use (CUA) loop – Planner + your executor

> Model proposes actions; **your Playwright** executes them and returns screenshots/state until done.

15. **Start**:

    ```py
    client.responses.create(
      model=CUA_MODEL,
      tools=[{"type":"computer_use"}],
      input=[{"role":"user","content": instruction}],
      # optional: previous_response_id to chain turns
    )
    ```

    (Use your CUA model; tool type name per docs.) ([OpenAI Platform][3])
16. **Observe**: inspect `response.output` for a `computer_call` item; it will contain a single **action** with a `type` (e.g., `mouse.click`, `keyboard.type`, `goto`) and parameters (e.g., `{coordinates:{x,y}}` or `{text:"..."}`). Execute it with Playwright. ([OpenAI Platform][3])
17. **Return results**: send a **follow-up** `responses.create` with:

    * `previous_response_id: <the last response id>`, and
    * an **input** item of type `computer_call_output` including the original `call_id` and evidence (usually a base64 screenshot), e.g.:

      ```json
      {
        "type":"computer_call_output",
        "call_id": "<id>",
        "output": { "image_base64": "<...>" }
      }
      ```

      (Exact field names match docs/spec of the tool; your code already wraps screenshot encoding.) ([OpenAI Platform][3])
18. **Loop** until there is **no `computer_call`** in the next turn (or hit your STOP/turn-cap). **Never** evaluate the profile from screenshots; instead, after CU has expanded the page, extract **full DOM text** with Playwright and pass that to the decision call. (That’s the official pattern.) ([OpenAI Platform][3])

---

## 6) Chaining turns (both flows)

19. **previous\_response\_id**: to keep context between turns (CUA loop or multi-step reasoning), include the prior `response.id` in the next `responses.create(...)`. ([OpenAI Platform][1])
20. **STOP / turn caps**: enforce an app-level STOP flag and a `max_turns` guard (e.g., 10–40) so tools never loop. Log `stopped` with reason. ([OpenAI Platform][3])

---

## 7) Error handling & retries

21. **Model/param variance**: if the API returns a 400 for `response_format` or `temperature`, **omit** those fields and fall back to **prompt-instructed JSON**. Keep a single retry with exponential backoff for transient 5xx. Log `response_format_fallback` or `retry_attempt`. ([OpenAI Platform][1])
22. **Parse failures**: when `output_text` is empty or JSON parse fails, emit `gpt5_parse_failure` with `output_items`, `output_types`, and first 200 chars of the raw text; then degrade to “ERROR” decision with rationale and stop sending. ([OpenAI Platform][5])
23. **Usage logging**: always emit a `model_usage` event with `{model, tokens_in, tokens_out}` if present. ([OpenAI Platform][1])

---

## 8) What your app MUST log per profile

24. `profile_extracted` `{len, engine}` (DOM text length; “cua” or “playwright”).
25. `decision` `{decision, rationale, score, confidence, decision_json_ok}`.
26. `model_usage` `{model, tokens_in, tokens_out}`.
27. `send_attempt` → `sent` (or `verify_failed`).
28. `profile_processing_error` with the exception message and stage (read/decide/fill/send).
29. For CUA: `cua_parse_method`, `cua_reasoning_item` (truncated), `cua_turn` (n).
    (These make “why no send?” instantly obvious.)

---

## 9) Selector contract (YC UI – current)

30. **Message box**: try in order

* `textarea[placeholder*="excited about potentially working" i]`
* `textarea[placeholder*="type a short message" i]`
* fallback: generic `textarea`, `[contenteditable="true"]`, `div[role="textbox"]`.
  Focus, short wait, clear, then fill.

31. **Send button**:

* `button:has-text("Invite to connect")` → green button
* fallback: `button:has-text("Invite")`, `button:has-text("Send")`, `button:has-text("Connect")`, `button[type="submit"]`.
  If none found, press `Enter` in the focused input as last resort.
  (Selectors are app-specific; keep them in one place with debug logs.)

---

## 10) Environment / config keys (single source of truth)

32. `OPENAI_API_KEY` (required).
33. `OPENAI_DECISION_MODEL` (optional; resolved at startup; prefer `gpt-5`).
34. `CUA_MODEL` (required if CUA enabled).
35. `ENABLE_CUA`, `ENABLE_PLAYWRIGHT_FALLBACK`.
36. `PACE_MIN_SECONDS`, `DAILY_QUOTA`, `WEEKLY_QUOTA`, `SHADOW_MODE`.
37. `PLAYWRIGHT_HEADLESS`, `PLAYWRIGHT_BROWSERS_PATH`.
    (Load via your `config.py` getters—not ad-hoc `os.getenv`—so UI, DI, and infra never disagree.)

---

## 11) Default knobs (ship these)

38. Decision call: `max_output_tokens=800`, `temperature=0.3` **if accepted**, else omit; `response_format=json_schema` **if accepted**, else prompt-enforce JSON; two-attempt retry on 5xx; strict JSON parse with errors logged. ([OpenAI Platform][1])
39. CUA loop: `max_turns=10–40`, STOP checked **before** making a turn; return immediately if set. ([OpenAI Platform][3])
40. Parser: prefer `output_text`; manual iteration fallback; always log `output_types` + `output_text_len`. ([OpenAI Platform][5])

---

## 12) “If you see this, do that” (gotchas)

41. **Only “reasoning” item, no text** → you’re reading the first item only. Use `output_text` or iterate `output`. ([OpenAI Platform][5])
42. **400: unsupported param** → remove `response_format` or `temperature` for this model/tenant; fallback to prompt-forced JSON. ([OpenAI Platform][1])
43. **Empty draft but YES** → enforce schema (draft must be string), treat as parse failure; don’t send. ([OpenAI Platform][4])
44. **CUA loops or stalls** → check you’re returning `computer_call_output` with screenshot and using `previous_response_id`; enforce `max_turns`. ([OpenAI Platform][3])
45. **“Skipping” feeling** → confirm `profile_extracted` len>0, `decision` event recorded, and parse logs show `output_text_len>0`. If zero, it’s a parse/schema issue—not a match decision.

---

## 13) Minimal acceptance tests (keep green)

46. **Decision shape test** (real call or sandbox): returns JSON with all fields; `output_text_len>0`. ([OpenAI Platform][1])
47. **Parser test**: response with `[reasoning, message]` yields non-empty text. ([OpenAI Platform][5])
48. **CUA loop test**: single `computer_call` → executor executes → follow-up with `computer_call_output` → next response has no call. ([OpenAI Platform][3])
49. **Selector test**: can locate YC message box and “Invite to connect” on a fixture page and fill/click successfully.

---

If you drop this file into `/docs/API_CONTRACT_RESPONSES.md` (and point your team there), nobody will be confused again.

If you want, I can also output a **one-page JSON Schema** (for your codebase) representing the **in/out contract** of the decision function—easy to validate in unit tests.

[1]: https://platform.openai.com/docs/api-reference/responses "OpenAI Platform"
[2]: https://platform.openai.com/docs/models/gpt-5 "OpenAI Platform"
[3]: https://platform.openai.com/docs/guides/tools-computer-use "OpenAI Platform"
[4]: https://platform.openai.com/docs/guides/structured-outputs "OpenAI Platform"
[5]: https://platform.openai.com/docs/guides/reasoning "OpenAI Platform"
