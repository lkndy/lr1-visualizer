"""Comprehensive tests for LR(1) items and item sets."""

import pytest
from parser.grammar_v2 import Grammar
from parser.items import ItemSet, LR1Item
from parser.types import Production, Symbol, SymbolType


class TestLR1Item:
    """Test LR(1) item functionality."""

    def test_create_item(self, production_s_to_ab, symbol_a):
        """Test creating an LR(1) item."""
        item = LR1Item(production=production_s_to_ab, dot_position=0, lookahead=symbol_a)

        assert item.production == production_s_to_ab
        assert item.dot_position == 0
        assert item.lookahead == symbol_a

    def test_item_properties(self, production_s_to_ab, symbol_a, symbol_b):
        """Test item properties."""
        item = LR1Item(production_s_to_ab, 0, symbol_a)

        # Test symbol_after_dot
        assert item.symbol_after_dot == symbol_a

        # Test is_complete
        assert not item.is_complete
        assert not item.is_reduce_item

        # Test alpha and beta
        assert item.alpha == []
        assert item.beta == [symbol_a, symbol_b]

    def test_complete_item(self, production_s_to_ab, symbol_a, symbol_b):
        """Test complete item properties."""
        item = LR1Item(production_s_to_ab, 2, symbol_a)  # Dot at end

        assert item.is_complete
        assert item.is_reduce_item
        assert item.symbol_after_dot is None
        assert item.alpha == [symbol_a, symbol_b]
        assert item.beta == []

    def test_advance_dot(self, production_s_to_ab, symbol_a):
        """Test advancing the dot."""
        item = LR1Item(production_s_to_ab, 0, symbol_a)
        advanced_item = item.advance_dot()

        assert advanced_item.dot_position == 1
        assert advanced_item.production == production_s_to_ab
        assert advanced_item.lookahead == symbol_a

    def test_advance_dot_complete_item(self, production_s_to_ab, symbol_a):
        """Test advancing dot on complete item raises error."""
        item = LR1Item(production_s_to_ab, 2, symbol_a)  # Complete item

        with pytest.raises(ValueError):
            item.advance_dot()

    def test_invalid_dot_position(self, production_s_to_ab, symbol_a):
        """Test invalid dot position raises error."""
        with pytest.raises(ValueError):
            LR1Item(production_s_to_ab, -1, symbol_a)

        with pytest.raises(ValueError):
            LR1Item(production_s_to_ab, 3, symbol_a)  # Beyond RHS length

    def test_invalid_lookahead(self, production_s_to_ab, symbol_s):
        """Test non-terminal lookahead raises error."""
        with pytest.raises(ValueError):
            LR1Item(production_s_to_ab, 0, symbol_s)  # Non-terminal lookahead

    def test_item_string_representation(self, production_s_to_ab, symbol_a):
        """Test item string representation."""
        item = LR1Item(production_s_to_ab, 1, symbol_a)
        item_str = str(item)

        assert "S" in item_str
        assert "a" in item_str
        assert "b" in item_str
        assert "·" in item_str  # Dot symbol

    def test_item_equality(self, production_s_to_ab, symbol_a):
        """Test item equality."""
        item1 = LR1Item(production_s_to_ab, 0, symbol_a)
        item2 = LR1Item(production_s_to_ab, 0, symbol_a)
        item3 = LR1Item(production_s_to_ab, 1, symbol_a)

        assert item1 == item2
        assert item1 != item3


class TestItemSet:
    """Test item set functionality."""

    def test_create_item_set(self, production_s_to_ab, symbol_a):
        """Test creating an item set."""
        item = LR1Item(production_s_to_ab, 0, symbol_a)
        item_set = ItemSet({item})

        assert len(item_set.items) == 1
        assert item in item_set.items

    def test_item_set_equality(self, production_s_to_ab, symbol_a):
        """Test item set equality."""
        item1 = LR1Item(production_s_to_ab, 0, symbol_a)
        item2 = LR1Item(production_s_to_ab, 1, symbol_a)

        set1 = ItemSet({item1, item2})
        set2 = ItemSet({item2, item1})  # Same items, different order

        assert set1 == set2

    def test_item_set_hash(self, production_s_to_ab, symbol_a):
        """Test item set hashing."""
        item1 = LR1Item(production_s_to_ab, 0, symbol_a)
        item2 = LR1Item(production_s_to_ab, 1, symbol_a)

        set1 = ItemSet({item1, item2})
        set2 = ItemSet({item2, item1})

        assert hash(set1) == hash(set2)

    def test_get_reduce_items(self, production_s_to_ab, symbol_a):
        """Test getting reduce items from item set."""
        complete_item = LR1Item(production_s_to_ab, 2, symbol_a)
        incomplete_item = LR1Item(production_s_to_ab, 0, symbol_a)

        item_set = ItemSet({complete_item, incomplete_item})
        reduce_items = item_set.get_reduce_items()

        assert len(reduce_items) == 1
        assert complete_item in reduce_items
        assert incomplete_item not in reduce_items

    def test_get_shift_symbols(self, production_s_to_ab, symbol_a, symbol_b):
        """Test getting shift symbols from item set."""
        item1 = LR1Item(production_s_to_ab, 0, symbol_a)  # Can shift 'a'
        item2 = LR1Item(production_s_to_ab, 1, symbol_b)  # Can shift 'b'

        item_set = ItemSet({item1, item2})
        shift_symbols = item_set.get_shift_symbols()

        assert symbol_a in shift_symbols
        assert symbol_b in shift_symbols

    def test_item_set_string_representation(self, production_s_to_ab, symbol_a):
        """Test item set string representation."""
        item = LR1Item(production_s_to_ab, 0, symbol_a)
        item_set = ItemSet({item})
        item_set_str = str(item_set)

        assert "{" in item_set_str
        assert "}" in item_set_str
        assert "S" in item_set_str


class TestItemSetClosure:
    """Test item set closure computation."""

    def test_closure_simple(self, simple_grammar):
        """Test closure computation for simple grammar."""
        # Create initial item: [S' -> •S, $]
        start_production = simple_grammar.productions[0]
        end_marker = Symbol("$", SymbolType.TERMINAL)
        initial_item = LR1Item(start_production, 0, end_marker)

        item_set = ItemSet.from_initial_item(initial_item, simple_grammar)

        # Should have more items after closure
        assert len(item_set.items) > 1

    def test_closure_arithmetic(self, arithmetic_grammar):
        """Test closure computation for arithmetic grammar."""
        # Create initial item: [E' -> •E, $]
        start_production = arithmetic_grammar.productions[0]
        end_marker = Symbol("$", SymbolType.TERMINAL)
        initial_item = LR1Item(start_production, 0, end_marker)

        item_set = ItemSet.from_initial_item(initial_item, arithmetic_grammar)

        # Should have many items after closure
        assert len(item_set.items) > 5

    def test_closure_with_epsilon(self, epsilon_grammar):
        """Test closure computation with epsilon productions."""
        # Create initial item: [S' -> •S, $]
        start_production = epsilon_grammar.productions[0]
        end_marker = Symbol("$", SymbolType.TERMINAL)
        initial_item = LR1Item(start_production, 0, end_marker)

        item_set = ItemSet.from_initial_item(initial_item, epsilon_grammar)

        # Should handle epsilon productions correctly
        assert len(item_set.items) > 0

    def test_closure_cycle_guard(self):
        """Test closure computation with cycle guard."""
        # Create grammar with potential cycles
        grammar_text = """
        A: B
        B: A
        """
        grammar = Grammar.from_text(grammar_text, "A")

        start_production = grammar.productions[0]
        end_marker = Symbol("$", SymbolType.TERMINAL)
        initial_item = LR1Item(start_production, 0, end_marker)

        # Should not infinite loop
        item_set = ItemSet.from_initial_item(initial_item, grammar)
        assert len(item_set.items) >= 0  # Should complete


class TestItemSetGoto:
    """Test item set GOTO operation."""

    def test_goto_simple(self, simple_grammar):
        """Test GOTO operation for simple grammar."""
        # Create item set with [S' -> •S, $]
        start_production = simple_grammar.productions[0]
        end_marker = Symbol("$", SymbolType.TERMINAL)
        initial_item = LR1Item(start_production, 0, end_marker)
        item_set = ItemSet.from_initial_item(initial_item, simple_grammar)

        # GOTO on S should return new item set
        s_symbol = Symbol("S", SymbolType.NON_TERMINAL)
        goto_set = item_set.goto(simple_grammar, s_symbol)

        assert goto_set is not None
        assert len(goto_set.items) > 0

    def test_goto_nonexistent_symbol(self, simple_grammar):
        """Test GOTO operation with non-existent symbol."""
        start_production = simple_grammar.productions[0]
        end_marker = Symbol("$", SymbolType.TERMINAL)
        initial_item = LR1Item(start_production, 0, end_marker)
        item_set = ItemSet.from_initial_item(initial_item, simple_grammar)

        # GOTO on non-existent symbol should return None
        nonexistent_symbol = Symbol("X", SymbolType.TERMINAL)
        goto_set = item_set.goto(simple_grammar, nonexistent_symbol)

        assert goto_set is None

    def test_goto_terminal(self, arithmetic_grammar):
        """Test GOTO operation with terminal symbol."""
        # Create item set with [E -> •E+T, $]
        e_production = None
        for prod in arithmetic_grammar.productions:
            if prod.lhs.name == "E" and len(prod.rhs) > 0:
                e_production = prod
                break

        assert e_production is not None

        end_marker = Symbol("$", SymbolType.TERMINAL)
        item = LR1Item(e_production, 0, end_marker)
        item_set = ItemSet({item})

        # GOTO on terminal should work
        plus_symbol = Symbol("+", SymbolType.TERMINAL)
        goto_set = item_set.goto(arithmetic_grammar, plus_symbol)

        # Should return None since we can't shift from this item
        assert goto_set is None


class TestItemSetEdgeCases:
    """Test item set edge cases and error conditions."""

    def test_empty_item_set(self):
        """Test empty item set."""
        item_set = ItemSet(set())

        assert len(item_set.items) == 0
        assert len(item_set.get_reduce_items()) == 0
        assert len(item_set.get_shift_symbols()) == 0

    def test_item_set_with_epsilon_production(self, epsilon_grammar):
        """Test item set with epsilon production."""
        # Find epsilon production
        epsilon_prod = None
        for prod in epsilon_grammar.productions:
            if len(prod.rhs) == 0:
                epsilon_prod = prod
                break

        assert epsilon_prod is not None

        end_marker = Symbol("$", SymbolType.TERMINAL)
        item = LR1Item(epsilon_prod, 0, end_marker)
        item_set = ItemSet({item})

        # Should handle epsilon production correctly
        assert len(item_set.items) == 1
        assert item.is_complete  # Epsilon production is complete immediately

    def test_item_set_closure_with_complex_grammar(self, complex_grammar):
        """Test closure with complex grammar."""
        start_production = complex_grammar.productions[0]
        end_marker = Symbol("$", SymbolType.TERMINAL)
        initial_item = LR1Item(start_production, 0, end_marker)

        item_set = ItemSet.from_initial_item(initial_item, complex_grammar)

        # Should complete without errors
        assert len(item_set.items) > 0

    def test_item_set_goto_with_ambiguous_grammar(self, ambiguous_grammar):
        """Test GOTO with ambiguous grammar."""
        start_production = ambiguous_grammar.productions[0]
        end_marker = Symbol("$", SymbolType.TERMINAL)
        initial_item = LR1Item(start_production, 0, end_marker)

        item_set = ItemSet.from_initial_item(initial_item, ambiguous_grammar)

        # Should handle ambiguous grammar
        assert len(item_set.items) > 0

        # Test GOTO operation
        s_symbol = Symbol("S", SymbolType.NON_TERMINAL)
        goto_set = item_set.goto(ambiguous_grammar, s_symbol)

        if goto_set is not None:
            assert len(goto_set.items) > 0


class TestItemSetPerformance:
    """Test item set performance characteristics."""

    def test_large_item_set(self):
        """Test item set with many items."""
        # Create grammar with many productions
        grammar_text = """
        S: A1 A2 A3 A4 A5 A6 A7 A8 A9 A10
        A1: "a1" | B1
        A2: "a2" | B2
        A3: "a3" | B3
        A4: "a4" | B4
        A5: "a5" | B5
        A6: "a6" | B6
        A7: "a7" | B7
        A8: "a8" | B8
        A9: "a9" | B9
        A10: "a10" | B10
        B1: "b1"
        B2: "b2"
        B3: "b3"
        B4: "b4"
        B5: "b5"
        B6: "b6"
        B7: "b7"
        B8: "b8"
        B9: "b9"
        B10: "b10"
        """
        grammar = Grammar.from_text(grammar_text, "S")

        start_production = grammar.productions[0]
        end_marker = Symbol("$", SymbolType.TERMINAL)
        initial_item = LR1Item(start_production, 0, end_marker)

        # Should complete in reasonable time
        item_set = ItemSet.from_initial_item(initial_item, grammar)
        assert len(item_set.items) > 0
