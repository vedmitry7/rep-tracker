def format_reps(reps: list[int]) -> str:
    if len(reps) == 1:
        return str(reps[0])
    if len(set(reps)) == 1:
        return f"{len(reps)} × {reps[0]}"
    return " • ".join(str(value) for value in reps)


def format_reps_total(reps: list[int]) -> str:
    return f"{format_reps(reps)} = {sum(reps)}"


def format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")
