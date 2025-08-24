# OpenAI Documentation Contradictions Audit

## 🚨 CRITICAL CONTRADICTIONS FOUND

After auditing all documentation files, here are the contradictions about OpenAI APIs:

---

## 1. **Max Output Tokens** - MASSIVE CONFUSION

### Different Values Documented:
| File | Says | Line/Context |
|------|------|--------------|
| **AGENTS.md** | 4000 | Line 46 now `max_output_tokens=4000` (fixed) |
| **GPT5_FACTS.md** | 4000 | Line 27: `max_output_tokens=4000,  # Supported (up to 128,000!)` |
| **docs/fixes/*.md** | 800 | Multiple files say 800 is correct |
| **docs/API_CONTRACT_RESPONSES.md** | 4000 | Updated default to 4000, up to 128,000 (fixed) |
| **CONTEXT7_TRUTH.md** | 4000 | The authoritative source says 4000 |
| **CLAUDE.md** | 4000 | Updated to match Context7 |

### ✅ TRUTH (from Context7): **4000 tokens default, up to 128,000 max**

---

## 2. **Verbosity Parameter Location** - MAJOR CONFLICT

### Contradictory Information:
| File | Says | Status |
|------|------|--------|
| **docs/fixes/GPT5_REASONING_ONLY_FIX.md** | Top-level `"verbosity": "low"` | ❌ WRONG |
| **docs/fixes/PRODUCTION_FIX_COMPLETE.md** | `params["verbosity"] = "low"` | ❌ WRONG |
| **GPT5_API_AUDIT_AUG2025.md** | Top-level verbosity | ❌ WRONG |
| **CONTEXT7_TRUTH.md** | `text: { verbosity: "low" }` | ✅ CORRECT |
| **CLAUDE.md** | Nested in text object | ✅ CORRECT |

### ✅ TRUTH (from Context7): **Nested in `text` object**

---

## 3. **GPT-5 Model ID** - CONSISTENT BUT NEEDS REINFORCEMENT

### All files agree:
- Model ID: `gpt-5` (NOT `gpt-5-thinking`)
- ✅ This is consistent across all docs

---

## 4. **Temperature Parameter** - INCONSISTENT DOCUMENTATION

### Different Claims:
| File | Says | Context |
|------|------|---------|
| **docs/fixes/TEMPERATURE_FIX_FINAL.md** | Supported | "temperature works" |
| **Old GPT5_FACTS.md line 42** | "NO temperature" | Contradicts reality |
| **CONTEXT7_TRUTH.md** | Supported 0-2 | Authoritative |

### ✅ TRUTH (from Context7): **Temperature IS supported (0-2 range)**

---

## 5. **Reasoning Effort Parameter** - NOT DOCUMENTED IN OLD FILES

### Status:
- **Missing from**: All docs/fixes/*.md files
- **Missing from**: docs/archive-cleanup/*.md files  
- **Only in**: CONTEXT7_TRUTH.md and CLAUDE.md

### ✅ TRUTH (from Context7): **`reasoning: { effort: "minimal" }` for speed**

---

## 6. **Response Format** - CONFUSION ABOUT SUPPORT

### Conflicting Info:
| File | Says |
|------|------|
| **docs/API_CONTRACT_RESPONSES.md** | Use `response_format=json_schema` |
| **Code reality** | Falls back when it fails |
| **CONTEXT7_TRUTH.md** | May not be in SDK yet |

### ✅ TRUTH: **Try it, but fallback if unsupported**

---

## 7. **API Endpoint** - MOSTLY CONSISTENT

### Agreement:
- GPT-5 uses **Responses API** (`client.responses.create`)
- GPT-4 uses **Chat Completions API** (`client.chat.completions.create`)
- ✅ This is consistent

---

## 8. **Previous Response ID** - UNDERDOCUMENTED

### Status:
- Only mentioned in CONTEXT7_TRUTH.md
- Missing from all other documentation
- Not used in most code examples

### ✅ TRUTH (from Context7): **Use for multi-turn conversations**

---

## FILES WITH MOST CONTRADICTIONS (Need Fixing)

1. **docs/fixes/*.md** - All say 800 tokens (wrong!)
2. **docs/archive-cleanup/*.md** - Outdated information
3. **GPT5_API_AUDIT_AUG2025.md** - Based on speculation
4. **AGENTS.md** - Says 800 tokens
5. **docs/API_CONTRACT_RESPONSES.md** - Says 600-800 tokens

---

## FILES THAT ARE CORRECT (Keep as Reference)

1. **CONTEXT7_TRUTH.md** - The authoritative source
2. **CLAUDE.md** - Recently updated to match Context7
3. **CONTEXT7_IMPLEMENTATION_SUMMARY.md** - Documents the fixes

---

## 🔧 ACTION PLAN TO FIX ALL CONTRADICTIONS

### Phase 1: Update Critical Files
1. [x] Fix AGENTS.md - Change 800 to 4000
2. [x] Fix docs/API_CONTRACT_RESPONSES.md - Update token limits
3. [x] Archive GPT5_API_AUDIT_AUG2025.md - Mark as outdated

### Phase 2: Fix docs/fixes/*.md
1. [x] Update key references to 800 tokens → 4000 (remaining occurrences are in DEPRECATED/archived files)
2. [x] Fix verbosity parameter location (use `text: { verbosity: "low" }`)
3. [x] Add reasoning.effort documentation

### Phase 3: Clean Archive Files
1. [ ] Add deprecation notice to docs/archive-cleanup/*.md
2. [ ] Add deprecation notice to docs/archive/*.md
3. [ ] Point all to CONTEXT7_TRUTH.md

### Phase 4: Create Single Source of Truth
1. [ ] Create OPENAI_API_REFERENCE.md with all correct info
2. [ ] Update README.md to reference it
3. [ ] Add to .env.example comments

---

## 🎯 The Single Truth

When in doubt, **ALWAYS** refer to:
1. **CONTEXT7_TRUTH.md** - The Context7 MCP-verified documentation
2. **The actual OpenAI API response** - Test with real API calls
3. **Context7 MCP** - Query for latest documentation

---

*Generated: December 2025*
