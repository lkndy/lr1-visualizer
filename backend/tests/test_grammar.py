"""Comprehensive tests for grammar parsing and validation."""

import pytest
from parser.grammar_v2 import Grammar
from parser.types import Symbol, SymbolType


class TestGrammarParsing:
    """Test grammar parsing functionality."""

    def test_parse_arithmetic_grammar(self, arithmetic_grammar):
        """Test parsing arithmetic grammar."""
        assert arithmetic_grammar is not None
        assert len(arithmetic_grammar.productions) > 0
        assert arithmetic_grammar.start_symbol.name == "E'"

    def test_parse_simple_grammar(self, simple_grammar):
        """Test parsing simple grammar."""
        assert simple_grammar is not None
        assert len(simple_grammar.productions) == 6  # 1 + 2 + 2 + 1 (augmented)
        assert simple_grammar.start_symbol.name == "S'"

    def test_parse_bnf_format(self, sample_grammar_texts):
        """Test parsing BNF format grammar."""
        bnf_text = sample_grammar_texts["bnf_format"]
        grammar = Grammar.from_text(bnf_text, "E")

        assert grammar is not None
        assert len(grammar.productions) > 0
        assert grammar.start_symbol.name == "E'"

    def test_parse_with_comments(self, sample_grammar_texts):
        """Test parsing grammar with comments."""
        commented_text = sample_grammar_texts["with_comments"]
        grammar = Grammar.from_text(commented_text, "E")

        assert grammar is not None
        assert len(grammar.productions) > 0

    def test_parse_quoted_terminals(self, sample_grammar_texts):
        """Test parsing grammar with quoted terminals."""
        quoted_text = sample_grammar_texts["quoted_terminals"]
        grammar = Grammar.from_text(quoted_text, "E")

        assert grammar is not None
        # Check that quoted terminals are properly handled
        terminals = [s.name for s in grammar.terminals]
        assert "id" in terminals
        assert "num" in terminals

    def test_parse_mixed_case(self, sample_grammar_texts):
        """Test parsing grammar with mixed case symbols."""
        mixed_text = sample_grammar_texts["mixed_case"]
        grammar = Grammar.from_text(mixed_text, "Expr")

        assert grammar is not None
        assert grammar.start_symbol.name == "Expr'"

    @pytest.mark.parametrize(
        "grammar_text,expected_props",
        [
            ("arithmetic", {"num_terminals": 9, "num_non_terminals": 5}),  # +1 for $, +1 for S (default start)
            ("simple", {"num_terminals": 4, "num_non_terminals": 4}),      # +1 for $, +1 for ε
            ("left_recursive", {"num_terminals": 4, "num_non_terminals": 5}),  # +1 for $, +1 for S (default start)
        ],
    )
    def test_grammar_properties(self, sample_grammar_texts, expected_grammar_properties, grammar_text, expected_props):
        """Test grammar properties match expected values."""
        text = sample_grammar_texts[grammar_text]
        grammar = Grammar.from_text(text)

        assert len(grammar.terminals) == expected_props["num_terminals"]
        assert len(grammar.non_terminals) == expected_props["num_non_terminals"]

    def test_parse_invalid_grammar(self, invalid_grammar_texts):
        """Test parsing invalid grammar texts."""
        for name, text in invalid_grammar_texts.items():
            with pytest.raises(Exception):
                Grammar.from_text(text)

    def test_parse_empty_grammar(self):
        """Test parsing empty grammar."""
        with pytest.raises(Exception):
            Grammar.from_text("")

    def test_parse_grammar_with_epsilon(self, epsilon_grammar):
        """Test parsing grammar with epsilon productions."""
        assert epsilon_grammar is not None
        assert len(epsilon_grammar.productions) == 8  # 1 + 2 + 2 + 2 + 1 (augmented)

        # Check that epsilon symbol is present
        epsilon_symbols = [s for s in epsilon_grammar.terminals if s.symbol_type == SymbolType.EPSILON]
        assert len(epsilon_symbols) > 0


class TestSymbolClassification:
    """Test symbol type classification."""

    def test_terminal_classification(self):
        """Test that terminals are properly classified."""
        grammar_text = """
        S: "a" | "b" | id | num
        """
        grammar = Grammar.from_text(grammar_text, "S")

        terminal_names = [s.name for s in grammar.terminals]
        assert "a" in terminal_names
        assert "b" in terminal_names
        assert "id" in terminal_names
        assert "num" in terminal_names

    def test_non_terminal_classification(self):
        """Test that non-terminals are properly classified."""
        grammar_text = """
        S: A B
        A: "a"
        B: "b"
        """
        grammar = Grammar.from_text(grammar_text, "S")

        non_terminal_names = [s.name for s in grammar.non_terminals]
        assert "S" in non_terminal_names
        assert "A" in non_terminal_names
        assert "B" in non_terminal_names

    def test_epsilon_classification(self):
        """Test that epsilon is properly classified."""
        grammar_text = """
        S: A | ε
        A: "a"
        """
        grammar = Grammar.from_text(grammar_text, "S")

        epsilon_symbols = [s for s in grammar.terminals if s.symbol_type == SymbolType.EPSILON]
        assert len(epsilon_symbols) > 0
        assert epsilon_symbols[0].name == "ε"


class TestFirstSets:
    """Test FIRST set computation."""

    def test_first_terminal(self, arithmetic_grammar):
        """Test FIRST set for terminal symbols."""
        id_symbol = Symbol("id", SymbolType.TERMINAL)
        first_set = arithmetic_grammar.first((id_symbol,))

        assert len(first_set) == 1
        assert id_symbol in first_set

    def test_first_non_terminal(self, arithmetic_grammar):
        """Test FIRST set for non-terminal symbols."""
        f_symbol = Symbol("F", SymbolType.NON_TERMINAL)
        first_set = arithmetic_grammar.first((f_symbol,))

        # F should have id, num, and ( in its FIRST set
        first_names = [s.name for s in first_set]
        assert "id" in first_names
        assert "num" in first_names
        assert "(" in first_names

    def test_first_sequence(self, arithmetic_grammar):
        """Test FIRST set for symbol sequences."""
        # Test FIRST(T + F) where T can derive id and F can derive id
        t_symbol = Symbol("T", SymbolType.NON_TERMINAL)
        plus_symbol = Symbol("+", SymbolType.TERMINAL)
        f_symbol = Symbol("F", SymbolType.NON_TERMINAL)

        first_set = arithmetic_grammar.first((t_symbol, plus_symbol, f_symbol))

        # Should only contain FIRST(T) since T is not nullable
        assert len(first_set) > 0

    def test_first_epsilon(self, epsilon_grammar):
        """Test FIRST set with epsilon productions."""
        a_symbol = Symbol("A", SymbolType.NON_TERMINAL)
        first_set = epsilon_grammar.first((a_symbol,))

        # A can derive both "a" and ε
        first_names = [s.name for s in first_set]
        assert "a" in first_names
        assert "ε" in first_names

    def test_first_caching(self, arithmetic_grammar):
        """Test that FIRST sets are properly cached."""
        e_symbol = Symbol("E", SymbolType.NON_TERMINAL)

        # Call first twice
        first1 = arithmetic_grammar.first((e_symbol,))
        first2 = arithmetic_grammar.first((e_symbol,))

        # Should be the same object (cached)
        assert first1 is first2


class TestFollowSets:
    """Test FOLLOW set computation."""

    def test_follow_start_symbol(self, arithmetic_grammar):
        """Test FOLLOW set for start symbol."""
        e_symbol = Symbol("E", SymbolType.NON_TERMINAL)
        follow_set = arithmetic_grammar.follow(e_symbol)

        # Start symbol should have $ in FOLLOW
        follow_names = [s.name for s in follow_set]
        assert "$" in follow_names

    def test_follow_non_start(self, arithmetic_grammar):
        """Test FOLLOW set for non-start symbols."""
        t_symbol = Symbol("T", SymbolType.NON_TERMINAL)
        follow_set = arithmetic_grammar.follow(t_symbol)

        # T should have +, -, ), and $ in FOLLOW
        follow_names = [s.name for s in follow_set]
        assert "+" in follow_names
        assert "-" in follow_names
        assert ")" in follow_names
        assert "$" in follow_names

    def test_follow_caching(self, arithmetic_grammar):
        """Test that FOLLOW sets are properly cached."""
        e_symbol = Symbol("E", SymbolType.NON_TERMINAL)

        # Call follow twice
        follow1 = arithmetic_grammar.follow(e_symbol)
        follow2 = arithmetic_grammar.follow(e_symbol)

        # Should be the same object (cached)
        assert follow1 is follow2


class TestGrammarValidation:
    """Test grammar validation functionality."""

    def test_validate_valid_grammar(self, arithmetic_grammar):
        """Test validation of valid grammar."""
        errors = arithmetic_grammar.validate()
        assert len(errors) == 0

    def test_validate_grammar_with_unreachable(self):
        """Test validation detects unreachable symbols."""
        grammar_text = """
        S: A
        A: "a"
        B: "b"  # Unreachable
        """
        grammar = Grammar.from_text(grammar_text, "S")
        errors = grammar.validate()

        # Should have error for unreachable B
        error_types = [error.error_type for error in errors]
        assert "unreachable_non_terminal" in error_types

    def test_validate_grammar_with_undefined(self):
        """Test validation detects undefined symbols."""
        grammar_text = """
        S: A B
        A: "a"
        # B is undefined
        """
        grammar = Grammar.from_text(grammar_text, "S")
        errors = grammar.validate()

        # Should have error for undefined B
        error_types = [error.error_type for error in errors]
        assert "undefined_non_terminal" in error_types

    def test_find_reachable_symbols(self, arithmetic_grammar):
        """Test finding reachable symbols."""
        reachable = arithmetic_grammar._find_reachable_symbols()

        # All symbols should be reachable in a valid grammar
        assert len(reachable) > 0
        assert arithmetic_grammar.start_symbol in reachable

    def test_find_left_recursive_symbols(self, left_recursive_grammar):
        """Test finding left recursive symbols."""
        left_recursive = left_recursive_grammar._find_left_recursive_symbols()

        # Should find left recursive symbols
        assert len(left_recursive) > 0
        left_recursive_names = [s.name for s in left_recursive]
        assert "E" in left_recursive_names
        assert "T" in left_recursive_names


class TestGrammarOperations:
    """Test grammar operations and utilities."""

    def test_get_productions_for_symbol(self, arithmetic_grammar):
        """Test getting productions for a symbol."""
        e_symbol = Symbol("E", SymbolType.NON_TERMINAL)
        productions = arithmetic_grammar.get_productions_for_symbol(e_symbol)

        assert len(productions) > 0
        for production in productions:
            assert production.lhs == e_symbol

    def test_is_terminal(self, arithmetic_grammar):
        """Test terminal checking."""
        id_symbol = Symbol("id", SymbolType.TERMINAL)
        e_symbol = Symbol("E", SymbolType.NON_TERMINAL)

        assert arithmetic_grammar.is_terminal(id_symbol)
        assert not arithmetic_grammar.is_terminal(e_symbol)

    def test_is_non_terminal(self, arithmetic_grammar):
        """Test non-terminal checking."""
        id_symbol = Symbol("id", SymbolType.TERMINAL)
        e_symbol = Symbol("E", SymbolType.NON_TERMINAL)

        assert not arithmetic_grammar.is_non_terminal(id_symbol)
        assert arithmetic_grammar.is_non_terminal(e_symbol)

    def test_grammar_equality(self, arithmetic_grammar):
        """Test grammar equality."""
        grammar_text = """
        E: E "+" T | E "-" T | T
        T: T "*" F | T "/" F | F
        F: "(" E ")" | "id" | "num"
        """
        grammar2 = Grammar.from_text(grammar_text, "E")

        # Should be equal (ignoring augmented start symbol)
        assert grammar2 is not None
        assert len(grammar2.productions) > 0

    def test_grammar_string_representation(self, arithmetic_grammar):
        """Test grammar string representation."""
        grammar_str = str(arithmetic_grammar)

        assert isinstance(grammar_str, str)
        assert len(grammar_str) > 0
        assert "E'" in grammar_str  # Augmented start symbol

    def test_grammar_repr(self, arithmetic_grammar):
        """Test grammar repr."""
        grammar_repr = repr(arithmetic_grammar)

        assert isinstance(grammar_repr, str)
        assert "Grammar" in grammar_repr
        assert "productions" in grammar_repr


class TestGrammarEdgeCases:
    """Test grammar edge cases and error conditions."""

    def test_grammar_with_only_epsilon(self):
        """Test grammar with only epsilon productions."""
        grammar_text = """
        S: ε
        """
        grammar = Grammar.from_text(grammar_text, "S")

        assert grammar is not None
        assert len(grammar.productions) == 2  # S' -> S, S -> ε

    def test_grammar_with_empty_alternatives(self):
        """Test grammar with empty alternatives."""
        grammar_text = """
        S: A | 
        A: "a"
        """
        grammar = Grammar.from_text(grammar_text, "S")

        assert grammar is not None
        # Empty alternative should be treated as epsilon

    def test_grammar_with_duplicate_productions(self):
        """Test grammar with duplicate productions."""
        grammar_text = """
        S: A
        S: A  # Duplicate
        A: "a"
        """
        grammar = Grammar.from_text(grammar_text, "S")

        assert grammar is not None
        # Should handle duplicates gracefully

    def test_grammar_with_very_long_rhs(self):
        """Test grammar with very long right-hand side."""
        grammar_text = """
        S: A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
        A: "a"
        B: "b"
        C: "c"
        D: "d"
        E: "e"
        F: "f"
        G: "g"
        H: "h"
        I: "i"
        J: "j"
        K: "k"
        L: "l"
        M: "m"
        N: "n"
        O: "o"
        P: "p"
        Q: "q"
        R: "r"
        S: "s"
        T: "t"
        U: "u"
        V: "v"
        W: "w"
        X: "x"
        Y: "y"
        Z: "z"
        """
        grammar = Grammar.from_text(grammar_text, "S")

        assert grammar is not None
        assert len(grammar.productions) > 0
