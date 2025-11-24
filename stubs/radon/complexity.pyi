"""Type stubs for radon.complexity module."""

from typing import Any

class ComplexityVisitor:
    """Visitor that calculates cyclomatic complexity."""

    complexity: int
    name: str
    lineno: int
    col_offset: int
    endline: int
    is_method: bool
    classname: str | None
    closures: list[ComplexityVisitor]

    def __init__(
        self,
        code: str,
        filename: str = ...,
    ) -> None: ...

def cc_visit(code: str, **kwargs: Any) -> list[ComplexityVisitor]:
    """Visit Python code and return complexity metrics."""
    ...

def cc_visit_ast(node: Any, **kwargs: Any) -> list[ComplexityVisitor]:
    """Visit AST node and return complexity metrics."""
    ...
