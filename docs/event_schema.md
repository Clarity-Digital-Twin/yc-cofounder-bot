# Event Schema Documentation

All events emitted to `.runs/events.jsonl` follow these standardized schemas.

## Core Events

### `decision`
Emitted when a profile is evaluated.
```json
{
  "event": "decision",
  "profile": 0,
  "decision": "YES|NO|ERROR",
  "mode": "ai|rubric|hybrid|advisor",
  "rationale": "string",
  "score": 0.0-1.0,
  "auto_send": true|false,
  "confidence": 0.0-1.0,
  "engine": "cua|playwright",
  "extracted_len": 1234,
  "decision_json_ok": true|false
}
```

### `sent`
Emitted when a message is successfully sent.
```json
{
  "event": "sent",
  "profile": 0,
  "ok": true,
  "mode": "auto|manual",
  "verified": true|false
}
```

### `profile_processing_error`
**IMPORTANT**: Processing failures emit `profile_processing_error`, NOT `error`.
```json
{
  "event": "profile_processing_error",
  "profile": 0,
  "error": "string",
  "traceback": "string"
}
```

### `duplicate`
Emitted when a profile has been seen before.
```json
{
  "event": "duplicate",
  "hash": "16-char-hash"
}
```

### `stopped`
Emitted when execution is halted by stop flag.
```json
{
  "event": "stopped",
  "at_profile": 0,
  "reason": "stop_flag"
}
```

### `shadow_send`
Emitted in shadow mode when a message would have been sent.
```json
{
  "event": "shadow_send",
  "profile": 0,
  "would_send": true
}
```

### `empty_profile`
Emitted when no profile text could be extracted.
```json
{
  "event": "empty_profile",
  "at_profile": 0,
  "engine": "cua|playwright",
  "skip_reason": "string",
  "extract_ms": 123
}
```

### `profile_extracted`
Emitted after successful profile extraction.
```json
{
  "event": "profile_extracted",
  "profile": 0,
  "extracted_len": 1234,
  "engine": "cua|playwright",
  "extract_ms": 123
}
```

## Usage Events

### `model_usage`
Token usage and cost estimates.
```json
{
  "event": "model_usage",
  "tokens_in": 100,
  "tokens_out": 50,
  "cost_est": 0.0015,
  "model": "gpt-5"
}
```

### `decision_latency`
Time taken for decision.
```json
{
  "event": "decision_latency",
  "duration_ms": 1234,
  "mode": "ai|rubric|hybrid"
}
```

## Quota Events

### `quota_check`
```json
{
  "event": "quota_check",
  "daily_used": 5,
  "daily_limit": 25,
  "weekly_used": 20,
  "weekly_limit": 120,
  "can_send": true
}
```

### `quota_exhausted`
```json
{
  "event": "quota_exhausted",
  "type": "daily|weekly",
  "used": 25,
  "limit": 25
}
```

## Login Events

### `auto_login_success`
```json
{
  "event": "auto_login_success"
}
```

### `auto_login_failed`
```json
{
  "event": "auto_login_failed",
  "error": "string"
}
```

### `login_required`
```json
{
  "event": "login_required",
  "has_credentials": true|false
}
```

## Testing Guidelines

1. **Always assert exact event names** - Use the names documented here
2. **Processing errors** - Assert `profile_processing_error` NOT `error`
3. **Event ordering** - `decision` must precede `sent` in the event stream
4. **Required fields** - All fields shown above are required unless marked optional

## Event Emission Order

The guaranteed order for a successful send:
1. `profile_extracted`
2. `decision` 
3. `sent`

For errors:
1. `profile_processing_error` (replaces normal flow)

For duplicates:
1. `duplicate` (replaces evaluation)