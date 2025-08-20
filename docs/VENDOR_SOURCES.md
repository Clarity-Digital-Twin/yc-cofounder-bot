Vendor Documentation (Fetched Artifacts)

Purpose
- Keep a local snapshot of critical external docs used for implementation (offline reference, auditability).
- Source: OpenAI CUA documentation

Layout
- docs/vendor/
  - openai/
    - computer-use.html          # Computer Use guide
    - agents.html                # Agents SDK guide
    - responses.html             # Responses API guide
  - manifest.json                # Fetch metadata (timestamp, status)

How to update
```bash
./scripts/fetch_vendor_docs.sh
# Outputs files under docs/vendor and updates manifest.json
```

Notes
- This fetch uses public documentation pages; URLs may change. If a page fails, update the script with the new URL and re-run.
- Use these as reference only. Always confirm exact API fields in the official docs before shipping changes.