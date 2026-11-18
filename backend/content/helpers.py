def entry(what, why, solves, uses, explain, formula, variables, why_works, code, adv, lim, related, example_intro, exact=None, example=None):
    """One learning page. `code` is a runnable beginner script; text after '#' on a line explains that line."""
    return {
        "intro": {"what": what, "why": why, "solves": solves, "uses": uses},
        "foundation": {"explain": explain, "formula": formula, "variables": variables, "why": why_works},
        "code": code.strip("\n"),
        "advantages": adv, "limitations": lim, "related": related,
        "example_intro": example_intro, "exact": exact, "example": example or {},
    }
