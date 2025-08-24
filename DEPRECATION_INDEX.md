# Deprecation Index - December 2025

## Purpose
This document indexes all deprecated documentation files that contain outdated OpenAI API information. These files are preserved for historical reference but should NOT be used for current implementation guidance.

---

## 🚨 SINGLE SOURCE OF TRUTH

For accurate, Context7-verified OpenAI API documentation, use ONLY:

1. **[CONTEXT7_TRUTH.md](./CONTEXT7_TRUTH.md)** - Raw Context7 MCP findings
2. **[OPENAI_API_REFERENCE.md](./OPENAI_API_REFERENCE.md)** - Comprehensive reference guide
3. **[CODE_ALIGNMENT_REPORT.md](./CODE_ALIGNMENT_REPORT.md)** - Current implementation status

---

## Deprecated Files List

### Root Level Deprecated
| File | Reason | Status |
|------|--------|--------|
| `GPT5_API_AUDIT_AUG2025.md` | Based on speculation before Context7 | ✅ Deprecated banner added |
| `GPT5_FACTS.md` | Contains outdated parameters | ✅ Updated with corrections |

### `docs/archive-cleanup/` (27 files)
All files in this directory are deprecated. Key files with OpenAI contradictions:

| File | Issue | Status |
|------|-------|--------|
| `GPT5_FACTS.md` | Wrong token limits, missing parameters | ✅ Deprecated banner added |
| `ERROR_HANDLING_IMPROVEMENTS.md` | References 800 tokens | ✅ Deprecated banner added |
| `FIXES_SUMMARY.md` | Outdated parameter examples | ✅ Deprecated banner added |
| `SYSTEMATIC_DEBUGGING_STRATEGY.md` | Wrong API parameters | ✅ Deprecated banner added |
| `CANONICAL_TRUTH.md` | References "gpt-5-thinking" | ❌ Contains wrong model ID |
| `SSOT.md` | Mixed correct/incorrect info | ⚠️ Partially outdated |
| `FINAL_TRUTH.md` | References "gpt-5-thinking" | ❌ Contains wrong model ID |
| `GPT5_RESOLUTION_SUMMARY.md` | Old parameter names | ⚠️ Historical context |
| `MODEL_RESOLUTION_IMPLEMENTED.md` | References old model names | ⚠️ Historical context |
| `IMPLEMENTATION_PLAN.md` | Outdated implementation | ⚠️ Historical context |
| `AUDIT_AND_PLAN.md` | References "gpt-5-thinking" | ❌ Contains wrong model ID |

### `docs/archive/` (12 files)
| File | Issue | Status |
|------|-------|--------|
| `HOW_IT_ACTUALLY_WORKS.md` | References "gpt-5-thinking" | ✅ Deprecated banner added |
| `AGENTS.md` | Different from root version | ⚠️ Historical version |
| Other files | No OpenAI content | ✅ No changes needed |

### `docs/fixes/` (9 files)
| File | Issue | Status |
|------|-------|--------|
| `TEMPERATURE_FIX_FINAL.md` | Updated to 4000 tokens | ✅ Fixed |
| `GPT5_WORKING_FINAL.md` | Updated to 4000 tokens | ✅ Fixed |
| `GPT5_REASONING_ONLY_FIX.md` | Updated to nested verbosity | ✅ Fixed |
| `PRODUCTION_FIX_COMPLETE.md` | Shows verbosity evolution | ✅ Historical context |

---

## Common Outdated Patterns to Avoid

### ❌ WRONG Patterns Found in Deprecated Files:

1. **Model ID**: `gpt-5-thinking` → ✅ Use `gpt-5`
2. **Token Limit**: `max_output_tokens=800` → ✅ Use `4000` (up to 128,000)
3. **Verbosity**: Top-level `"verbosity": "low"` → ✅ Use `text: { "verbosity": "low" }`
4. **Missing**: No `reasoning.effort` → ✅ Add `reasoning: { "effort": "minimal" }`
5. **Temperature**: "Not supported" → ✅ IS supported (0-2 range)
6. **API**: Chat Completions for GPT-5 → ✅ Use Responses API

---

## Migration Guide

If you find yourself looking at a deprecated file:

1. **Stop** - Don't use the information
2. **Check** - Look at [OPENAI_API_REFERENCE.md](./OPENAI_API_REFERENCE.md)
3. **Verify** - Cross-reference with [CONTEXT7_TRUTH.md](./CONTEXT7_TRUTH.md)
4. **Test** - Run `make check-cua` to verify your setup

---

## Archival Recommendation

To prevent confusion, consider:

1. **Move all deprecated files** to a single `docs/DEPRECATED_ARCHIVE/` folder
2. **Add `.deprecated` extension** to filenames
3. **Update `.gitignore`** to exclude from searches
4. **Create redirect notes** in original locations

---

## Search Filter

When searching for OpenAI information, exclude deprecated content:

```bash
# Exclude deprecated directories
grep -r "pattern" . \
  --exclude-dir=docs/archive-cleanup \
  --exclude-dir=docs/archive \
  --exclude="*DEPRECATED*"
```

---

*Last Updated: December 2025*
*Status: All major contradictions resolved*