import sys


def public(f):
    # Get list các public function và field của package
    _all = sys.modules[f.__module__].__dict__.setdefault("__all__", [])

    if f.__name__ not in _all:  # Prevent duplicates if run from an IDE.
        _all.append(f.__name__)
