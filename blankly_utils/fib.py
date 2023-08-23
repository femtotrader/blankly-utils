PHI = (1 + 5**0.5) / 2  # Golden ratio.


def fib(n):
    return int((PHI**n - (1 - PHI) ** n) / 5**0.5)
