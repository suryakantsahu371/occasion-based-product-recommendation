"""Print a data-audit summary of the catalog (phase 1 verification, referenced from the README)."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.adapter import load_products, published  # noqa: E402
from app.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    products = load_products(settings.products_path, settings)
    live = published(products)
    print(f"total payloads        : {len(products)}")
    print(f"status breakdown      : {dict(Counter(p.status for p in products))}")
    print(f"published (indexable) : {len(live)}")
    print(f"excluded              : {[p.title for p in products if not p.is_published]}")
    flagged = [p for p in live if p.quality_flags]
    print(f"quality-flagged (live): {len(flagged)}")
    for p in flagged:
        print(f"  - {p.title!r:40} {p.quality_flag}")
    groups = Counter(p.group_key for p in live)
    print(f"product groups        : {len(groups)} (largest: {groups.most_common(1)[0][1]} products)")
    print(f"shops                 : {sorted({p.shop for p in live})}")
    print(f"kept extra descriptions: {sum(bool(p.extra_description) for p in live)}")


if __name__ == "__main__":
    main()
