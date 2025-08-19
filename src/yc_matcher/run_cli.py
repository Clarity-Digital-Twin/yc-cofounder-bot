from __future__ import annotations

import argparse
from pathlib import Path

from .decision import decide_and_draft
from .templates import load_default_template


def main() -> None:
    p = argparse.ArgumentParser(description="YC matcher CLI (paste-mode)")
    p.add_argument("profile", nargs="?", help="Path to file with profile text; stdin if omitted")
    p.add_argument("--criteria-file", dest="criteria_file", help="Path to criteria text file")
    p.add_argument("--template-file", dest="template_file", help="Path to template file")
    args = p.parse_args()

    profile_text = (
        Path(args.profile).read_text(encoding="utf-8") if args.profile else input()
    )
    criteria = (
        Path(args.criteria_file).read_text(encoding="utf-8") if args.criteria_file else ""
    )
    template = (
        Path(args.template_file).read_text(encoding="utf-8") if args.template_file else load_default_template()
    )

    result = decide_and_draft(criteria=criteria, profile_text=profile_text, template=template)
    print(f"Decision: {result.decision}")
    print(f"Rationale: {result.rationale}")
    if result.message:
        print("\n--- Draft Message ---\n")
        print(result.message)


if __name__ == "__main__":
    main()
