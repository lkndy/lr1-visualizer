"""Arithmetic expression grammars for testing."""

# Simple arithmetic with operator precedence
ARITHMETIC_GRAMMAR = """
E: E "+" T | E "-" T | T
T: T "*" F | T "/" F | F
F: "(" E ")" | "id" | "num"
"""

# Arithmetic with unary operators
ARITHMETIC_UNARY_GRAMMAR = """
E: E "+" T | E "-" T | T
T: T "*" F | T "/" F | F
F: "+" F | "-" F | "(" E ")" | "id" | "num"
"""

# Arithmetic with exponentiation
ARITHMETIC_EXP_GRAMMAR = """
E: E "+" T | E "-" T | T
T: T "*" F | T "/" F | F
F: F "^" G | G
G: "(" E ")" | "id" | "num"
"""

# Arithmetic with function calls
ARITHMETIC_FUNCTIONS_GRAMMAR = """
E: E "+" T | E "-" T | T
T: T "*" F | T "/" F | F
F: "id" "(" E ")" | "(" E ")" | "id" | "num"
"""

# Arithmetic with array access
ARITHMETIC_ARRAYS_GRAMMAR = """
E: E "+" T | E "-" T | T
T: T "*" F | T "/" F | F
F: F "[" E "]" | "(" E ")" | "id" | "num"
"""
