"""Mathematical expression grammars for testing."""

# Boolean algebra
BOOLEAN_GRAMMAR = """
expr: expr "||" term | term
term: term "&&" factor | factor
factor: "!" factor | "(" expr ")" | "true" | "false" | "id"
"""

# Set theory
SET_GRAMMAR = """
expr: expr "∪" term | expr "∩" term | term
term: term "\\" factor | factor
factor: "(" expr ")" | "{" elements "}" | "id"
elements: element elements_tail | ε
elements_tail: "," element elements_tail | ε
element: "id" | "num"
"""

# Logic formulas
LOGIC_GRAMMAR = """
formula: formula "∨" term | term
term: term "∧" factor | factor
factor: "¬" factor | "(" formula ")" | "id" | "true" | "false"
"""

# Calculus expressions
CALCULUS_GRAMMAR = """
expr: expr "+" term | expr "-" term | term
term: term "*" factor | term "/" factor | factor
factor: "d/dx" factor | "∫" factor "dx" | "(" expr ")" | "id" | "num"
"""

# Matrix operations
MATRIX_GRAMMAR = """
expr: expr "+" term | expr "-" term | term
term: term "*" factor | factor
factor: "[" rows "]" | "(" expr ")" | "id" | "num"
rows: row rows_tail
rows_tail: ";" row rows_tail | ε
row: element row_tail
row_tail: "," element row_tail | ε
element: "id" | "num"
"""
