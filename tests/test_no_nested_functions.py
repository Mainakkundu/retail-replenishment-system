from __future__ import annotations

import ast
from pathlib import Path
from typing import Union

SOURCE_ROOT = Path("src")


def test_no_nested_functions_in_src() -> None:
    nested_functions = []
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        visitor = NestedFunctionVisitor(path)
        visitor.visit(tree)
        nested_functions.extend(visitor.nested_functions)

    assert nested_functions == []


class NestedFunctionVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.function_depth = 0
        self.nested_functions: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.record_function(node)
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.record_function(node)
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def record_function(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    ) -> None:
        if self.function_depth > 0:
            self.nested_functions.append(f"{self.path}:{node.lineno}:{node.name}")
