"""LR(1) parsing table generation (ACTION and GOTO tables)."""

from parser.automaton import Automaton
from parser.items import ItemSet, LR1Item
from parser.types import ActionType, ConflictInfo, ParsingAction, SymbolType


class ParsingTable:
    """Represents the LR(1) parsing tables (ACTION and GOTO)."""

    def __init__(self, automaton: Automaton) -> None:
        """Generate parsing tables from the LR(1) automaton."""
        self.automaton = automaton
        self.grammar = automaton.grammar
        self.action_table: dict[tuple[int, str], ParsingAction] = {}
        self.goto_table: dict[tuple[int, str], int] = {}
        self.conflicts: list[ConflictInfo] = []

        self._build_tables()

    def _build_tables(self) -> None:
        """Build the ACTION and GOTO tables."""
        self.action_table = {}
        self.goto_table = {}

        for state_index, state in enumerate(self.automaton.states):
            self._process_reduce_items(state_index, state)
            self._process_shift_actions(state_index)
            self._process_goto_transitions(state_index)

    def _process_reduce_items(self, state_index: int, state: ItemSet) -> None:
        """Process reduce items for a given state."""
        reduce_items = state.get_reduce_items()
        for item in reduce_items:
            lookahead = item.lookahead

            if item.production == self.grammar.productions[0]:  # S' -> S·
                self._add_accept_action(state_index, lookahead.name)
            else:
                self._add_reduce_action(state_index, item, lookahead.name)

    def _add_accept_action(self, state_index: int, lookahead: str) -> None:
        """Add accept action to the action table."""
        action = ParsingAction(action_type=ActionType.ACCEPT, target=None)
        key = (state_index, lookahead)

        if key in self.action_table:
            existing_action = self.action_table[key]
            self._add_conflict(state_index, lookahead, existing_action, action, "accept_conflict")
        else:
            self.action_table[key] = action

    def _add_reduce_action(self, state_index: int, item: LR1Item, lookahead: str) -> None:
        """Add reduce action to the action table."""
        production_index = self.grammar.productions.index(item.production)
        action = ParsingAction(action_type=ActionType.REDUCE, target=production_index)
        key = (state_index, lookahead)

        if key in self.action_table:
            existing_action = self.action_table[key]
            conflict_type = "shift_reduce" if existing_action.action_type == ActionType.SHIFT.value else "reduce_reduce"
            self._add_conflict(state_index, lookahead, existing_action, action, conflict_type)
        else:
            self.action_table[key] = action

    def _process_shift_actions(self, state_index: int) -> None:
        """Process shift actions for a given state."""
        for transition in self.automaton.get_transitions_from_state(state_index):
            if transition.symbol.symbol_type == SymbolType.TERMINAL:
                action = ParsingAction(action_type=ActionType.SHIFT, target=transition.to_state)
                key = (state_index, transition.symbol.name)

                if key in self.action_table:
                    existing_action = self.action_table[key]
                    conflict_type = "shift_reduce" if existing_action.action_type == ActionType.REDUCE.value else "shift_shift"
                    self._add_conflict(state_index, transition.symbol.name, existing_action, action, conflict_type)
                else:
                    self.action_table[key] = action

    def _process_goto_transitions(self, state_index: int) -> None:
        """Process GOTO transitions for a given state."""
        for transition in self.automaton.get_transitions_from_state(state_index):
            if transition.symbol.symbol_type == SymbolType.NON_TERMINAL:
                key = (state_index, transition.symbol.name)
                self.goto_table[key] = transition.to_state

    def _add_conflict(
        self,
        state_index: int,
        symbol: str,
        existing_action: ParsingAction,
        new_action: ParsingAction,
        conflict_type: str,
    ) -> None:
        """Add a conflict to the conflicts list."""
        self.conflicts.append(
            ConflictInfo(
                state=state_index,
                symbol=symbol,
                actions=[existing_action, new_action],
                conflict_type=conflict_type,
            ),
        )

    def get_action(self, state: int, symbol: str) -> ParsingAction | None:
        """Get the action for a given state and terminal symbol."""
        key = (state, symbol)
        return self.action_table.get(key)

    def get_goto(self, state: int, non_terminal: str) -> int | None:
        """Get the GOTO state for a given state and non-terminal symbol."""
        key = (state, non_terminal)
        return self.goto_table.get(key)

    def has_conflicts(self) -> bool:
        """Check if the parsing table has conflicts."""
        return len(self.conflicts) > 0

    def is_valid_table(self) -> bool:
        """Check if the parsing table is valid (no conflicts)."""
        return not self.has_conflicts()

    def get_conflict_summary(self) -> dict:
        """Get a summary of all conflicts in the table."""
        conflict_types = {}
        for conflict in self.conflicts:
            conflict_type = conflict.conflict_type
            if conflict_type not in conflict_types:
                conflict_types[conflict_type] = []
            conflict_types[conflict_type].append(
                {
                    "state": conflict.state,
                    "symbol": conflict.symbol,
                    "actions": [{"type": action.action_type, "target": action.target} for action in conflict.actions],
                },
            )

        return {
            "total_conflicts": len(self.conflicts),
            "conflict_types": conflict_types,
            "is_lr1": len(self.conflicts) == 0,
        }

    def get_table_summary(self) -> dict:
        """Get a summary of the parsing table."""
        terminals = set()
        non_terminals = set()

        for key in self.action_table:
            terminals.add(key[1])

        for key in self.goto_table:
            non_terminals.add(key[1])

        return {
            "num_states": len(self.automaton.states),
            "num_terminals": len(terminals),
            "num_non_terminals": len(non_terminals),
            "action_entries": len(self.action_table),
            "goto_entries": len(self.goto_table),
            "has_conflicts": self.has_conflicts(),
            "conflicts": self.get_conflict_summary(),
        }

    def export_action_table(self) -> dict:
        """Export ACTION table in a format suitable for frontend display."""
        # Collect all states and terminal symbols
        states = set()
        symbols = set()
        for state, symbol_name in self.action_table.keys():
            states.add(state)
            symbols.add(symbol_name)

        # Ensure '$' is in symbols if it's a terminal
        if self.automaton.grammar.end_of_input in [s.name for s in self.automaton.grammar.terminals]:
            symbols.add(self.automaton.grammar.end_of_input)

        states = sorted(list(states))
        symbols = sorted(list(symbols))

        # Create table structure
        table = {"headers": ["State", *symbols], "rows": []}

        for state in states:
            row = [f"State {state}"]
            for symbol in symbols:
                key = (state, symbol)
                action = self.action_table.get(key)
                if action:
                    if action.action_type == ActionType.SHIFT:
                        row.append(f"s{action.target}")
                    elif action.action_type == ActionType.REDUCE:
                        row.append(f"r{action.target}")
                    elif action.action_type == ActionType.ACCEPT:
                        row.append("acc")
                    else:
                        row.append("")  # Error actions show as empty, not "err"
                else:
                    row.append("")
            table["rows"].append(row)

        return table

    def export_goto_table(self) -> dict:
        """Export GOTO table in a format suitable for frontend display."""
        # Get all unique states and non-terminals
        states = set()
        non_terminals = set()

        for key in self.goto_table:
            states.add(key[0])
            non_terminals.add(key[1])

        states = sorted(states)
        non_terminals = sorted(non_terminals)

        # Create table structure
        table = {"headers": ["State", *non_terminals], "rows": []}

        for state in states:
            row = [f"State {state}"]
            for non_terminal in non_terminals:
                key = (state, non_terminal)
                goto_state = self.goto_table.get(key)
                row.append(str(goto_state) if goto_state is not None else "")
            table["rows"].append(row)

        return table

    def __str__(self) -> str:
        """Return string representation of the parsing table."""
        lines = []
        lines.extend(self._format_action_table())
        lines.extend(self._format_goto_table())
        lines.extend(self._format_conflicts())
        return "\n".join(lines)

    def _format_action_table(self) -> list[str]:
        """Format the ACTION table as a list of strings."""
        lines = ["ACTION Table:"]

        states, symbols = self._get_action_table_keys()

        # Print header
        header = "State".ljust(8)
        for symbol in symbols:
            header += symbol.ljust(8)
        lines.append(header)

        # Print rows
        for state in states:
            row = f"{state}".ljust(8)
            for symbol in symbols:
                cell = self._format_action_cell(state, symbol)
                row += cell.ljust(8)
            lines.append(row)

        return lines

    def _format_goto_table(self) -> list[str]:
        """Format the GOTO table as a list of strings."""
        lines = ["", "GOTO Table:"]

        states, non_terminals = self._get_goto_table_keys()

        # Print header
        header = "State".ljust(8)
        for non_terminal in non_terminals:
            header += non_terminal.ljust(8)
        lines.append(header)

        # Print rows
        for state in states:
            row = f"{state}".ljust(8)
            for non_terminal in non_terminals:
                key = (state, non_terminal)
                goto_state = self.goto_table.get(key)
                cell = str(goto_state) if goto_state is not None else ""
                row += cell.ljust(8)
            lines.append(row)

        return lines

    def _format_conflicts(self) -> list[str]:
        """Format conflicts as a list of strings."""
        if not self.conflicts:
            return []

        lines = ["", "Conflicts:"]
        for conflict in self.conflicts:
            lines.append(f"  State {conflict.state}, Symbol '{conflict.symbol}': {conflict.conflict_type}")
            lines.extend([f"    - {action.action_type.value} {action.target}" for action in conflict.actions])

        return lines

    def _get_action_table_keys(self) -> tuple[list[int], list[str]]:
        """Get sorted states and symbols from action table."""
        states = set()
        symbols = set()
        for key in self.action_table:
            states.add(key[0])
            symbols.add(key[1])
        return sorted(states), sorted(symbols)

    def _get_goto_table_keys(self) -> tuple[list[int], list[str]]:
        """Get sorted states and non-terminals from goto table."""
        states = set()
        non_terminals = set()
        for key in self.goto_table:
            states.add(key[0])
            non_terminals.add(key[1])
        return sorted(states), sorted(non_terminals)

    def _format_action_cell(self, state: int, symbol: str) -> str:
        """Format a single action table cell."""
        key = (state, symbol)
        action = self.action_table.get(key)

        if not action:
            return ""

        match action.action_type:
            case ActionType.SHIFT:
                return f"s{action.target}"
            case ActionType.REDUCE:
                return f"r{action.target}"
            case ActionType.ACCEPT:
                return "acc"
            case _:
                return "err"
