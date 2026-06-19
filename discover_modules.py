from __future__ import annotations

import json
from pathlib import Path
import p_vs_np


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "inventory"
INVENTORY.mkdir(exist_ok=True)


PACKAGES = {
    "database_problems": p_vs_np.database_problems,
    "flow_problems": p_vs_np.flow_problems,
    "graph_theory": p_vs_np.graph_theory,
    "network_design": p_vs_np.network_design,
}


def title_from_filename(path: Path) -> str:
    name = path.stem
    name = name.replace("_", " ").replace("-", " ")
    name = name.replace("|", "")
    return " ".join(part.capitalize() for part in name.split())


def discover():
    records = []

    for category, package in PACKAGES.items():
        package_dir = Path(package.__file__).resolve().parent

        for file in sorted(package_dir.glob("*.py")):
            if file.name == "__init__.py":
                continue

            source = file.read_text(encoding="utf-8", errors="replace")
            records.append({
                "id": f"{category}/{file.stem}",
                "title": title_from_filename(file),
                "category": category,
                "filename": file.name,
                "path": str(file),
                "source_lines": len(source.splitlines()),
                "has_print": "print(" in source or "print (" in source,
                "has_input": "input(" in source,
                "has_main_guard": "__main__" in source,
                "size_bytes": file.stat().st_size,
            })

    summary = {
        "total": len(records),
        "categories": {
            category: sum(1 for r in records if r["category"] == category)
            for category in PACKAGES
        }
    }

    (INVENTORY / "modules.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    (INVENTORY / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    discover()