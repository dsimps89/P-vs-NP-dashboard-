from __future__ import annotations

import importlib
import inspect
import json
import traceback
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
INVENTORY = ROOT / "inventory"

app = FastAPI(title="P vs NP Universal GUI")

app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")


class RunRequest(BaseModel):
    qualified_name: str
    args: list[Any] = []
    kwargs: dict[str, Any] = {}


def load_json(name: str, default):
    path = INVENTORY / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_qualified_name(qualified_name: str):
    module_name, attr_name = qualified_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


@app.get("/api/summary")
def summary():
    return load_json("summary.json", {
        "error": "No inventory found. Run: python scripts/discover_p_vs_np.py"
    })


@app.get("/api/capabilities")
def capabilities():
    return load_json("capabilities.json", [])


@app.get("/api/functions")
def functions():
    return load_json("functions.json", [])


@app.get("/api/classes")
def classes():
    return load_json("classes.json", [])


@app.get("/api/modules")
def modules():
    return load_json("modules.json", [])


@app.post("/api/run")
def run(req: RunRequest):
    try:
        obj = resolve_qualified_name(req.qualified_name)

        if inspect.isclass(obj):
            instance = obj(*req.args, **req.kwargs)
            return {
                "ok": True,
                "type": "class_instance",
                "result": repr(instance),
            }

        if callable(obj):
            result = obj(*req.args, **req.kwargs)
            return {
                "ok": True,
                "type": "function_result",
                "result": repr(result),
            }

        return {
            "ok": False,
            "error": "Resolved object is not callable.",
        }

    except Exception:
        return JSONResponse({
            "ok": False,
            "error": traceback.format_exc(limit=8),
        }, status_code=400)


@app.post("/api/run-batch-smoke")
def run_batch_smoke(limit: int = 25):
    caps = load_json("capabilities.json", [])
    results = []

    for cap in caps[:limit]:
        qn = cap["qualified_name"]

        try:
            obj = resolve_qualified_name(qn)
            sig = inspect.signature(obj)

            # Only smoke-run no-argument callables.
            required = [
                p for p in sig.parameters.values()
                if p.default is inspect._empty
                and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
            ]

            if required:
                results.append({
                    "qualified_name": qn,
                    "ok": None,
                    "status": "skipped_requires_args",
                    "required_args": [p.name for p in required],
                })
                continue

            value = obj()
            results.append({
                "qualified_name": qn,
                "ok": True,
                "status": "ran",
                "result": repr(value)[:500],
            })

        except Exception as exc:
            results.append({
                "qualified_name": qn,
                "ok": False,
                "status": "error",
                "error": str(exc),
            })

    return {
        "count": len(results),
        "results": results,
    }