"""Parse the reviewed PDF notation: '/' is OR, whitespace between groups is AND.

Parentheses bind a group, e.g. '(A B)/C' becomes (A OR C) AND (B OR C).
Only course codes and this notation are accepted; unknown syntax must be reviewed.
"""

from __future__ import annotations

import re

CODE = r"[A-Z]{3}\d{4}[A-Z]?"


def expression_key(expression: list[list[str]]) -> tuple[tuple[str, ...], ...]:
    return tuple(sorted({tuple(sorted(set(clause))) for clause in expression}))


def parse_prerequisites(raw: str | None) -> list[list[str]]:
    if not raw or not raw.strip():
        return []
    value = re.sub(r"\s*/\s*", "/", raw.strip())
    value = re.sub(r"\(\s*", "(", value)
    value = re.sub(r"\s*\)", ")", value)
    value = re.sub(r"\s+", " ", value)
    tokens = re.findall(rf"{CODE}|[()/ ]", value)
    if "".join(tokens) != value:
        raise ValueError("Unsupported prerequisite expression")
    position = 0

    def atom() -> list[list[str]]:
        nonlocal position
        if position >= len(tokens):
            raise ValueError("Incomplete prerequisite expression")
        token = tokens[position]
        position += 1
        if token == "(":
            result = conjunction()
            if position >= len(tokens) or tokens[position] != ")":
                raise ValueError("Unclosed prerequisite parentheses")
            position += 1
            return result
        if not re.fullmatch(CODE, token):
            raise ValueError("Expected prerequisite course code")
        return [[token]]

    def alternatives() -> list[list[str]]:
        nonlocal position
        result = atom()
        while position < len(tokens) and tokens[position] == "/":
            position += 1
            right = atom()
            if len(result) * len(right) > 128:
                raise ValueError("Prerequisite expression requires manual review")
            result = [sorted(set(a + b)) for a in result for b in right]
        return result

    def conjunction() -> list[list[str]]:
        nonlocal position
        result = alternatives()
        while position < len(tokens) and tokens[position] == " ":
            position += 1
            result += alternatives()
        return result

    result = conjunction()
    if position != len(tokens):
        raise ValueError("Unexpected prerequisite token")
    # Preserve group order for stable database group numbers.
    return [list(clause) for clause in dict.fromkeys(tuple(sorted(c)) for c in result)]
