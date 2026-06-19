from __future__ import annotations

import contextlib
import io
import json
import runpy
import sys
import traceback


def main():
    payload = json.loads(sys.stdin.read())
    path = payload["path"]

    stdout = io.StringIO()
    stderr = io.StringIO()

    result = {
        "ok": False,
        "stdout": "",
        "stderr": "",
        "error": None,
    }

    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            runpy.run_path(path, run_name="__main__")

        result["ok"] = True

    except Exception:
        result["error"] = traceback.format_exc(limit=8)

    result["stdout"] = stdout.getvalue()
    result["stderr"] = stderr.getvalue()

    print(json.dumps(result))


if __name__ == "__main__":
    main()