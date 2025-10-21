"""Validation tools for grammar, items, and parsing table consistency."""

import logging
from typing import Any, Dict, List

from parser.grammar_v2 import Grammar
from parser.types import Symbol, SymbolType

logger = logging.getLogger(__name__)


class GrammarValidator:
    """Validate grammar consistency and correctness."""

    def __init__(self, grammar: Grammar):
        """Initialize with a grammar."""
        self.grammar = grammar
        self.logger = logging.getLogger(f"{__name__}.GrammarValidator")

    def validate_symbol_usage(self) -> List[Dict[str, Any]]:
        """Validate that all symbols are properly defined and used."""
        errors = []

        # Check that all non-terminals have productions
        non_terminals_with_productions = {p.lhs for p in self.grammar.productions}

        for nt in self.grammar.non_terminals:
            if nt not in non_terminals_with_productions:
                errors.append(
                    {
                        "type": "undefined_non_terminal",
                        "symbol": nt.name,
                        "message": f"Non-terminal '{nt.name}' has no productions",
                    }
                )

        # Check for undefined symbols in RHS
        all_defined_symbols = set()
        for production in self.grammar.productions:
            all_defined_symbols.add(production.lhs)
            all_defined_symbols.update(production.rhs)

        for production in self.grammar.productions:
            for symbol in production.rhs:
                if symbol not in all_defined_symbols:
                    errors.append(
                        {
                            "type": "undefined_symbol",
                            "symbol": symbol.name,
                            "production": str(production),
                            "message": f"Symbol '{symbol.name}' used but not defined",
                        }
                    )

        return errors

    def validate_first_follow_consistency(self) -> List[Dict[str, Any]]:
        """Validate FIRST and FOLLOW set consistency."""
        errors = []

        # Check for epsilon in FIRST sets where it shouldn't be
        for nt in self.grammar.non_terminals:
            first_set = self.grammar.first((nt,))
            epsilon_symbol = Symbol("ε", SymbolType.EPSILON)

            # Check if epsilon is in FIRST(nt) but nt has no epsilon production
            if epsilon_symbol in first_set and not self.grammar._has_epsilon_production(nt):
                errors.append(
                    {
                        "type": "first_follow_inconsistency",
                        "symbol": nt.name,
                        "message": f"Non-terminal '{nt.name}' has epsilon in FIRST set but no epsilon production",
                    }
                )

        return errors

    def validate_grammar_structure(self) -> List[Dict[str, Any]]:
        """Validate basic grammar structure."""
        errors = []

        # Check for empty grammar
        if not self.grammar.productions:
            errors.append({"type": "empty_grammar", "message": "Grammar has no productions"})

        # Check for start symbol productions
        start_productions = [p for p in self.grammar.productions if p.lhs == self.grammar.start_symbol]
        if not start_productions:
            errors.append(
                {
                    "type": "no_start_productions",
                    "message": f"Start symbol '{self.grammar.start_symbol.name}' has no productions",
                }
            )

        # Check for unreachable symbols
        reachable = self.grammar._find_reachable_symbols()
        unreachable = self.grammar.non_terminals - reachable

        for symbol in unreachable:
            errors.append(
                {
                    "type": "unreachable_symbol",
                    "symbol": symbol.name,
                    "message": f"Non-terminal '{symbol.name}' is unreachable from start symbol",
                }
            )

        return errors

    def validate_lr1_properties(self) -> List[Dict[str, Any]]:
        """Validate properties specific to LR(1) parsing."""
        errors = []

        # Check for left recursion (warning, not error for LR)
        left_recursive = self.grammar._find_left_recursive_symbols()
        if left_recursive:
            self.logger.warning(f"Left recursion detected: {[s.name for s in left_recursive]} (acceptable for LR)")

        # Check for ambiguous productions
        productions_by_lhs = {}
        for production in self.grammar.productions:
            lhs_name = production.lhs.name
            if lhs_name not in productions_by_lhs:
                productions_by_lhs[lhs_name] = []
            productions_by_lhs[lhs_name].append(production)

        for lhs_name, productions in productions_by_lhs.items():
            if len(productions) > 1:
                # Check for identical RHS
                rhs_strings = []
                for production in productions:
                    rhs_str = " ".join(s.name for s in production.rhs) if production.rhs else "ε"
                    rhs_strings.append(rhs_str)

                if len(set(rhs_strings)) != len(rhs_strings):
                    errors.append(
                        {
                            "type": "duplicate_productions",
                            "symbol": lhs_name,
                            "message": f"Non-terminal '{lhs_name}' has duplicate productions",
                        }
                    )

        return errors

    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        self.logger.info("Running comprehensive grammar validation")

        all_errors = []
        all_errors.extend(self.validate_symbol_usage())
        all_errors.extend(self.validate_first_follow_consistency())
        all_errors.extend(self.validate_grammar_structure())
        all_errors.extend(self.validate_lr1_properties())

        return {
            "is_valid": len(all_errors) == 0,
            "error_count": len(all_errors),
            "errors": all_errors,
            "error_types": list(set(error["type"] for error in all_errors)),
        }


class ItemSetValidator:
    """Validate LR(1) item set consistency."""

    def __init__(self, item_set):
        """Initialize with an item set."""
        self.item_set = item_set
        self.logger = logging.getLogger(f"{__name__}.ItemSetValidator")

    def validate_item_consistency(self) -> List[Dict[str, Any]]:
        """Validate that items in the set are consistent."""
        errors = []

        for item in self.item_set.items:
            # Check dot position validity
            if item.dot_position < 0 or item.dot_position > len(item.production.rhs):
                errors.append(
                    {
                        "type": "invalid_dot_position",
                        "item": str(item),
                        "message": f"Invalid dot position {item.dot_position} for production {item.production}",
                    }
                )

            # Check lookahead is terminal
            if item.lookahead.symbol_type != SymbolType.TERMINAL:
                errors.append(
                    {
                        "type": "invalid_lookahead",
                        "item": str(item),
                        "message": f"Lookahead must be terminal, got {item.lookahead.symbol_type}",
                    }
                )

        return errors

    def validate_closure_properties(self) -> List[Dict[str, Any]]:
        """Validate closure computation properties."""
        errors = []

        # Check that all items have proper lookaheads
        for item in self.item_set.items:
            if not item.is_complete:
                # For incomplete items, check that lookahead is reasonable
                if item.lookahead.name == "ε":
                    errors.append(
                        {"type": "epsilon_lookahead", "item": str(item), "message": "Incomplete item has epsilon lookahead"}
                    )

        return errors

    def validate_all(self) -> Dict[str, Any]:
        """Run all item set validation checks."""
        self.logger.debug("Validating item set")

        all_errors = []
        all_errors.extend(self.validate_item_consistency())
        all_errors.extend(self.validate_closure_properties())

        return {
            "is_valid": len(all_errors) == 0,
            "error_count": len(all_errors),
            "errors": all_errors,
            "item_count": len(self.item_set.items),
        }


class TableValidator:
    """Validate parsing table consistency."""

    def __init__(self, parsing_table):
        """Initialize with a parsing table."""
        self.parsing_table = parsing_table
        self.logger = logging.getLogger(f"{__name__}.TableValidator")

    def validate_action_table_consistency(self) -> List[Dict[str, Any]]:
        """Validate ACTION table consistency."""
        errors = []

        # Check for missing actions where they should exist
        for (state, symbol), action in self.parsing_table.action_table.items():
            # Validate action type and target
            if action.action_type.value == "shift" and action.target is None:
                errors.append(
                    {
                        "type": "invalid_shift_action",
                        "state": state,
                        "symbol": symbol,
                        "message": "Shift action missing target state",
                    }
                )

            if action.action_type.value == "reduce" and action.target is None:
                errors.append(
                    {
                        "type": "invalid_reduce_action",
                        "state": state,
                        "symbol": symbol,
                        "message": "Reduce action missing production index",
                    }
                )

        return errors

    def validate_goto_table_consistency(self) -> List[Dict[str, Any]]:
        """Validate GOTO table consistency."""
        errors = []

        # Check that all GOTO entries have valid target states
        for (state, symbol), target_state in self.parsing_table.goto_table.items():
            if target_state is None:
                errors.append(
                    {
                        "type": "invalid_goto_target",
                        "state": state,
                        "symbol": symbol,
                        "message": "GOTO action missing target state",
                    }
                )

            # Check that target state exists
            if target_state >= len(self.parsing_table.automaton.states):
                errors.append(
                    {
                        "type": "invalid_goto_state",
                        "state": state,
                        "symbol": symbol,
                        "target_state": target_state,
                        "message": f"GOTO target state {target_state} does not exist",
                    }
                )

        return errors

    def validate_conflict_resolution(self) -> List[Dict[str, Any]]:
        """Validate conflict resolution strategies."""
        errors = []

        for conflict in self.parsing_table.conflicts:
            if conflict.conflict_type == "shift_reduce":
                # Check if shift-reduce conflict is resolvable
                errors.append(
                    {
                        "type": "shift_reduce_conflict",
                        "state": conflict.state,
                        "symbol": conflict.symbol,
                        "message": f"Shift-reduce conflict in state {conflict.state} for symbol '{conflict.symbol}'",
                    }
                )

            elif conflict.conflict_type == "reduce_reduce":
                # Reduce-reduce conflicts are generally not resolvable
                errors.append(
                    {
                        "type": "reduce_reduce_conflict",
                        "state": conflict.state,
                        "symbol": conflict.symbol,
                        "message": f"Reduce-reduce conflict in state {conflict.state} for symbol '{conflict.symbol}'",
                    }
                )

        return errors

    def validate_table_completeness(self) -> List[Dict[str, Any]]:
        """Validate that table is complete for all necessary entries."""
        errors = []

        # This would require knowledge of what entries should exist
        # For now, just check that we have some entries
        if not self.parsing_table.action_table:
            errors.append({"type": "empty_action_table", "message": "ACTION table is empty"})

        if not self.parsing_table.goto_table:
            errors.append({"type": "empty_goto_table", "message": "GOTO table is empty"})

        return errors

    def validate_all(self) -> Dict[str, Any]:
        """Run all table validation checks."""
        self.logger.info("Running comprehensive table validation")

        all_errors = []
        all_errors.extend(self.validate_action_table_consistency())
        all_errors.extend(self.validate_goto_table_consistency())
        all_errors.extend(self.validate_conflict_resolution())
        all_errors.extend(self.validate_table_completeness())

        return {
            "is_valid": len(all_errors) == 0,
            "error_count": len(all_errors),
            "errors": all_errors,
            "has_conflicts": self.parsing_table.has_conflicts(),
            "conflict_count": len(self.parsing_table.conflicts),
        }
