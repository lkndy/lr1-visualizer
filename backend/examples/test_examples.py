"""Test all example grammars."""

import pytest
from parser.grammar_v2 import Grammar
from parser.automaton import Automaton
from parser.table import ParsingTable

# Import all example grammars
from . import arithmetic
from . import programming
from . import data_structures
from . import mathematical
from . import edge_cases


class TestExampleGrammars:
    """Test all example grammars for basic functionality."""

    @pytest.mark.parametrize(
        "grammar_name,grammar_text",
        [
            ("arithmetic", arithmetic.ARITHMETIC_GRAMMAR),
            ("arithmetic_unary", arithmetic.ARITHMETIC_UNARY_GRAMMAR),
            ("arithmetic_exp", arithmetic.ARITHMETIC_EXP_GRAMMAR),
            ("arithmetic_functions", arithmetic.ARITHMETIC_FUNCTIONS_GRAMMAR),
            ("arithmetic_arrays", arithmetic.ARITHMETIC_ARRAYS_GRAMMAR),
        ],
    )
    def test_arithmetic_grammars(self, grammar_name, grammar_text):
        """Test arithmetic grammars."""
        grammar = Grammar.from_text(grammar_text, "E")
        assert grammar is not None
        assert len(grammar.productions) > 0

        # Test automaton construction
        automaton = Automaton(grammar)
        assert automaton is not None
        assert len(automaton.states) > 0

        # Test table construction
        table = ParsingTable(automaton)
        assert table is not None
        assert len(table.action_table) > 0

    @pytest.mark.parametrize(
        "grammar_name,grammar_text",
        [
            ("c_like", programming.C_LIKE_GRAMMAR),
            ("python_like", programming.PYTHON_LIKE_GRAMMAR),
            ("javascript_like", programming.JAVASCRIPT_LIKE_GRAMMAR),
            ("assembly_like", programming.ASSEMBLY_LIKE_GRAMMAR),
        ],
    )
    def test_programming_grammars(self, grammar_name, grammar_text):
        """Test programming language grammars."""
        grammar = Grammar.from_text(grammar_text, "program")
        assert grammar is not None
        assert len(grammar.productions) > 0

        # Test automaton construction
        automaton = Automaton(grammar)
        assert automaton is not None
        assert len(automaton.states) > 0

        # Test table construction
        table = ParsingTable(automaton)
        assert table is not None
        assert len(table.action_table) > 0

    @pytest.mark.parametrize(
        "grammar_name,grammar_text",
        [
            ("json", data_structures.JSON_GRAMMAR),
            ("xml", data_structures.XML_GRAMMAR),
            ("csv", data_structures.CSV_GRAMMAR),
            ("sql", data_structures.SQL_GRAMMAR),
        ],
    )
    def test_data_structure_grammars(self, grammar_name, grammar_text):
        """Test data structure grammars."""
        start_symbol = (
            "value"
            if grammar_name == "json"
            else "document"
            if grammar_name == "xml"
            else "csv"
            if grammar_name == "csv"
            else "query"
        )

        grammar = Grammar.from_text(grammar_text, start_symbol)
        assert grammar is not None
        assert len(grammar.productions) > 0

        # Test automaton construction
        automaton = Automaton(grammar)
        assert automaton is not None
        assert len(automaton.states) > 0

        # Test table construction
        table = ParsingTable(automaton)
        assert table is not None
        assert len(table.action_table) > 0

    @pytest.mark.parametrize(
        "grammar_name,grammar_text",
        [
            ("boolean", mathematical.BOOLEAN_GRAMMAR),
            ("set", mathematical.SET_GRAMMAR),
            ("logic", mathematical.LOGIC_GRAMMAR),
            ("calculus", mathematical.CALCULUS_GRAMMAR),
            ("matrix", mathematical.MATRIX_GRAMMAR),
        ],
    )
    def test_mathematical_grammars(self, grammar_name, grammar_text):
        """Test mathematical grammars."""
        start_symbol = "expr" if grammar_name in ["boolean", "calculus"] else "formula" if grammar_name == "logic" else "expr"

        grammar = Grammar.from_text(grammar_text, start_symbol)
        assert grammar is not None
        assert len(grammar.productions) > 0

        # Test automaton construction
        automaton = Automaton(grammar)
        assert automaton is not None
        assert len(automaton.states) > 0

        # Test table construction
        table = ParsingTable(automaton)
        assert table is not None
        assert len(table.action_table) > 0

    @pytest.mark.parametrize(
        "grammar_name,grammar_text",
        [
            ("ambiguous", edge_cases.AMBIGUOUS_GRAMMAR),
            ("left_recursive", edge_cases.LEFT_RECURSIVE_GRAMMAR),
            ("right_recursive", edge_cases.RIGHT_RECURSIVE_GRAMMAR),
            ("epsilon", edge_cases.EPSILON_GRAMMAR),
            ("single_production", edge_cases.SINGLE_PRODUCTION_GRAMMAR),
            ("empty", edge_cases.EMPTY_GRAMMAR),
            ("deep_nesting", edge_cases.DEEP_NESTING_GRAMMAR),
            ("many_alternatives", edge_cases.MANY_ALTERNATIVES_GRAMMAR),
            ("long_rhs", edge_cases.LONG_RHS_GRAMMAR),
        ],
    )
    def test_edge_case_grammars(self, grammar_name, grammar_text):
        """Test edge case grammars."""
        grammar = Grammar.from_text(grammar_text, "S")
        assert grammar is not None
        assert len(grammar.productions) > 0

        # Test automaton construction
        automaton = Automaton(grammar)
        assert automaton is not None
        assert len(automaton.states) > 0

        # Test table construction
        table = ParsingTable(automaton)
        assert table is not None
        assert len(table.action_table) > 0

        # Check for expected conflicts
        if grammar_name == "ambiguous":
            assert table.has_conflicts()
        elif grammar_name in ["left_recursive", "right_recursive", "epsilon", "single_production", "empty"]:
            # These should be valid LR(1) grammars
            assert not table.has_conflicts()

    def test_circular_grammar_handling(self):
        """Test that circular grammars are handled gracefully."""
        grammar = Grammar.from_text(edge_cases.CIRCULAR_GRAMMAR, "A")
        assert grammar is not None

        # Should handle circular grammar without infinite loops
        automaton = Automaton(grammar)
        assert automaton is not None
        assert len(automaton.states) > 0

    def test_self_referencing_grammar_handling(self):
        """Test that self-referencing grammars are handled gracefully."""
        grammar = Grammar.from_text(edge_cases.SELF_REF_GRAMMAR, "A")
        assert grammar is not None

        # Should handle self-referencing grammar without infinite loops
        automaton = Automaton(grammar)
        assert automaton is not None
        assert len(automaton.states) > 0


def test_all_examples_import():
    """Test that all example modules can be imported."""
    import backend.examples.arithmetic
    import backend.examples.programming
    import backend.examples.data_structures
    import backend.examples.mathematical
    import backend.examples.edge_cases

    # Test that all grammar constants are defined
    assert hasattr(backend.examples.arithmetic, "ARITHMETIC_GRAMMAR")
    assert hasattr(backend.examples.programming, "C_LIKE_GRAMMAR")
    assert hasattr(backend.examples.data_structures, "JSON_GRAMMAR")
    assert hasattr(backend.examples.mathematical, "BOOLEAN_GRAMMAR")
    assert hasattr(backend.examples.edge_cases, "AMBIGUOUS_GRAMMAR")
