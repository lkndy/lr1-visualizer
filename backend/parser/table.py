"""LR(1) parsing table generation (ACTION and GOTO tables)."""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from parser.types import ActionType, ParsingAction, ConflictInfo, Symbol, SymbolType


class ParsingTable:
    """Represents the LR(1) parsing tables (ACTION and GOTO)."""
    
    def __init__(self, automaton):
        """Generate parsing tables from the LR(1) automaton."""
        self.automaton = automaton
        self.grammar = automaton.grammar
        self.action_table: Dict[Tuple[int, str], ParsingAction] = {}
        self.goto_table: Dict[Tuple[int, str], int] = {}
        self.conflicts: List[ConflictInfo] = []
        
        self._build_tables()
    
    def _build_tables(self):
        """Build the ACTION and GOTO tables."""
        # Initialize tables
        self.action_table = {}
        self.goto_table = {}
        
        # Get all terminals and non-terminals
        terminals = set(self.grammar.terminals)
        non_terminals = set(self.grammar.non_terminals)
        
        # Ensure end-of-input marker '$' is a terminal for ACTION lookups
        if all(symbol.name != "$" for symbol in terminals):
            terminals.add(Symbol("$", SymbolType.TERMINAL))
        
        # Build ACTION and GOTO tables
        for state_index, state in enumerate(self.automaton.states):
            # Handle reduce items
            reduce_items = state.get_reduce_items()
            for item in reduce_items:
                lookahead = item.lookahead
                
                if item.production == self.grammar.productions[0]:  # S' -> S·
                    # Accept action
                    action = ParsingAction(
                        action_type=ActionType.ACCEPT,
                        target=None
                    )
                    key = (state_index, lookahead.name)
                    
                    if key in self.action_table:
                        # Conflict - already have an action for this state/lookahead
                        existing_action = self.action_table[key]
                        self.conflicts.append(ConflictInfo(
                            state=state_index,
                            symbol=lookahead.name,
                            actions=[existing_action, action],
                            conflict_type="accept_conflict"
                        ))
                    else:
                        self.action_table[key] = action
                else:
                    # Reduce action
                    production_index = self.grammar.productions.index(item.production)
                    action = ParsingAction(
                        action_type=ActionType.REDUCE,
                        target=production_index
                    )
                    key = (state_index, lookahead.name)
                    
                    if key in self.action_table:
                        # Conflict
                        existing_action = self.action_table[key]
                        self.conflicts.append(ConflictInfo(
                            state=state_index,
                            symbol=lookahead.name,
                            actions=[existing_action, action],
                            conflict_type="shift_reduce" if existing_action.action_type == ActionType.SHIFT else "reduce_reduce"
                        ))
                    else:
                        self.action_table[key] = action
            
            # Handle shift actions
            for transition in self.automaton.get_transitions_from_state(state_index):
                if transition.symbol.symbol_type.name == "TERMINAL":
                    action = ParsingAction(
                        action_type=ActionType.SHIFT,
                        target=transition.to_state
                    )
                    key = (state_index, transition.symbol.name)
                    
                    if key in self.action_table:
                        # Conflict
                        existing_action = self.action_table[key]
                        self.conflicts.append(ConflictInfo(
                            state=state_index,
                            symbol=transition.symbol.name,
                            actions=[existing_action, action],
                            conflict_type="shift_reduce" if existing_action.action_type == ActionType.REDUCE else "shift_shift"
                        ))
                    else:
                        self.action_table[key] = action
            
            # Build GOTO table
            for transition in self.automaton.get_transitions_from_state(state_index):
                if transition.symbol.symbol_type.name == "NON_TERMINAL":
                    key = (state_index, transition.symbol.name)
                    self.goto_table[key] = transition.to_state
    
    def get_action(self, state: int, symbol: str) -> Optional[ParsingAction]:
        """Get the action for a given state and terminal symbol."""
        key = (state, symbol)
        return self.action_table.get(key)
    
    def get_goto(self, state: int, non_terminal: str) -> Optional[int]:
        """Get the GOTO state for a given state and non-terminal symbol."""
        key = (state, non_terminal)
        return self.goto_table.get(key)
    
    def has_conflicts(self) -> bool:
        """Check if the parsing table has conflicts."""
        return len(self.conflicts) > 0
    
    def is_valid_table(self) -> bool:
        """Check if the parsing table is valid (no conflicts)."""
        return not self.has_conflicts()
    
    def get_conflict_summary(self) -> Dict:
        """Get a summary of all conflicts in the table."""
        conflict_types = {}
        for conflict in self.conflicts:
            conflict_type = conflict.conflict_type
            if conflict_type not in conflict_types:
                conflict_types[conflict_type] = []
            conflict_types[conflict_type].append({
                "state": conflict.state,
                "symbol": conflict.symbol,
                "actions": [
                    {
                        "type": action.action_type.value,
                        "target": action.target
                    } for action in conflict.actions
                ]
            })
        
        return {
            "total_conflicts": len(self.conflicts),
            "conflict_types": conflict_types,
            "is_lr1": len(self.conflicts) == 0
        }
    
    def get_table_summary(self) -> Dict:
        """Get a summary of the parsing table."""
        terminals = set()
        non_terminals = set()
        
        for key in self.action_table.keys():
            terminals.add(key[1])
        
        for key in self.goto_table.keys():
            non_terminals.add(key[1])
        
        return {
            "num_states": len(self.automaton.states),
            "num_terminals": len(terminals),
            "num_non_terminals": len(non_terminals),
            "action_entries": len(self.action_table),
            "goto_entries": len(self.goto_table),
            "has_conflicts": self.has_conflicts(),
            "conflicts": self.get_conflict_summary()
        }
    
    def export_action_table(self) -> Dict:
        """Export ACTION table in a format suitable for frontend display."""
        # Get all unique states and symbols
        states = set()
        symbols = set()
        
        for key in self.action_table.keys():
            states.add(key[0])
            symbols.add(key[1])
        
        states = sorted(list(states))
        symbols = sorted(list(symbols))
        
        # Create table structure
        table = {
            "headers": ["State"] + symbols,
            "rows": []
        }
        
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
                        row.append("err")
                else:
                    row.append("")
            table["rows"].append(row)
        
        return table
    
    def export_goto_table(self) -> Dict:
        """Export GOTO table in a format suitable for frontend display."""
        # Get all unique states and non-terminals
        states = set()
        non_terminals = set()
        
        for key in self.goto_table.keys():
            states.add(key[0])
            non_terminals.add(key[1])
        
        states = sorted(list(states))
        non_terminals = sorted(list(non_terminals))
        
        # Create table structure
        table = {
            "headers": ["State"] + non_terminals,
            "rows": []
        }
        
        for state in states:
            row = [f"State {state}"]
            for non_terminal in non_terminals:
                key = (state, non_terminal)
                goto_state = self.goto_table.get(key)
                if goto_state is not None:
                    row.append(str(goto_state))
                else:
                    row.append("")
            table["rows"].append(row)
        
        return table
    
    def __str__(self) -> str:
        """String representation of the parsing table."""
        lines = []
        lines.append("ACTION Table:")
        
        # Get all unique states and symbols for ACTION table
        states = set()
        symbols = set()
        for key in self.action_table.keys():
            states.add(key[0])
            symbols.add(key[1])
        
        states = sorted(list(states))
        symbols = sorted(list(symbols))
        
        # Print header
        header = "State".ljust(8)
        for symbol in symbols:
            header += symbol.ljust(8)
        lines.append(header)
        
        # Print rows
        for state in states:
            row = f"{state}".ljust(8)
            for symbol in symbols:
                key = (state, symbol)
                action = self.action_table.get(key)
                if action:
                    if action.action_type == ActionType.SHIFT:
                        cell = f"s{action.target}"
                    elif action.action_type == ActionType.REDUCE:
                        cell = f"r{action.target}"
                    elif action.action_type == ActionType.ACCEPT:
                        cell = "acc"
                    else:
                        cell = "err"
                else:
                    cell = ""
                row += cell.ljust(8)
            lines.append(row)
        
        lines.append("")
        lines.append("GOTO Table:")
        
        # Get all unique states and non-terminals for GOTO table
        states = set()
        non_terminals = set()
        for key in self.goto_table.keys():
            states.add(key[0])
            non_terminals.add(key[1])
        
        states = sorted(list(states))
        non_terminals = sorted(list(non_terminals))
        
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
                if goto_state is not None:
                    cell = str(goto_state)
                else:
                    cell = ""
                row += cell.ljust(8)
            lines.append(row)
        
        if self.conflicts:
            lines.append("")
            lines.append("Conflicts:")
            for conflict in self.conflicts:
                lines.append(f"  State {conflict.state}, Symbol '{conflict.symbol}': {conflict.conflict_type}")
                for action in conflict.actions:
                    lines.append(f"    - {action.action_type.value} {action.target}")
        
        return "\n".join(lines)
