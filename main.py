import inspect
from fastapi import FastAPI

app = FastAPI()

try:
    import p_vs_np
except Exception as e:
    p_vs_np = None
    IMPORT_ERROR = str(e)

def build_registry():
    reg = {}
    if p_vs_np is None:
        return reg
    for name, obj in inspect.getmembers(p_vs_np):
        if callable(obj) and not name.startswith("_"):
            reg[name] = obj
    return reg

REGISTRY = build_registry()

@app.get("/api/functions")
def functions():
    return {"count": len(REGISTRY), "functions": sorted(REGISTRY.keys())}