from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
INVENTORY = ROOT / "inventory"
WORKER = ROOT / "backend" / "worker.py"

app = FastAPI(title="P vs NP Module Runner GUI")


class RunRequest(BaseModel):
    id: str
    timeout: int = 8


def load_json(name: str, default):
    path = INVENTORY / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def get_modules():
    return load_json("modules.json", [])


def find_module(module_id: str):
    for item in get_modules():
        if item["id"] == module_id:
            return item
    return None


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "message": "Backend connected."}


@app.get("/api/summary")
def summary():
    return load_json("summary.json", {
        "total": 0,
        "categories": {},
        "error": "No inventory found. Run: python scripts/discover_modules.py"
    })


@app.get("/api/modules")
def modules():
    return get_modules()


@app.get("/api/source/{module_id:path}")
def source(module_id: str):
    item = find_module(module_id)
    if not item:
        return JSONResponse({"error": "Module not found."}, status_code=404)

    try:
        source_text = Path(item["path"]).read_text(encoding="utf-8", errors="replace")
        return {
            "id": item["id"],
            "title": item["title"],
            "source": source_text,
        }
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@app.post("/api/run")
def run_module(req: RunRequest):
    item = find_module(req.id)
    if not item:
        return JSONResponse({"ok": False, "error": "Module not found."}, status_code=404)

    payload = json.dumps({"path": item["path"]})

    start = time.perf_counter()

    try:
        proc = subprocess.run(
            [sys.executable, str(WORKER)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=req.timeout,
        )

        runtime = time.perf_counter() - start

        if proc.returncode != 0:
            return {
                "ok": False,
                "id": item["id"],
                "title": item["title"],
                "runtime_seconds": runtime,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "error": f"Worker exited with code {proc.returncode}",
            }

        try:
            data = json.loads(proc.stdout.strip().splitlines()[-1])
        except Exception:
            data = {
                "ok": False,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "error": "Worker did not return valid JSON.",
            }

        data["id"] = item["id"]
        data["title"] = item["title"]
        data["runtime_seconds"] = runtime
        return data

    except subprocess.TimeoutExpired:
        runtime = time.perf_counter() - start
        return {
            "ok": False,
            "id": item["id"],
            "title": item["title"],
            "runtime_seconds": runtime,
            "stdout": "",
            "stderr": "",
            "error": f"Timed out after {req.timeout} seconds.",
        }


@app.post("/api/run-category/{category}")
def run_category(category: str, limit: int = 25, timeout: int = 8):
    modules = [m for m in get_modules() if m["category"] == category][:limit]
    results = []

    for item in modules:
        result = run_module(RunRequest(id=item["id"], timeout=timeout))
        results.append(result)

    return {
        "category": category,
        "count": len(results),
        "results": results,
    }