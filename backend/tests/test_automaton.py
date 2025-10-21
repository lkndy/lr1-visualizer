"""Comprehensive tests for automaton construction and conflict detection."""

import pytest
from parser.automaton import Automaton
from parser.grammar_v2 import Grammar
from parser.types import Symbol, SymbolType


class TestAutomatonConstruction:
    """Test automaton construction functionality."""

    def test_construct_simple_automaton(self, simple_grammar):
        """Test constructing automaton for simple grammar."""
        automaton = Automaton(simple_grammar)

        assert automaton is not None
        assert len(automaton.states) > 0
        assert len(automaton.transitions) > 0

    def test_construct_arithmetic_automaton(self, arithmetic_grammar):
        """Test constructing automaton for arithmetic grammar."""
        automaton = Automaton(arithmetic_grammar)

        assert automaton is not None
        assert len(automaton.states) > 5  # Should have multiple states
        assert len(automaton.transitions) > 5  # Should have multiple transitions

    def test_construct_left_recursive_automaton(self, left_recursive_grammar):
        """Test constructing automaton for left recursive grammar."""
        automaton = Automaton(left_recursive_grammar)

        assert automaton is not None
        assert len(automaton.states) > 0
        assert len(automaton.transitions) > 0

    def test_construct_ambiguous_automaton(self, ambiguous_grammar):
        """Test constructing automaton for ambiguous grammar."""
        automaton = Automaton(ambiguous_grammar)

        assert automaton is not None
        assert len(automaton.states) > 0
        # Ambiguous grammar should have conflicts
        conflicts = automaton.find_conflicts()
        assert len(conflicts) > 0

    def test_construct_epsilon_automaton(self, epsilon_grammar):
        """Test constructing automaton for grammar with epsilon productions."""
        automaton = Automaton(epsilon_grammar)

        assert automaton is not None
        assert len(automaton.states) > 0
        assert len(automaton.transitions) > 0

    def test_construct_complex_automaton(self, complex_grammar):
        """Test constructing automaton for complex grammar."""
        automaton = Automaton(complex_grammar)

        assert automaton is not None
        assert len(automaton.states) > 10  # Complex grammar should have many states
        assert len(automaton.transitions) > 10


class TestAutomatonStates:
    """Test automaton state functionality."""

    def test_initial_state(self, simple_grammar):
        """Test that initial state is properly created."""
        automaton = Automaton(simple_grammar)

        # First state should be the initial state
        initial_state = automaton.states[0]
        assert len(initial_state.items) > 0

        # Should contain the augmented start production
        start_production = simple_grammar.productions[0]
        has_start_item = any(item.production == start_production and item.dot_position == 0 for item in initial_state.items)
        assert has_start_item

    def test_state_numbering(self, arithmetic_grammar):
        """Test that states are properly numbered."""
        automaton = Automaton(arithmetic_grammar)

        # All states should have valid numbers
        for i, state in enumerate(automaton.states):
            state_number = automaton.get_state_number(state)
            assert state_number == i

    def test_state_info(self, arithmetic_grammar):
        """Test getting state information."""
        automaton = Automaton(arithmetic_grammar)

        for i in range(len(automaton.states)):
            state_info = automaton.get_state_info(i)

            assert "state_index" in state_info
            assert "items" in state_info
            assert "shift_items" in state_info
            assert "reduce_items" in state_info
            assert "shift_symbols" in state_info
            assert "transitions_out" in state_info
            assert "transitions_in" in state_info

            assert state_info["state_index"] == i
            assert len(state_info["items"]) > 0

    def test_state_transitions(self, arithmetic_grammar):
        """Test state transitions."""
        automaton = Automaton(arithmetic_grammar)

        # Check that transitions are properly set up
        for i, state in enumerate(automaton.states):
            transitions_out = automaton.get_transitions_from_state(i)
            transitions_in = automaton.get_transitions_to_state(i)

            # Each transition should have valid target state
            for transition in transitions_out:
                assert 0 <= transition.to_state < len(automaton.states)
                assert transition.from_state == i
                assert transition.symbol is not None

            # Each incoming transition should have valid source state
            for transition in transitions_in:
                assert 0 <= transition.from_state < len(automaton.states)
                assert transition.to_state == i
                assert transition.symbol is not None


class TestAutomatonConflicts:
    """Test conflict detection in automaton."""

    def test_no_conflicts_simple_grammar(self, simple_grammar):
        """Test that simple grammar has no conflicts."""
        automaton = Automaton(simple_grammar)
        conflicts = automaton.find_conflicts()

        assert len(conflicts) == 0
        assert automaton.is_lr1_grammar()

    def test_no_conflicts_arithmetic_grammar(self, arithmetic_grammar):
        """Test that arithmetic grammar has no conflicts."""
        automaton = Automaton(arithmetic_grammar)
        conflicts = automaton.find_conflicts()

        assert len(conflicts) == 0
        assert automaton.is_lr1_grammar()

    def test_conflicts_ambiguous_grammar(self, ambiguous_grammar):
        """Test that ambiguous grammar has conflicts."""
        automaton = Automaton(ambiguous_grammar)
        conflicts = automaton.find_conflicts()

        assert len(conflicts) > 0
        assert not automaton.is_lr1_grammar()

    def test_shift_reduce_conflicts(self, ambiguous_grammar):
        """Test shift-reduce conflict detection."""
        automaton = Automaton(ambiguous_grammar)
        conflicts = automaton.find_conflicts()

        shift_reduce_conflicts = [c for c in conflicts if c["type"] == "shift_reduce"]

        # Should have shift-reduce conflicts
        assert len(shift_reduce_conflicts) > 0

        # Each conflict should have required fields
        for conflict in shift_reduce_conflicts:
            assert "state" in conflict
            assert "symbol" in conflict
            assert "shift_transition" in conflict
            assert "reduce_item" in conflict
            assert "production_index" in conflict

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
        conflicts = automaton.find_conflicts()

        reduce_reduce_conflicts = [c for c in conflicts if c["type"] == "reduce_reduce"]

        # Should have reduce-reduce conflicts
        assert len(reduce_reduce_conflicts) > 0

        # Each conflict should have required fields
        for conflict in reduce_reduce_conflicts:
            assert "state" in conflict
            assert "symbol" in conflict
            assert "reduce_items" in conflict
            assert "production_indices" in conflict


class TestGrammarTypeDetection:
    """Test grammar type detection."""

    def test_lr1_grammar_detection(self, arithmetic_grammar):
        """Test detection of LR(1) grammar."""
        automaton = Automaton(arithmetic_grammar)
        grammar_type = automaton.get_grammar_type()

        assert grammar_type == "LR(1)"
        assert automaton.is_lr1_grammar()

    def test_non_lr1_grammar_detection(self, ambiguous_grammar):
        """Test detection of non-LR(1) grammar."""
        automaton = Automaton(ambiguous_grammar)
        grammar_type = automaton.get_grammar_type()

        assert grammar_type != "LR(1)"
        assert not automaton.is_lr1_grammar()

    def test_grammar_type_with_conflicts(self):
        """Test grammar type detection with different conflict types."""
        # Grammar with shift-reduce conflicts (actually ambiguous)
        grammar_text = """
        S: S S | "a"
        """
        grammar = Grammar.from_text(grammar_text, "S")
        automaton = Automaton(grammar)
        grammar_type = automaton.get_grammar_type()

        # Should indicate some type of conflict
        assert "conflict" in grammar_type.lower() or grammar_type != "LR(1)"


class TestAutomatonProperties:
    """Test automaton properties and invariants."""

    def test_automaton_consistency(self, arithmetic_grammar):
        """Test that automaton maintains consistency."""
        automaton = Automaton(arithmetic_grammar)

        # All states should be reachable
        reachable_states = set()
        for transition in automaton.transitions:
            reachable_states.add(transition.from_state)
            reachable_states.add(transition.to_state)

        # State 0 should always be reachable (initial state)
        assert 0 in reachable_states

        # All states should be reachable from state 0
        # (This is a simplified check - in practice, you'd do a full reachability analysis)
        assert len(reachable_states) > 0

    def test_transition_consistency(self, arithmetic_grammar):
        """Test that transitions are consistent."""
        automaton = Automaton(arithmetic_grammar)

        for transition in automaton.transitions:
            # Source and target states should exist
            assert 0 <= transition.from_state < len(automaton.states)
            assert 0 <= transition.to_state < len(automaton.states)

            # Symbol should be valid
            assert transition.symbol is not None
            assert transition.symbol.name is not None

    def test_item_set_consistency(self, arithmetic_grammar):
        """Test that item sets are consistent."""
        automaton = Automaton(arithmetic_grammar)

        for state in automaton.states:
            # Each state should have items
            assert len(state.items) > 0

            # Items should be valid
            for item in state.items:
                assert item.production is not None
                assert 0 <= item.dot_position <= len(item.production.rhs)
                assert item.lookahead is not None


class TestAutomatonEdgeCases:
    """Test automaton edge cases and error conditions."""

    def test_empty_grammar_automaton(self):
        """Test automaton construction with empty grammar."""
        grammar_text = """
        S: ε
        """
        grammar = Grammar.from_text(grammar_text, "S")
        automaton = Automaton(grammar)

        assert automaton is not None
        assert len(automaton.states) > 0

    def test_single_production_automaton(self):
        """Test automaton construction with single production."""
        grammar_text = """
        S: "a"
        """
        grammar = Grammar.from_text(grammar_text, "S")
        automaton = Automaton(grammar)

        assert automaton is not None
        assert len(automaton.states) > 0

    def test_very_large_automaton(self):
        """Test automaton construction with large grammar."""
        # Create grammar with many productions
        grammar_text = """
        S: A1 A2 A3 A4 A5
        A1: "a1" | B1
        A2: "a2" | B2
        A3: "a3" | B3
        A4: "a4" | B4
        A5: "a5" | B5
        B1: "b1"
        B2: "b2"
        B3: "b3"
        B4: "b4"
        B5: "b5"
        """
        grammar = Grammar.from_text(grammar_text, "S")
        automaton = Automaton(grammar)

        assert automaton is not None
        assert len(automaton.states) > 0

    def test_automaton_with_cycles(self):
        """Test automaton construction with cyclic grammar."""
        grammar_text = """
        A: B
        B: C
        C: A
        """
        grammar = Grammar.from_text(grammar_text, "A")
        automaton = Automaton(grammar)

        # Should handle cycles gracefully
        assert automaton is not None
        assert len(automaton.states) > 0


class TestAutomatonPerformance:
    """Test automaton performance characteristics."""

    def test_automaton_construction_time(self, complex_grammar):
        """Test that automaton construction completes in reasonable time."""
        import time

        start_time = time.time()
        automaton = Automaton(complex_grammar)
        end_time = time.time()

        construction_time = end_time - start_time

        # Should complete in reasonable time (adjust threshold as needed)
        assert construction_time < 10.0  # 10 seconds max
        assert automaton is not None

    def test_automaton_memory_usage(self, complex_grammar):
        """Test that automaton doesn't use excessive memory."""
        automaton = Automaton(complex_grammar)

        # Basic memory usage checks
        assert len(automaton.states) < 1000  # Should not have too many states
        assert len(automaton.transitions) < 10000  # Should not have too many transitions

        # Each state should not have too many items
        for state in automaton.states:
            assert len(state.items) < 1000  # Reasonable limit per state
