from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import traceback
from pathlib import Path
from types import ModuleType
from typing import Any


PACKAGE_CANDIDATES = [
    "p_vs_np",
    "p_vs_np_python",
    "p_vs_np_problems",
    "p_vs_np_package",
]


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "inventory"
INVENTORY.mkdir(exist_ok=True)


def try_import_package() -> tuple[str, ModuleType]:
    errors = {}

    for name in PACKAGE_CANDIDATES:
        try:
            return name, importlib.import_module(name)
        except Exception as exc:
            errors[name] = str(exc)

    raise RuntimeError(
        "Could not import the package. Tried: "
        + ", ".join(PACKAGE_CANDIDATES)
        + "\nErrors:\n"
        + json.dumps(errors, indent=2)
    )


def safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return "(signature unavailable)"


def safe_doc(obj: Any, limit: int = 500) -> str:
    doc = inspect.getdoc(obj) or ""
    doc = " ".join(doc.split())
    return doc[:limit]


def walk_modules(package_name: str, package: ModuleType) -> list[dict]:
    modules = [{
        "name": package_name,
        "is_package": hasattr(package, "__path__"),
        "origin": getattr(package, "__file__", None),
        "error": None,
    }]

    if not hasattr(package, "__path__"):
        return modules

    for info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        record = {
            "name": info.name,
            "is_package": info.ispkg,
            "origin": None,
            "error": None,
        }

        try:
            mod = importlib.import_module(info.name)
            record["origin"] = getattr(mod, "__file__", None)
        except Exception:
            record["error"] = traceback.format_exc(limit=3)

        modules.append(record)

    return modules


def inspect_module(module_name: str) -> tuple[list[dict], list[dict]]:
    functions = []
    classes = []

    try:
        mod = importlib.import_module(module_name)
    except Exception as exc:
        return functions, classes

    for name, obj in inspect.getmembers(mod):
        if name.startswith("_"):
            continue

        if inspect.isfunction(obj):
            functions.append({
                "name": name,
                "qualified_name": f"{module_name}.{name}",
                "module": module_name,
                "signature": safe_signature(obj),
                "doc": safe_doc(obj),
                "source_available": inspect.getsourcefile(obj) is not None,
            })

        elif inspect.isclass(obj):
            methods = []
            for m_name, m_obj in inspect.getmembers(obj):
                if m_name.startswith("_"):
                    continue
                if inspect.isfunction(m_obj) or inspect.ismethod(m_obj):
                    methods.append({
                        "name": m_name,
                        "signature": safe_signature(m_obj),
                        "doc": safe_doc(m_obj, 250),
                    })

            classes.append({
                "name": name,
                "qualified_name": f"{module_name}.{name}",
                "module": module_name,
                "signature": safe_signature(obj),
                "doc": safe_doc(obj),
                "methods": methods,
            })

    return functions, classes


def infer_category(qualified_name: str) -> str:
    lower = qualified_name.lower()

    rules = [
        ("graph", ["graph", "clique", "vertex", "edge", "hamiltonian", "color", "colour", "dominating", "matching"]),
        ("sat", ["sat", "satisfiability", "cnf", "boolean"]),
        ("set", ["set", "cover", "packing", "partition"]),
        ("scheduling", ["schedule", "job", "shop", "machine"]),
        ("routing", ["path", "tour", "travel", "route"]),
        ("optimization", ["opt", "min", "max", "integer", "linear"]),
        ("number", ["number", "integer", "prime", "subset_sum"]),
    ]

    for category, terms in rules:
        if any(term in lower for term in terms):
            return category

    return "uncategorized"


def infer_visualizer(qualified_name: str, signature: str) -> str:
    text = f"{qualified_name} {signature}".lower()

    if any(x in text for x in ["graph", "edge", "vertex", "clique", "path", "cycle", "color"]):
        return "graph"
    if any(x in text for x in ["set", "cover", "subset", "partition"]):
        return "set"
    if any(x in text for x in ["matrix", "array", "grid"]):
        return "matrix"
    if any(x in text for x in ["sat", "cnf", "clause", "boolean"]):
        return "boolean"
    return "generic"


def build_capabilities(functions: list[dict], classes: list[dict]) -> list[dict]:
    capabilities = []

    for f in functions:
        capabilities.append({
            "kind": "function",
            "name": f["name"],
            "qualified_name": f["qualified_name"],
            "category": infer_category(f["qualified_name"]),
            "visualizer": infer_visualizer(f["qualified_name"], f["signature"]),
            "signature": f["signature"],
            "doc": f["doc"],
        })

    for c in classes:
        capabilities.append({
            "kind": "class",
            "name": c["name"],
            "qualified_name": c["qualified_name"],
            "category": infer_category(c["qualified_name"]),
            "visualizer": infer_visualizer(c["qualified_name"], c["signature"]),
            "signature": c["signature"],
            "doc": c["doc"],
            "method_count": len(c["methods"]),
        })

    return capabilities


def write_json(name: str, payload: Any) -> None:
    path = INVENTORY / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {path}")


def main():
    package_name, package = try_import_package()

    modules = walk_modules(package_name, package)

    all_functions = []
    all_classes = []

    for m in modules:
        if m["error"]:
            continue

        functions, classes = inspect_module(m["name"])
        all_functions.extend(functions)
        all_classes.extend(classes)

    capabilities = build_capabilities(all_functions, all_classes)

    summary = {
        "package_import_name": package_name,
        "package_file": getattr(package, "__file__", None),
        "module_count": len(modules),
        "function_count": len(all_functions),
        "class_count": len(all_classes),
        "capability_count": len(capabilities),
        "categories": sorted(set(c["category"] for c in capabilities)),
        "visualizers": sorted(set(c["visualizer"] for c in capabilities)),
    }

    write_json("summary.json", summary)
    write_json("modules.json", modules)
    write_json("functions.json", all_functions)
    write_json("classes.json", all_classes)
    write_json("capabilities.json", capabilities)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()