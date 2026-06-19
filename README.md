# P vs NP Discovery GUI

This project discovers the installed `p-vs-np` package and builds a GUI from the discovered inventory.

## 1. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Discover the package

```bash
python scripts/discover_p_vs_np.py
```

This creates:

```text
inventory/
├── summary.json
├── modules.json
├── functions.json
├── classes.json
└── capabilities.json
```

## 3. Run the GUI

```bash
uvicorn backend.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## What this version does

- Imports the installed package.
- Walks submodules.
- Extracts modules, functions, classes, signatures, and docstrings.
- Infers rough categories and visualizer types.
- Builds a universal capability dashboard.
- Runs selected functions/classes with JSON arguments.
- Performs a no-argument smoke test batch.

## Important

This version does not assume the package API. It discovers the real structure first.
If the import name is not `p_vs_np`, edit `PACKAGE_CANDIDATES` in:

```text
scripts/discover_p_vs_np.py
```