"""Business logic kept separate from the web layer so it is easy to test."""


def add(a: int, b: int) -> int:
    return a + b


def divide(a: int, b: int) -> float:
    if b == 0:
        raise ValueError("division by zero")
    return a / b
