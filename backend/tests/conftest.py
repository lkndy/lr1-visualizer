"""Pytest configuration and fixtures for the LR(1) Parser Visualizer tests."""

import pytest
from parser.grammar_v2 import Grammar
from parser.types import Production, Symbol, SymbolType


@pytest.fixture
def arithmetic_grammar():
    """Arithmetic expressions grammar for testing."""
    grammar_text = """
    E: E "+" T | E "-" T | T
    T: T "*" F | T "/" F | F  
    F: "(" E ")" | "id" | "num"
    """
    return Grammar.from_text(grammar_text, "E")


@pytest.fixture
def simple_grammar():
    """Simple grammar for basic testing."""
    grammar_text = """
    S: A B
    A: "a" | ε
    B: "b" | ε
    """
    return Grammar.from_text(grammar_text, "S")


@pytest.fixture
def left_recursive_grammar():
    """Grammar with left recursion for testing."""
    grammar_text = """
    E: E "+" T | T
    T: T "*" F | F
    F: "id"
    """
    return Grammar.from_text(grammar_text, "E")


@pytest.fixture
def ambiguous_grammar():
    """Ambiguous grammar for conflict testing."""
    grammar_text = """
    S: S S | "a"
    """
    return Grammar.from_text(grammar_text, "S")


@pytest.fixture
def epsilon_grammar():
    """Grammar with epsilon productions for testing."""
    grammar_text = """
    S: A B C
    A: "a" | ε
    B: "b" | ε  
    C: "c" | ε
    """
    return Grammar.from_text(grammar_text, "S")


@pytest.fixture
def complex_grammar():
    """Complex grammar with multiple non-terminals."""
    grammar_text = """
    program: stmt_list
    stmt_list: stmt stmt_list | stmt
    stmt: "if" expr "then" stmt | "while" expr "do" stmt | expr
    expr: expr "+" term | expr "-" term | term
    term: term "*" factor | term "/" factor | factor
    factor: "id" | "num" | "(" expr ")"
    """
    return Grammar.from_text(grammar_text, "program")


@pytest.fixture
def json_like_grammar():
    """JSON-like grammar for testing."""
    grammar_text = """
    value: object | array | string | number | "true" | "false" | "null"
    object: "{" pairs "}"
    pairs: pair pairs_tail | ε
    pairs_tail: "," pair pairs_tail | ε
    pair: string ":" value
    array: "[" elements "]"
    elements: value elements_tail | ε
    elements_tail: "," value elements_tail | ε
    string: "\"" string_content "\""
    string_content: string_char string_content | ε
    string_char: /[^"\\]/
    number: /[0-9]+/
    """
    return Grammar.from_text(grammar_text, "value")


@pytest.fixture
def symbol_a():
    """Symbol 'a' for testing."""
    return Symbol("a", SymbolType.TERMINAL)


@pytest.fixture
def symbol_b():
    """Symbol 'b' for testing."""
    return Symbol("b", SymbolType.TERMINAL)


@pytest.fixture
def symbol_s():
    """Non-terminal symbol 'S' for testing."""
    return Symbol("S", SymbolType.NON_TERMINAL)


@pytest.fixture
def symbol_epsilon():
    """Epsilon symbol for testing."""
    return Symbol("ε", SymbolType.EPSILON)


@pytest.fixture
def production_s_to_ab(symbol_s, symbol_a, symbol_b):
    """Production S -> A B for testing."""
    return Production(symbol_s, [symbol_a, symbol_b])


@pytest.fixture
def production_s_to_epsilon(symbol_s, symbol_epsilon):
    """Production S -> ε for testing."""
    return Production(symbol_s, [])


@pytest.fixture
def sample_grammar_texts():
    """Collection of sample grammar texts for parametrized testing."""
    return {
        "arithmetic": """
        E: E "+" T | E "-" T | T
        T: T "*" F | T "/" F | F
        F: "(" E ")" | "id" | "num"
        """,
        "simple": """
        S: A B
        A: "a" | ε
        B: "b" | ε
        """,
        "left_recursive": """
        E: E "+" T | T
        T: T "*" F | F
        F: "id"
        """,
        "ambiguous": """
        S: S S | "a"
        """,
        "epsilon": """
        S: A B C
        A: "a" | ε
        B: "b" | ε
        C: "c" | ε
        """,
        "bnf_format": """
        E -> E + T | E - T | T
        T -> T * F | T / F | F
        F -> ( E ) | id | num
        """,
        "with_comments": """
        # Arithmetic expressions
        E: E "+" T | E "-" T | T  # Expression
        T: T "*" F | T "/" F | F  # Term
        F: "(" E ")" | "id" | "num"  # Factor
        """,
        "quoted_terminals": """
        E: E "+" T | E "-" T | T
        T: T "*" F | T "/" F | F
        F: "(" E ")" | "id" | "num"
        """,
        "mixed_case": """
        Expr: Expr "+" Term | Expr "-" Term | Term
        Term: Term "*" Factor | Term "/" Factor | Factor
        Factor: "(" Expr ")" | "id" | "num"
        """,
        "operators": """
        E: E "+" E | E "-" E | E "*" E | E "/" E | "(" E ")" | "id" | "num"
        """,
    }


@pytest.fixture
def expected_grammar_properties():
    """Expected properties for sample grammars."""
    return {
        "arithmetic": {
            "num_terminals": 7,  # +, -, *, /, (, ), id, num
            "num_non_terminals": 3,  # E, T, F
            "num_productions": 8,  # 3 + 3 + 3 - 1 (augmented)
            "has_left_recursion": True,
            "is_lr1": True,
        },
        "simple": {
            "num_terminals": 2,  # a, b
            "num_non_terminals": 3,  # S, A, B
            "num_productions": 5,  # 1 + 2 + 2
            "has_left_recursion": False,
            "is_lr1": True,
        },
        "left_recursive": {
            "num_terminals": 1,  # id
            "num_non_terminals": 3,  # E, T, F
            "num_productions": 5,  # 2 + 2 + 1
            "has_left_recursion": True,
            "is_lr1": True,
        },
        "ambiguous": {
            "num_terminals": 1,  # a
            "num_non_terminals": 1,  # S
            "num_productions": 2,  # 1 + 1
            "has_left_recursion": True,
            "is_lr1": False,  # Ambiguous
        },
    }


@pytest.fixture
def sample_inputs():
    """Sample input strings for testing."""
    return {
        "arithmetic": ["id", "id + id", "id * id", "id + id * id", "( id + id ) * id", "id - id / id"],
        "simple": [
            "a b",
            "a",
            "b",
            "",  # Empty string (epsilon)
        ],
        "left_recursive": ["id", "id + id", "id * id", "id + id * id"],
    }


@pytest.fixture
def invalid_grammar_texts():
    """Invalid grammar texts for error testing."""
    return {
        "empty": "",
        "no_colon": "S A B",
        "invalid_symbol": "S: @#$",
        "unclosed_quotes": 'S: "a',
        "missing_lhs": ": A B",
    }


# Test data generators
def generate_grammar_variations(base_grammar_text: str) -> list:
    """Generate variations of a grammar for testing."""
    variations = [base_grammar_text]

    # Add BNF format
    bnf_version = base_grammar_text.replace(":", "->")
    variations.append(bnf_version)

    # Add with comments
    commented_version = base_grammar_text.replace("\n", "\n# Comment\n")
    variations.append(commented_version)

    return variations


def generate_test_cases(grammar_texts: dict, expected_properties: dict) -> list:
    """Generate test cases for parametrized testing."""
    test_cases = []

    for name, text in grammar_texts.items():
        if name in expected_properties:
            test_cases.append(pytest.param(text, expected_properties[name], id=name))

    return test_cases
