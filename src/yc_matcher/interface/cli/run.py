from __future__ import annotations

import argparse
from pathlib import Path

from ...domain.entities import Criteria, Profile
from ...infrastructure.utils.template_loader import load_default_template
from ..di import build_services


def main() -> None:
    p = argparse.ArgumentParser(description="YC matcher CLI (paste-mode, gated)")
    p.add_argument("profile", nargs="?", help="Path to file with profile text; stdin if omitted")
    p.add_argument("--criteria-file", dest="criteria_file", help="Path to criteria text file")
    p.add_argument("--template-file", dest="template_file", help="Path to template file")
    args = p.parse_args()

    profile_text = Path(args.profile).read_text(encoding="utf-8") if args.profile else input()
    criteria_text = (
        Path(args.criteria_file).read_text(encoding="utf-8") if args.criteria_file else ""
    )
    template_text = (
        Path(args.template_file).read_text(encoding="utf-8")
        if args.template_file
        else load_default_template()
    )

    eval_use, _send_use, _logger = build_services(
        criteria_text=criteria_text,
        template_text=template_text,
        prompt_ver="v1",
        rubric_ver="v1",
    )
    data = eval_use(Profile(raw_text=profile_text), Criteria(text=criteria_text))
    print(f"Decision: {data.get('decision')}")
    print(f"Rationale: {data.get('rationale')}")
    draft = data.get("draft")
    if draft:
        print("\n--- Draft Message ---\n")
        print(draft)


if __name__ == "__main__":
    main()
