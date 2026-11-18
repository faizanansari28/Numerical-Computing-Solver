"""Learning content for every method (the 'Explore & Understand' page)."""
from content import arith, approx, diffode, integration, interp, linalg, optim, root

CONTENT = {}
for _m in (root, interp, integration, diffode, linalg, approx, optim, arith):
    CONTENT.update(_m.CONTENT)


def get_learning_content(method_id):
    return CONTENT[method_id]
