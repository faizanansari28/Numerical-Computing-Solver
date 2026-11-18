"""NUMERIQ backend (Flask).  Run:  python app.py   ->  http://localhost:5000"""
import logging
import os
import time

import numpy as np
from flask import Flask, jsonify, request, send_from_directory

import challenges
import registry
from content import get_learning_content
from utils.errors import NumericalError
from utils.results import finish, to_plain  # noqa: F401  (finish is used by adapters)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024            # requests are tiny; refuse anything big
logging.basicConfig(level=logging.INFO)
LEARN_CACHE = {}


@app.after_request
def add_cors(resp):                                       # lets the React dev server call the API directly
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


@app.errorhandler(NumericalError)
def numerical_error(e):
    return jsonify({"ok": False, "error": str(e)}), 400


@app.errorhandler(np.linalg.LinAlgError)
def linalg_error(e):
    return jsonify({"ok": False, "error": "The matrix is singular, so this computation is not possible."}), 400


@app.errorhandler(ZeroDivisionError)
def zero_division(e):
    return jsonify({"ok": False, "error": "Division by zero happened during the calculation. Check your inputs (for example a zero pivot or zero derivative)."}), 400


@app.errorhandler(OverflowError)
def overflow(e):
    return jsonify({"ok": False, "error": "A number became too large to handle. Try smaller inputs or a smaller step size."}), 400


@app.errorhandler(Exception)
def unexpected(e):
    if hasattr(e, "code") and isinstance(e.code, int):    # normal HTTP errors (404, 413 ...)
        return jsonify({"ok": False, "error": e.description}), e.code
    logging.exception("Unexpected error")
    return jsonify({"ok": False, "error": "Something unexpected went wrong while computing. Please check your inputs."}), 500


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "methods": len(registry.METHODS)})


@app.get("/api/catalog")
def catalog():
    return jsonify(to_plain(registry.catalog()))


def _solve(method_id, params):
    if method_id not in registry.METHODS:
        raise NumericalError("Unknown method.")
    spec = registry.METHODS[method_id]
    start = time.perf_counter()
    result = spec["run"](params)
    result.update(ok=True, method=method_id, title=spec["name"], category=spec["category"], formula=spec["formula"],
                  time_ms=round((time.perf_counter() - start) * 1000, 2))
    return result


@app.post("/api/solve")
def solve():
    data = request.get_json(silent=True) or {}
    params = data.get("params") or {}
    if not isinstance(params, dict):
        raise NumericalError("Invalid request.")
    return jsonify(_solve(data.get("method", ""), params))


@app.get("/api/learn/<method_id>")
def learn(method_id):
    if method_id not in registry.METHODS:
        return jsonify({"ok": False, "error": "Unknown method."}), 404
    if method_id not in LEARN_CACHE:
        spec = registry.METHODS[method_id]
        content = get_learning_content(method_id)
        params = registry.defaults(method_id)
        params.update(content.get("example", {}))
        result = _solve(method_id, params)
        exact = content.get("exact")
        if exact:                                   # compare with the known analytic answer
            a = np.array(result["answers"][0]["value"], float)
            e = np.array(exact["value"], float)
            err = float(np.linalg.norm((a - e).ravel()))
            norm = float(np.linalg.norm(e.ravel()))
            result["exact_answer"] = to_plain({"label": exact["label"], "value": exact["value"], "absolute_error": err,
                                               "relative_error": err / norm if norm > 1e-300 else None})
        LEARN_CACHE[method_id] = {"ok": True, "id": method_id, "name": spec["name"], "category": spec["category"], "formula": spec["formula"],
                                  "content": content, "example_params": params, "inputs": spec["inputs"], "result": result}
    return jsonify(LEARN_CACHE[method_id])


@app.get("/api/challenges")
def challenge_list():
    return jsonify(to_plain({"ok": True, "challenges": challenges.public_definitions()}))


@app.post("/api/challenge/<cid>")
def challenge_run(cid):
    data = request.get_json(silent=True) or {}
    out = challenges.run_challenge(cid, data.get("methods") or [], data.get("knobs") or {})
    out["ok"] = True
    return jsonify(out)


# Optional single-command mode: after "npm run build", Flask also serves the website itself.
DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")


@app.get("/", defaults={"path": ""})
@app.get("/<path:path>")
def website(path):
    if path.startswith("api/") or not os.path.isdir(DIST):
        return jsonify({"ok": False, "error": "Not found. (Build the frontend with 'npm run build' to serve it from here.)"}), 404
    full = os.path.join(DIST, path)
    if path and os.path.isfile(full):
        return send_from_directory(DIST, path)
    return send_from_directory(DIST, "index.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
