"""Safe arithmetic calculator for BORO BHAI."""

from __future__ import annotations

import ast
import operator

_ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _to_number(value):
    if isinstance(value, bool):
        raise ValueError("Boolean values are not allowed in arithmetic expressions.")
    if not isinstance(value, (int, float)):
        raise ValueError(f"Unsupported value type: {type(value).__name__}")
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _evaluate(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise ValueError("Boolean values are not allowed in arithmetic expressions.")
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"Unsupported constant: {node.value!r}")
        return _to_number(node.value)

    if isinstance(node, ast.BinOp):
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        op_type = type(node.op)
        if op_type not in _ALLOWED_BIN_OPS:
            raise ValueError(f"Operator not allowed: {type(node.op).__name__}")
        return _ALLOWED_BIN_OPS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        operand = _evaluate(node.operand)
        op_type = type(node.op)
        if op_type not in _ALLOWED_UNARY_OPS:
            raise ValueError(f"Unary operator not allowed: {type(node.op).__name__}")
        return _ALLOWED_UNARY_OPS[op_type](operand)

    if isinstance(node, ast.Expression):
        return _evaluate(node.body)

    if isinstance(node, ast.Call):
        raise ValueError("Function calls are not allowed in calculator expressions.")

    if isinstance(node, ast.Name):
        raise ValueError(f"Variable names are not allowed: {node.id}")

    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def calculate(expression: str):
    """Safely evaluate a small arithmetic expression.

    Supported operations:
    +, -, *, /, %, **, parentheses, and numeric constants.
    """
    if expression is None or not str(expression).strip():
        raise ValueError("Expression cannot be empty.")

    cleaned = str(expression).strip()
    if any(ch.isalpha() for ch in cleaned):
        raise ValueError("Only numeric expressions are allowed.")

    try:
        parsed = ast.parse(cleaned, mode="eval")
        result = _evaluate(parsed)
    except SyntaxError as exc:
        raise ValueError(f"Invalid arithmetic expression: {expression}") from exc
    except ZeroDivisionError as exc:
        raise ValueError("Division by zero is not allowed.") from exc
    except ValueError:
        raise
    except Exception as exc:  # pragma: no cover - broad fail-safe for unexpected AST cases
        raise ValueError(f"Unable to evaluate expression: {expression}") from exc

    return _to_number(result)
