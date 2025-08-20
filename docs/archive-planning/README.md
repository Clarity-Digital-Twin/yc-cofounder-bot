# Archived Planning Documents

This directory contains planning documents from the initial refactoring strategy phase. These documents describe the transition from a "manual paste" workflow to the OpenAI CUA autonomous approach.

## Why Archived?

These documents were created when the codebase was still using a manual paste-and-evaluate workflow. They detail the migration strategy to move to OpenAI Computer Use. Since we've now committed to the CUA approach as documented in `/docs`, these planning documents are archived for historical reference.

## Contents

- **REFACTORING_STRATEGY.md** - Professional refactoring approach using TDD and feature flags
- **IMPLEMENTATION_ROADMAP.md** - 5-week migration plan from manual to CUA
- **CODEBASE_AUDIT.md** - Analysis of the old manual-paste codebase
- **AUDIT_STATUS.md** - External auditor review status

## Current Status

The project now uses OpenAI Computer Use via the Responses API where:
1. YOU provide the browser via Playwright
2. CUA analyzes screenshots and suggests actions
3. YOU execute the actions in your browser
4. The loop continues until task completion

See `/docs` for the current, accurate documentation.