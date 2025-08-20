#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
OUT_DIR="$ROOT_DIR/docs/vendor"
MANIFEST="$OUT_DIR/manifest.json"
TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# Define sources: url|relative_output_path (OPENAI ONLY!)
SOURCES=(
  "https://platform.openai.com/docs/guides/computer-use|openai/computer-use.html"
  "https://platform.openai.com/docs/guides/agents|openai/agents.html"  
  "https://platform.openai.com/docs/guides/responses|openai/responses.html"
)

mkdir -p "$OUT_DIR/openai"

# Collect manifest items
manifest_items=()

for entry in "${SOURCES[@]}"; do
  IFS='|' read -r url rel <<< "$entry"
  out_path="$OUT_DIR/$rel"
  out_dir="$(dirname "$out_path")"
  mkdir -p "$out_dir"
  echo "Fetching: $url -> $rel"
  status="ok"
  if ! curl -fsSL "$url" -o "$out_path"; then
    echo "WARN: Failed to fetch $url" >&2
    status="failed"
  fi
  manifest_items+=("{\"url\":\"$url\",\"path\":\"docs/vendor/$rel\",\"fetched_at\":\"$TS\",\"status\":\"$status\"}")
  # Also drop a small sidecar .src file with the URL and timestamp
  printf 'source: %s\nfetched_at: %s\n' "$url" "$TS" > "$out_path.src"
done

# Write manifest
{
  echo '{'
  echo '  "generated_at": '"\"$TS\""','
  echo '  "items": ['
  for i in "${!manifest_items[@]}"; do
    printf '    %s' "${manifest_items[$i]}"
    if [[ $i -lt $((${#manifest_items[@]} - 1)) ]]; then
      printf ','
    fi
    printf '\n'
  done
  echo '  ]'
  echo '}'
} > "$MANIFEST"

echo "Manifest written: $MANIFEST"