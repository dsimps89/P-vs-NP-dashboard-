# P vs NP Studio — Module Runner GUI

This version is built for the actual `p-vs-np` package structure.

It treats the 361 problem files as runnable scripts instead of normal importable functions.

## Why

The package contains categories like:

```text
database_problems: 203
flow_problems: 64
graph_theory: 65
network_design: 29
TOTAL: 361
```

Many files have names that are not clean Python import names, so this app runs by file path using:

```python
runpy.run_path(path, run_name="__main__")
```

inside a subprocess.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Discover modules

```bash
python scripts/discover_modules.py
```

## Run GUI

```bash
uvicorn backend.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Features

- Discovers all problem `.py` files.
- Groups them by category.
- Runs selected modules.
- Captures stdout/stderr/errors/runtime.
- Shows source code.
- Runs first 25 modules in a category.
- Avoids import-name problems by using file-path execution.

## Notes for Pyto

Pyto may support the discovery and module running scripts directly.
The FastAPI GUI may be easier on desktop or a Python web host.