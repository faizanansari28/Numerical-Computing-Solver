"""Turns the raw dictionary returned by a method into the final API result."""
import math

import numpy as np

from utils.plotting import render


def to_plain(obj):
    """Make NumPy values JSON friendly (NaN/inf -> None)."""
    if isinstance(obj, dict):
        return {k: to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_plain(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return to_plain(obj.tolist())
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return v if math.isfinite(v) else None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def answer(label, value):
    return {"label": label, "value": value}


def finish(raw, reference=None, plot=True):
    """raw = dict from a method; reference = {"label", "value", "exact": bool} or None."""
    primary = raw["answers"][0]["value"]
    analysis = {
        "reference_label": None, "reference_value": None, "reference_is_exact": False,
        "absolute_error": None, "relative_error": None,
        "iterations": raw.get("iterations"), "converged": raw.get("converged"),
        "metrics": raw.get("metrics", []), "notes": raw.get("notes", []),
    }
    if reference is not None and reference.get("value") is not None and not isinstance(primary, str):
        a = np.array(primary, dtype=float)
        r = np.array(reference["value"], dtype=float)
        abs_err = float(np.linalg.norm((a - r).ravel()))
        norm_r = float(np.linalg.norm(r.ravel()))
        analysis.update(
            reference_label=reference["label"], reference_value=reference["value"],
            reference_is_exact=bool(reference.get("exact")),
            absolute_error=abs_err, relative_error=(abs_err / norm_r) if norm_r > 1e-300 else None,
        )
    converged = raw.get("converged")
    if converged is False:
        status = {"state": "warning", "message": raw.get("status_message", "Stopped before reaching the tolerance.")}
    else:
        status = {"state": "success", "message": raw.get("status_message", "Computation finished successfully.")}
    tables = raw.get("tables")
    if tables is None:
        tables = [{"title": raw.get("table_title", "Iteration table"), "columns": raw.get("columns", []), "rows": raw.get("rows", [])}]
    for t in tables:                            # keep the page fast: show first 60 and last 60 rows of very long tables
        if len(t["rows"]) > 120:
            t["total_rows"] = len(t["rows"])
            t["rows"] = t["rows"][:60] + t["rows"][-60:]
            t["truncated_at"] = 60
    return to_plain({
        "answers": raw["answers"], "steps": raw.get("steps", []), "tables": tables,
        "error_analysis": analysis, "status": status,
        "plot": render(raw.get("plot")) if plot else None,
        "extra": raw.get("extra", {}),
    })
