# Fix Documentation Archive

This directory contains documentation of various fixes and improvements made to the YC Co-Founder Bot.

## Fix History (Chronological)

### Core Fixes
- `CODEBASE_AUDIT_FIXES.md` - Initial codebase audit and fixes
- `CODEBASE_FIXED_SUMMARY.md` - Summary of codebase improvements
- `FIX_SUMMARY.md` - General fix summary

### GPT-5 Integration Fixes
- `FINDINGS_GPT5_MESSAGE_SENDING.md` - Initial findings on message sending issues
- `GPT5_WORKING_FINAL.md` - GPT-5 working implementation
- `RESPONSES_API_MIGRATION.md` - Migration from Agents SDK to Responses API
- `TEMPERATURE_FIX_FINAL.md` - Temperature parameter handling for GPT-5
- `GPT5_REASONING_ONLY_FIX.md` - Critical fix for reasoning-only responses
- `PRODUCTION_FIX_COMPLETE.md` - Final production fix verification

### Other Improvements
- `TIMEZONE_FIX.md` - UTC timezone consistency across codebase
- `VERIFICATION_COMPLETE.md` - Verification of all fixes
- `FINAL_FIX_COMPLETE.md` - Final comprehensive fix summary

### Post-Mortem
- `WHY_THIS_HAPPENED.md` - Analysis of why production issues occurred despite testing

## Key Learnings

1. **Test Reality, Not Assumptions** - Mock actual API responses, not ideal ones
2. **Defensive Parsing** - Always have fallback parsers for edge cases
3. **Observability First** - Comprehensive logging catches issues early
4. **Integration Testing** - Test against real APIs, not just mocks