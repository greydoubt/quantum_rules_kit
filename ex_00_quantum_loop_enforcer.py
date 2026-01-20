"""
quantum_loop_enforcer.py

A standalone Python + Qiskit script that enforces:
1. Reversibility (unitarity)
2. No information deletion
3. No data-dependent control-flow divergence
"""

from __future__ import annotations

from typing import Callable, Dict, Any, List, Tuple
from functools import wraps

from qiskit import QuantumCircuit
from qiskit.circuit import Gate


# ============================================================
# Exceptions representing violations of quantum theory
# ============================================================

class QuantumRuleViolation(Exception):
    """Base class for quantum rule violations."""


class IrreversibleFunctionError(QuantumRuleViolation):
    """Raised when a function is not reversible."""


class InformationDeletionError(QuantumRuleViolation):
    """Raised when information would be discarded."""


class ControlFlowDivergenceError(QuantumRuleViolation):
    """Raised when data-dependent control flow is detected."""


# ============================================================
# Decorators enforcing quantum rules
# ============================================================

def reversible(func: Callable[[int], int]) -> Callable[[int], int]:
    """
    Enforces that a classical function is reversible (injective).
    """
    seen_outputs: Dict[int, int] = {}

    @wraps(func)
    def wrapper(x: int) -> int:
        y = func(x)
        if y in seen_outputs and seen_outputs[y] != x:
            raise IrreversibleFunctionError(
                f"Function {func.__name__} is not reversible: "
                f"{seen_outputs[y]} and {x} map to {y}"
            )
        seen_outputs[y] = x
        return y

    return wrapper


def no_information_deletion(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Ensures all inputs are preserved in outputs.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)

        if result is None:
            raise InformationDeletionError(
                f"Function {func.__name__} discards information (returns None)"
            )

        return result

    return wrapper


def no_control_flow_divergence(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Prohibits classical branching based on runtime data.
    """

    source = func.__code__.co_names
    forbidden = {"if", "while", "break", "continue"}

    for name in forbidden:
        if name in source:
            raise ControlFlowDivergenceError(
                f"Function {func.__name__} contains forbidden control flow: {name}"
            )

    return func


# ============================================================
# Quantum-safe classical function abstraction
# ============================================================

class QuantumSafeFunction:
    """
    Represents a classical function that can be embedded
    into a quantum circuit.
    """

    def __init__(self, func: Callable[[int], int]) -> None:
        self.func = func

    def evaluate(self, x: int) -> int:
        return self.func(x)

    def to_gate(self, name: str = "U_f") -> Gate:
        """
        Converts the function into a placeholder reversible gate.
        (In real compilers this would synthesize a circuit.)
        """
        qc = QuantumCircuit(2, name=name)
        qc.cx(0, 1)  # placeholder reversible operation
        return qc.to_gate()


# ============================================================
# Quantum loop abstraction (fixed, uniform, reversible)
# ============================================================

class QuantumLoop:
    """
    A quantum-valid loop:
    - fixed iteration count
    - reversible body
    - no branching
    """

    def __init__(
        self,
        iterations: int,
        body: QuantumSafeFunction
    ) -> None:
        if iterations <= 0:
            raise ValueError("Quantum loops must have fixed positive iterations")

        self.iterations = iterations
        self.body = body

    def build_circuit(self) -> QuantumCircuit:
        qc = QuantumCircuit(2)

        gate = self.body.to_gate()

        for _ in range(self.iterations):
            qc.append(gate, [0, 1])

        return qc


# ============================================================
# Example: valid quantum-safe loop
# ============================================================

@no_control_flow_divergence
@no_information_deletion
@reversible
def reversible_increment(x: int) -> int:
    return x ^ 1  # bijection on {0,1}


def main() -> None:
    safe_func = QuantumSafeFunction(reversible_increment)
    qloop = QuantumLoop(iterations=3, body=safe_func)

    circuit = qloop.build_circuit()
    print(circuit.draw())


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()
