def normalize_exercise_name(name: str) -> str:
    """Return the canonical value used for exact exercise-name matching."""

    return name.strip().lower()
