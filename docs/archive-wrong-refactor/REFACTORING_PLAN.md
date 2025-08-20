# YC Cofounder Bot - Refactoring Plan

## Overview

This repository needs refactoring to align the codebase with the documented OpenAI CUA architecture. The current implementation uses a paste-based workflow instead of the documented 3-input autonomous flow.

## 📁 Refactoring Documents

The complete refactoring plan is divided into 4 parts:

1. **[REFACTOR_PART_1_FOUNDATION.md](./REFACTOR_PART_1_FOUNDATION.md)**
   - Fix CUA browser adapter to drive entire flow
   - Define autonomous browsing ports
   - Create decision mode interfaces (Advisor/Rubric/Hybrid)
   - Add feature flags for safe migration

2. **[REFACTOR_PART_2_CORE_FLOW.md](./REFACTOR_PART_2_CORE_FLOW.md)**
   - Create ProcessAutonomous use case
   - Integrate decision modes into pipeline
   - Update dependency injection
   - Maintain backward compatibility

3. **[REFACTOR_PART_3_INTERFACE.md](./REFACTOR_PART_3_INTERFACE.md)**
   - Build new 3-input UI panel
   - Add decision mode selector
   - Implement real-time progress display
   - Keep legacy UI behind feature flag

4. **[REFACTOR_PART_4_VALIDATION.md](./REFACTOR_PART_4_VALIDATION.md)**
   - Comprehensive CUA test suite
   - Acceptance criteria validation
   - Deployment validation scripts
   - Rollback procedures

## 📊 Current State Analysis

See `/docs/refactoring/` for detailed audits:
- **CURRENT_CODEBASE_AUDIT.md** - Analysis of existing implementation
- **CURRENT_TEST_AUDIT.md** - Test coverage gaps

## 🎯 Key Issues to Fix

1. **Wrong User Flow**: Currently paste-based, needs 3-input autonomous
2. **CUA Underutilized**: Exists but only for message sending, should drive entire flow
3. **Missing Decision Modes**: Need Advisor, Rubric, and Hybrid modes
4. **Zero CUA Tests**: No test coverage for Computer Use integration

## 🚀 Implementation Strategy

### Phase 1: Foundation (Week 1)
- Implement CUA browser methods
- Create decision mode classes
- Add feature flags
- Write unit tests

### Phase 2: Core Flow (Week 2)
- Build autonomous use case
- Integrate decision modes
- Update dependency injection
- Add integration tests

### Phase 3: Interface (Week 3)
- Create 3-input UI
- Add progress display
- Implement mode selector
- Test UI components

### Phase 4: Validation (Week 4)
- Run acceptance tests
- Performance testing
- Deploy with flags disabled
- Gradual rollout

## ⚙️ Feature Flags for Safe Migration

```bash
# Start with everything disabled
USE_CUA_PRIMARY=false
USE_THREE_INPUT_UI=false
USE_DECISION_MODES=false

# Gradual enablement
USE_CUA_PRIMARY=true      # Enable CUA
USE_DECISION_MODES=true   # Enable modes
USE_THREE_INPUT_UI=true   # Enable new UI
```

## ✅ Success Criteria

- [ ] CUA drives entire browsing flow
- [ ] Three decision modes functional
- [ ] 3-input UI replaces paste UI
- [ ] All tests pass
- [ ] No breaking changes when flags disabled
- [ ] Performance maintained or improved

## 📚 Reference Documentation

- **[OpenAI Computer Use Truth](./OPENAI_COMPUTER_USE_TRUTH.md)** - Critical CUA facts
- **[Model Selection](./MODEL_SELECTION.md)** - Model configuration guide
- **[Main Documentation](/docs)** - Complete system documentation

## 🚨 Important Notes

1. **YOU provide the browser** via Playwright - CUA only analyzes and suggests actions
2. **Use environment variables** for models - never hardcode
3. **Feature flags** enable safe rollback at any time
4. **Test everything** - especially CUA integration which currently has 0% coverage

Start with Part 1 and proceed sequentially through all 4 parts.