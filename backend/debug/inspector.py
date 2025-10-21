"""Inspection tools for grammar, automaton, and parsing table visualization."""

import logging
from typing import Any, Dict, List

from parser.grammar_v2 import Grammar

logger = logging.getLogger(__name__)


class GrammarInspector:
    """Inspect and visualize grammar properties."""

    def __init__(self, grammar: Grammar):
        """Initialize with a grammar."""
        self.grammar = grammar
        self.logger = logging.getLogger(f"{__name__}.GrammarInspector")

    def inspect_productions(self) -> Dict[str, Any]:
        """Inspect all productions in the grammar."""
        productions_by_lhs = {}

        for i, production in enumerate(self.grammar.productions):
            lhs_name = production.lhs.name
            if lhs_name not in productions_by_lhs:
                productions_by_lhs[lhs_name] = []

            rhs_str = " ".join(s.name for s in production.rhs) if production.rhs else "ε"
            productions_by_lhs[lhs_name].append(
                {
                    "index": i,
                    "rhs": rhs_str,
                    "rhs_symbols": [s.name for s in production.rhs],
                    "is_epsilon": len(production.rhs) == 0,
                }
            )

        return {
            "total_productions": len(self.grammar.productions),
            "productions_by_lhs": productions_by_lhs,
            "lhs_symbols": list(productions_by_lhs.keys()),
        }

    def inspect_symbols(self) -> Dict[str, Any]:
        """Inspect all symbols in the grammar."""
        terminals = [s.name for s in self.grammar.terminals]
        non_terminals = [s.name for s in self.grammar.non_terminals]

        return {
            "terminals": terminals,
            "non_terminals": non_terminals,
            "total_terminals": len(terminals),
            "total_non_terminals": len(non_terminals),
            "start_symbol": self.grammar.start_symbol.name,
        }

    def inspect_first_sets(self) -> Dict[str, List[str]]:
        """Inspect FIRST sets for all non-terminals."""
        first_sets = {}

        for nt in self.grammar.non_terminals:
            first_set = self.grammar.first((nt,))
            first_sets[nt.name] = [s.name for s in first_set]

        return first_sets

    def inspect_follow_sets(self) -> Dict[str, List[str]]:
        """Inspect FOLLOW sets for all non-terminals."""
        follow_sets = {}

        for nt in self.grammar.non_terminals:
            follow_set = self.grammar.follow(nt)
            follow_sets[nt.name] = [s.name for s in follow_set]

        return follow_sets

    def inspect_left_recursion(self) -> Dict[str, Any]:
        """Inspect for left recursion."""
        left_recursive = self.grammar._find_left_recursive_symbols()

        return {
            "has_left_recursion": len(left_recursive) > 0,
            "left_recursive_symbols": [s.name for s in left_recursive],
            "is_acceptable_for_lr": True,  # LR parsers can handle left recursion
        }

    def inspect_reachability(self) -> Dict[str, Any]:
        """Inspect symbol reachability."""
        reachable = self.grammar._find_reachable_symbols()
        unreachable = self.grammar.non_terminals - reachable

        return {
            "reachable_symbols": [s.name for s in reachable],
            "unreachable_symbols": [s.name for s in unreachable],
            "has_unreachable": len(unreachable) > 0,
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive grammar inspection report."""
        self.logger.info("Generating grammar inspection report")

        return {
            "grammar_info": {
                "start_symbol": self.grammar.start_symbol.name,
                "total_productions": len(self.grammar.productions),
            },
            "symbols": self.inspect_symbols(),
            "productions": self.inspect_productions(),
            "first_sets": self.inspect_first_sets(),
            "follow_sets": self.inspect_follow_sets(),
            "left_recursion": self.inspect_left_recursion(),
            "reachability": self.inspect_reachability(),
        }


class AutomatonInspector:
    """Inspect and visualize automaton properties."""

    def __init__(self, automaton):
        """Initialize with an automaton."""
        self.automaton = automaton
        self.logger = logging.getLogger(f"{__name__}.AutomatonInspector")

    def inspect_states(self) -> Dict[str, Any]:
        """Inspect all states in the automaton."""
        states_info = []

        for i, state in enumerate(self.automaton.states):
            state_info = {
                "state_number": i,
                "num_items": len(state.items),
                "shift_items": [],
                "reduce_items": [],
                "shift_symbols": [s.name for s in state.get_shift_symbols()],
                "transitions_out": [],
                "transitions_in": [],
            }

            # Categorize items
            for item in state.items:
                item_str = self._format_item(item)
                if item.is_reduce_item:
                    state_info["reduce_items"].append(item_str)
                else:
                    state_info["shift_items"].append(item_str)

            # Get transitions
            for transition in self.automaton.get_transitions_from_state(i):
                state_info["transitions_out"].append(
                    {
                        "to_state": transition.to_state,
                        "symbol": transition.symbol.name,
                        "symbol_type": transition.symbol.symbol_type.value,
                    }
                )

            for transition in self.automaton.get_transitions_to_state(i):
                state_info["transitions_in"].append(
                    {
                        "from_state": transition.from_state,
                        "symbol": transition.symbol.name,
                        "symbol_type": transition.symbol.symbol_type.value,
                    }
                )

            states_info.append(state_info)

        return {"total_states": len(self.automaton.states), "states": states_info}

    def inspect_conflicts(self) -> Dict[str, Any]:
        """Inspect conflicts in the automaton."""
        conflicts = self.automaton.find_conflicts()

        conflict_summary = {"total_conflicts": len(conflicts), "shift_reduce_conflicts": [], "reduce_reduce_conflicts": []}

        for conflict in conflicts:
            conflict_info = {"state": conflict["state"], "symbol": conflict["symbol"]}

            if conflict["type"] == "shift_reduce":
                conflict_info.update(
                    {
                        "shift_transition": conflict.get("shift_transition"),
                        "reduce_item": str(conflict["reduce_item"]),
                        "production_index": conflict.get("production_index"),
                    }
                )
                conflict_summary["shift_reduce_conflicts"].append(conflict_info)
            elif conflict["type"] == "reduce_reduce":
                conflict_info.update(
                    {
                        "reduce_items": [str(item) for item in conflict["reduce_items"]],
                        "production_indices": conflict.get("production_indices", []),
                    }
                )
                conflict_summary["reduce_reduce_conflicts"].append(conflict_info)

        return conflict_summary

    def inspect_grammar_type(self) -> Dict[str, Any]:
        """Inspect the grammar type."""
        grammar_type = self.automaton.get_grammar_type()
        conflicts = self.automaton.find_conflicts()

        return {
            "grammar_type": grammar_type,
            "is_lr1": len(conflicts) == 0,
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
        }

    def _format_item(self, item) -> str:
        """Format an LR(1) item for display."""
        rhs = item.production.rhs
        if not rhs:
            rhs_str = "•ε"
        else:
            rhs_list = []
            for i, symbol in enumerate(rhs):
                if i == item.dot_position:
                    rhs_list.append("•")
                rhs_list.append(symbol.name)
            if item.dot_position == len(rhs):
                rhs_list.append("•")
            rhs_str = " ".join(rhs_list)

        return f"[{item.production.lhs.name} → {rhs_str}, {item.lookahead.name}]"

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive automaton inspection report."""
        self.logger.info("Generating automaton inspection report")

        return {
            "automaton_info": {
                "total_states": len(self.automaton.states),
                "total_transitions": len(self.automaton.transitions),
            },
            "states": self.inspect_states(),
            "conflicts": self.inspect_conflicts(),
            "grammar_type": self.inspect_grammar_type(),
        }


class TableInspector:
    """Inspect and visualize parsing table properties."""

    def __init__(self, parsing_table):
        """Initialize with a parsing table."""
        self.parsing_table = parsing_table
        self.logger = logging.getLogger(f"{__name__}.TableInspector")

    def inspect_action_table(self) -> Dict[str, Any]:
        """Inspect the ACTION table."""
        action_entries = {}
        terminals = set()
        states = set()

        for (state, symbol), action in self.parsing_table.action_table.items():
            terminals.add(symbol)
            states.add(state)

            if state not in action_entries:
                action_entries[state] = {}

            action_entries[state][symbol] = {"type": action.action_type.value, "target": action.target}

        return {
            "total_entries": len(self.parsing_table.action_table),
            "states": sorted(states),
            "terminals": sorted(terminals),
            "entries": action_entries,
        }

    def inspect_goto_table(self) -> Dict[str, Any]:
        """Inspect the GOTO table."""
        goto_entries = {}
        non_terminals = set()
        states = set()

        for (state, symbol), target_state in self.parsing_table.goto_table.items():
            non_terminals.add(symbol)
            states.add(state)

            if state not in goto_entries:
                goto_entries[state] = {}

            goto_entries[state][symbol] = target_state

        return {
            "total_entries": len(self.parsing_table.goto_table),
            "states": sorted(states),
            "non_terminals": sorted(non_terminals),
            "entries": goto_entries,
        }

    def inspect_conflicts(self) -> Dict[str, Any]:
        """Inspect conflicts in the parsing table."""
        conflicts = self.parsing_table.conflicts

        conflict_summary = {"total_conflicts": len(conflicts), "conflicts_by_type": {}, "conflicts_by_state": {}}

        for conflict in conflicts:
            conflict_type = conflict.conflict_type
            state = conflict.state

            if conflict_type not in conflict_summary["conflicts_by_type"]:
                conflict_summary["conflicts_by_type"][conflict_type] = 0
            conflict_summary["conflicts_by_type"][conflict_type] += 1

            if state not in conflict_summary["conflicts_by_state"]:
                conflict_summary["conflicts_by_state"][state] = []

            conflict_summary["conflicts_by_state"][state].append(
                {
                    "symbol": conflict.symbol,
                    "actions": [{"type": action.action_type.value, "target": action.target} for action in conflict.actions],
                    "conflict_type": conflict_type,
                }
            )

        return conflict_summary

    def inspect_table_density(self) -> Dict[str, Any]:
        """Inspect table density and coverage."""
        action_table = self.parsing_table.action_table
        goto_table = self.parsing_table.goto_table

        # Get all states and symbols
        all_states = set()
        all_terminals = set()
        all_non_terminals = set()

        for state, symbol in action_table.keys():
            all_states.add(state)
            all_terminals.add(symbol)

        for state, symbol in goto_table.keys():
            all_states.add(state)
            all_non_terminals.add(symbol)

        # Calculate densities
        action_cells = len(all_states) * len(all_terminals)
        goto_cells = len(all_states) * len(all_non_terminals)

        action_density = len(action_table) / action_cells if action_cells > 0 else 0
        goto_density = len(goto_table) / goto_cells if goto_cells > 0 else 0

        return {
            "action_table": {"total_cells": action_cells, "filled_cells": len(action_table), "density": action_density},
            "goto_table": {"total_cells": goto_cells, "filled_cells": len(goto_table), "density": goto_density},
            "states": len(all_states),
            "terminals": len(all_terminals),
            "non_terminals": len(all_non_terminals),
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive table inspection report."""
        self.logger.info("Generating table inspection report")

        return {
            "table_info": {
                "has_conflicts": self.parsing_table.has_conflicts(),
                "is_valid": self.parsing_table.is_valid_table(),
            },
            "action_table": self.inspect_action_table(),
            "goto_table": self.inspect_goto_table(),
            "conflicts": self.inspect_conflicts(),
            "density": self.inspect_table_density(),
        }
