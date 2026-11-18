"""Custom error type used everywhere in NUMERIQ.

Whenever the user gives bad input (wrong interval, singular matrix, ...)
we raise NumericalError with a friendly message. The API turns it into
a clean error response instead of crashing.
"""


class NumericalError(Exception):
    pass
