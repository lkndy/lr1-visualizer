"""Comprehensive tests for parsing table generation and validation."""

import pytest
from parser.automaton import Automaton
from parser.grammar_v2 import Grammar
from parser.table import ParsingTable
from parser.types import ActionType


class TestParsingTableConstruction:
    """Test parsing table construction functionality."""

    def test_construct_simple_table(self, simple_grammar):
        """Test constructing parsing table for simple grammar."""
        automaton = Automaton(simple_grammar)
        table = ParsingTable(automaton)

        assert table is not None
        assert len(table.action_table) > 0
        assert len(table.goto_table) > 0

    def test_construct_arithmetic_table(self, arithmetic_grammar):
        """Test constructing parsing table for arithmetic grammar."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        assert table is not None
        assert len(table.action_table) > 0
        assert len(table.goto_table) > 0

    def test_construct_left_recursive_table(self, left_recursive_grammar):
        """Test constructing parsing table for left recursive grammar."""
        automaton = Automaton(left_recursive_grammar)
        table = ParsingTable(automaton)

        assert table is not None
        assert len(table.action_table) > 0
        assert len(table.goto_table) > 0

    def test_construct_ambiguous_table(self, ambiguous_grammar):
        """Test constructing parsing table for ambiguous grammar."""
        automaton = Automaton(ambiguous_grammar)
        table = ParsingTable(automaton)

        assert table is not None
        # Ambiguous grammar should have conflicts
        assert table.has_conflicts()
        assert len(table.conflicts) > 0

    def test_construct_epsilon_table(self, epsilon_grammar):
        """Test constructing parsing table for grammar with epsilon productions."""
        automaton = Automaton(epsilon_grammar)
        table = ParsingTable(automaton)

        assert table is not None
        assert len(table.action_table) > 0
        assert len(table.goto_table) > 0


class TestActionTable:
    """Test ACTION table functionality."""

    def test_action_table_entries(self, arithmetic_grammar):
        """Test ACTION table has proper entries."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        # Should have shift actions
        shift_actions = [action for action in table.action_table.values() if action.action_type == ActionType.SHIFT.value]
        assert len(shift_actions) > 0

        # Should have reduce actions
        reduce_actions = [action for action in table.action_table.values() if action.action_type == ActionType.REDUCE.value]
        assert len(reduce_actions) > 0

        # Should have accept action
        accept_actions = [action for action in table.action_table.values() if action.action_type == ActionType.ACCEPT.value]
        assert len(accept_actions) > 0

    def test_action_table_lookup(self, arithmetic_grammar):
        """Test ACTION table lookup functionality."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        # Test getting actions for valid state-symbol pairs
        for (state, symbol), action in table.action_table.items():
            retrieved_action = table.get_action(state, symbol)
            assert retrieved_action == action
            assert retrieved_action is not None

    def test_action_table_missing_entries(self, arithmetic_grammar):
        """Test ACTION table lookup for missing entries."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        # Test getting actions for invalid state-symbol pairs
        invalid_state = 9999
        invalid_symbol = "invalid"

        action = table.get_action(invalid_state, invalid_symbol)
        assert action is None

    def test_action_table_consistency(self, arithmetic_grammar):
        """Test ACTION table consistency."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        for (state, symbol), action in table.action_table.items():
            # State should be valid
            assert 0 <= state < len(automaton.states)

            # Symbol should be valid
            assert symbol is not None
            assert len(symbol) > 0

            # Action should be valid
            assert action is not None
            assert action.action_type in [ActionType.SHIFT.value, ActionType.REDUCE.value, ActionType.ACCEPT.value, ActionType.ERROR.value]

            # Target should be valid for shift/reduce actions
            if action.action_type == ActionType.SHIFT.value:
                assert action.target is not None
                assert 0 <= action.target < len(automaton.states)
            elif action.action_type == ActionType.REDUCE.value:
                assert action.target is not None
                assert 0 <= action.target < len(automaton.grammar.productions)


class TestGotoTable:
    """Test GOTO table functionality."""

    def test_goto_table_entries(self, arithmetic_grammar):
        """Test GOTO table has proper entries."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        # Should have GOTO entries for non-terminals
        assert len(table.goto_table) > 0

        # All entries should have valid target states
        for (state, symbol), target_state in table.goto_table.items():
            assert 0 <= state < len(automaton.states)
            assert 0 <= target_state < len(automaton.states)
            assert symbol is not None

    def test_goto_table_lookup(self, arithmetic_grammar):
        """Test GOTO table lookup functionality."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        # Test getting GOTO for valid state-symbol pairs
        for (state, symbol), target_state in table.goto_table.items():
            retrieved_target = table.get_goto(state, symbol)
            assert retrieved_target == target_state
            assert retrieved_target is not None

    def test_goto_table_missing_entries(self, arithmetic_grammar):
        """Test GOTO table lookup for missing entries."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        # Test getting GOTO for invalid state-symbol pairs
        invalid_state = 9999
        invalid_symbol = "invalid"

        target = table.get_goto(invalid_state, invalid_symbol)
        assert target is None


class TestTableConflicts:
    """Test parsing table conflict detection."""

    def test_no_conflicts_simple_grammar(self, simple_grammar):
        """Test that simple grammar has no conflicts."""
        automaton = Automaton(simple_grammar)
        table = ParsingTable(automaton)

        assert not table.has_conflicts()
        assert table.is_valid_table()
        assert len(table.conflicts) == 0

    def test_no_conflicts_arithmetic_grammar(self, arithmetic_grammar):
        """Test that arithmetic grammar has no conflicts."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        assert not table.has_conflicts()
        assert table.is_valid_table()
        assert len(table.conflicts) == 0

    def test_conflicts_ambiguous_grammar(self, ambiguous_grammar):
        """Test that ambiguous grammar has conflicts."""
        automaton = Automaton(ambiguous_grammar)
        table = ParsingTable(automaton)

        assert table.has_conflicts()
        assert not table.is_valid_table()
        assert len(table.conflicts) > 0

    def test_conflict_summary(self, ambiguous_grammar):
        """Test conflict summary generation."""
        automaton = Automaton(ambiguous_grammar)
        table = ParsingTable(automaton)

        summary = table.get_conflict_summary()

        assert "total_conflicts" in summary
        assert "conflict_types" in summary
        assert "is_lr1" in summary

        assert summary["total_conflicts"] > 0
        assert not summary["is_lr1"]
        assert len(summary["conflict_types"]) > 0

    def test_shift_reduce_conflicts(self, ambiguous_grammar):
        """Test shift-reduce conflict detection."""
        automaton = Automaton(ambiguous_grammar)
        table = ParsingTable(automaton)

        shift_reduce_conflicts = [conflict for conflict in table.conflicts if conflict.conflict_type == "shift_reduce"]

        # Should have shift-reduce conflicts
        assert len(shift_reduce_conflicts) > 0

        # Each conflict should have required fields
        for conflict in shift_reduce_conflicts:
            assert hasattr(conflict, "state")
            assert hasattr(conflict, "symbol")
            assert hasattr(conflict, "actions")
            assert hasattr(conflict, "conflict_type")
            assert len(conflict.actions) == 2  # Should have two conflicting actions

    def test_reduce_reduce_conflicts(self):
        """Test reduce-reduce conflict detection."""
        # Create grammar that should have reduce-reduce conflicts
        grammar_text = """
        S: A | B
        A: "a"
        B: "a"
        """
        grammar = Grammar.from_text(grammar_text, "S")
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)

        reduce_reduce_conflicts = [conflict for conflict in table.conflicts if conflict.conflict_type == "reduce_reduce"]

        # Should have reduce-reduce conflicts
        assert len(reduce_reduce_conflicts) > 0


class TestTableExport:
    """Test parsing table export functionality."""

    def test_export_action_table(self, arithmetic_grammar):
        """Test ACTION table export."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        exported = table.export_action_table()

        assert "headers" in exported
        assert "rows" in exported
        assert len(exported["headers"]) > 0
        assert len(exported["rows"]) > 0

        # Headers should include "State" and terminal symbols
        assert "State" in exported["headers"]

        # Each row should have the right number of columns
        for row in exported["rows"]:
            assert len(row) == len(exported["headers"])

    def test_export_goto_table(self, arithmetic_grammar):
        """Test GOTO table export."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        exported = table.export_goto_table()

        assert "headers" in exported
        assert "rows" in exported
        assert len(exported["headers"]) > 0
        assert len(exported["rows"]) > 0

        # Headers should include "State" and non-terminal symbols
        assert "State" in exported["headers"]

        # Each row should have the right number of columns
        for row in exported["rows"]:
            assert len(row) == len(exported["headers"])

    def test_export_table_summary(self, arithmetic_grammar):
        """Test table summary export."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        summary = table.get_table_summary()

        assert "num_states" in summary
        assert "num_terminals" in summary
        assert "num_non_terminals" in summary
        assert "action_entries" in summary
        assert "goto_entries" in summary
        assert "has_conflicts" in summary
        assert "conflicts" in summary

        assert summary["num_states"] > 0
        assert summary["action_entries"] > 0
        assert summary["goto_entries"] > 0
        assert isinstance(summary["has_conflicts"], bool)


class TestTableValidation:
    """Test parsing table validation."""

    def test_table_validation_no_conflicts(self, arithmetic_grammar):
        """Test table validation with no conflicts."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        assert table.is_valid_table()
        assert not table.has_conflicts()

    def test_table_validation_with_conflicts(self, ambiguous_grammar):
        """Test table validation with conflicts."""
        automaton = Automaton(ambiguous_grammar)
        table = ParsingTable(automaton)

        assert not table.is_valid_table()
        assert table.has_conflicts()

    def test_table_consistency(self, arithmetic_grammar):
        """Test table consistency checks."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        # All action table entries should be valid
        for (state, symbol), action in table.action_table.items():
            assert 0 <= state < len(automaton.states)
            assert symbol in [s.name for s in automaton.grammar.terminals]
            assert action is not None

        # All goto table entries should be valid
        for (state, symbol), target_state in table.goto_table.items():
            assert 0 <= state < len(automaton.states)
            assert symbol in [s.name for s in automaton.grammar.non_terminals]
            assert 0 <= target_state < len(automaton.states)


class TestTableEdgeCases:
    """Test parsing table edge cases and error conditions."""

    def test_empty_grammar_table(self):
        """Test table construction with empty grammar."""
        grammar_text = """
        S: ε
        """
        grammar = Grammar.from_text(grammar_text, "S")
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)

        assert table is not None
        assert len(table.action_table) > 0  # Should have at least accept action
        assert len(table.goto_table) >= 0

    def test_single_production_table(self):
        """Test table construction with single production."""
        grammar_text = """
        S: "a"
        """
        grammar = Grammar.from_text(grammar_text, "S")
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)

        assert table is not None
        assert len(table.action_table) > 0
        assert len(table.goto_table) >= 0

    def test_table_with_epsilon_productions(self, epsilon_grammar):
        """Test table construction with epsilon productions."""
        automaton = Automaton(epsilon_grammar)
        table = ParsingTable(automaton)

        assert table is not None
        assert len(table.action_table) > 0
        assert len(table.goto_table) >= 0

    def test_table_string_representation(self, arithmetic_grammar):
        """Test table string representation."""
        automaton = Automaton(arithmetic_grammar)
        table = ParsingTable(automaton)

        table_str = str(table)

        assert isinstance(table_str, str)
        assert len(table_str) > 0
        assert "ACTION Table:" in table_str
        assert "GOTO Table:" in table_str


class TestTablePerformance:
    """Test parsing table performance characteristics."""

    def test_table_construction_time(self, complex_grammar):
        """Test that table construction completes in reasonable time."""
        import time

        automaton = Automaton(complex_grammar)

        start_time = time.time()
        table = ParsingTable(automaton)
        end_time = time.time()

        construction_time = end_time - start_time

        # Should complete in reasonable time
        assert construction_time < 5.0  # 5 seconds max
        assert table is not None

    def test_table_memory_usage(self, complex_grammar):
        """Test that table doesn't use excessive memory."""
        automaton = Automaton(complex_grammar)
        table = ParsingTable(automaton)

        # Basic memory usage checks
        assert len(table.action_table) < 10000  # Should not have too many action entries
        assert len(table.goto_table) < 10000  # Should not have too many goto entries
        assert len(table.conflicts) < 1000  # Should not have too many conflicts
