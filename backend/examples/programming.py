"""Programming language grammars for testing."""

# Simple C-like language
C_LIKE_GRAMMAR = """
program: stmt_list
stmt_list: stmt stmt_list | stmt
stmt: "if" "(" expr ")" stmt | "while" "(" expr ")" stmt | "{" stmt_list "}" | expr ";"
expr: expr "+" term | expr "-" term | term
term: term "*" factor | term "/" factor | factor
factor: "id" | "num" | "(" expr ")"
"""

# Python-like language
PYTHON_LIKE_GRAMMAR = """
program: stmt_list
stmt_list: stmt stmt_list | stmt
stmt: "if" expr ":" stmt | "while" expr ":" stmt | "def" "id" "(" ")" ":" stmt | expr
expr: expr "+" term | expr "-" term | term
term: term "*" factor | term "/" factor | factor
factor: "id" | "num" | "(" expr ")"
"""

# JavaScript-like language
JAVASCRIPT_LIKE_GRAMMAR = """
program: stmt_list
stmt_list: stmt stmt_list | stmt
stmt: "if" "(" expr ")" stmt | "while" "(" expr ")" stmt | "function" "id" "(" ")" "{" stmt_list "}" | expr ";"
expr: expr "+" term | expr "-" term | term
term: term "*" factor | term "/" factor | factor
factor: "id" | "num" | "(" expr ")"
"""

# Assembly-like language
ASSEMBLY_LIKE_GRAMMAR = """
program: instr_list
instr_list: instr instr_list | instr
instr: "mov" reg "," reg | "add" reg "," reg | "sub" reg "," reg | "jmp" label
reg: "r1" | "r2" | "r3" | "r4"
label: "id"
"""
