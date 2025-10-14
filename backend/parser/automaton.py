"""LR(1) automaton construction (canonical collection of LR(1) item sets)."""

from dataclasses import dataclass

from parser.grammar import Grammar
from parser.items import ItemSet, LR1Item, extend_grammar_with_first, extend_grammar_with_follow
from parser.types import Symbol, SymbolType


@dataclass
class StateTransition:
    """Represents a transition between states in the LR(1) automaton."""

    from_state: int
    to_state: int
    symbol: Symbol

    def __str__(self) -> str:
        """Return string representation of the transition."""
        return f"State {self.from_state} --{self.symbol}--> State {self.to_state}"


class Automaton:
    """Represents the LR(1) automaton (canonical collection of LR(1) item sets)."""

    def __init__(self, grammar: Grammar) -> None:
        """Initialize and build the LR(1) automaton from the grammar."""
        self.grammar = grammar
        self.states: list[ItemSet] = []
        self.transitions: list[StateTransition] = []
        self.state_map: dict[ItemSet, int] = {}  # Maps item sets to state numbers

        self._build_automaton()

    def _build_automaton(self) -> None:
        """Build the canonical collection of LR(1) item sets."""
        # Add FIRST and FOLLOW computation to grammar if not already present
        if not hasattr(self.grammar, "first"):
            self._add_first_computation()
        if not hasattr(self.grammar, "follow"):
            self._add_follow_computation()

        # Create initial item set with [S' -> ·S, $]
        start_production = self.grammar.productions[0]  # Augmented production
        end_marker = Symbol("$", SymbolType.TERMINAL)

        initial_item = LR1Item(
            production=start_production,
            dot_position=0,
            lookahead=end_marker,
        )

        initial_item_set = ItemSet.from_initial_item(initial_item, self.grammar)

        # Initialize states with the initial item set
        self.states = [initial_item_set]
        self.state_map[initial_item_set] = 0

        # Build states using worklist algorithm
        worklist = [0]  # Queue of state indices to process

        while worklist:
            state_index = worklist.pop(0)
            current_state = self.states[state_index]

            # Get all symbols that can be shifted from this state
            shift_symbols = current_state.get_shift_symbols()

            for symbol in shift_symbols:
                # Compute GOTO(current_state, symbol)
                goto_state = current_state.goto(self.grammar, symbol)

                if goto_state is not None:
                    # Check if we've seen this item set before
                    if goto_state in self.state_map:
                        # Existing state
                        target_state_index = self.state_map[goto_state]
                    else:
                        # New state
                        target_state_index = len(self.states)
                        self.states.append(goto_state)
                        self.state_map[goto_state] = target_state_index
                        worklist.append(target_state_index)

                    # Add transition
                    transition = StateTransition(
                        from_state=state_index,
                        to_state=target_state_index,
                        symbol=symbol,
                    )
                    self.transitions.append(transition)

    def _add_first_computation(self) -> None:
        """Add FIRST computation methods to the grammar."""
        extend_grammar_with_first(self.grammar)

    def _add_follow_computation(self) -> None:
        """Add FOLLOW computation methods to the grammar."""
        extend_grammar_with_follow(self.grammar)

    def get_state_number(self, item_set: ItemSet) -> int | None:
        """Get the state number for a given item set."""
        return self.state_map.get(item_set)

    def get_transitions_from_state(self, state_index: int) -> list[StateTransition]:
        """Get all transitions from a given state."""
        return [t for t in self.transitions if t.from_state == state_index]

    def get_transitions_to_state(self, state_index: int) -> list[StateTransition]:
        """Get all transitions to a given state."""
        return [t for t in self.transitions if t.to_state == state_index]

    def get_transition(
        self,
        from_state: int,
        symbol: Symbol,
    ) -> StateTransition | None:
        """Get the transition for a given state and symbol."""
        for transition in self.transitions:
            if transition.from_state == from_state and transition.symbol == symbol:
                return transition
        return None

    def get_state_info(self, state_index: int) -> dict:
        """Get detailed information about a state."""
        if state_index >= len(self.states):
            return {}

        state = self.states[state_index]

        # Separate items by type
        shift_items = []
        reduce_items = []

        for item in state.items:
            if item.is_reduce_item:
                reduce_items.append(item)
            else:
                shift_items.append(item)

        # Get possible actions
        shift_symbols = state.get_shift_symbols()

        return {
            "state_index": state_index,
            "items": list(state.items),
            "shift_items": shift_items,
            "reduce_items": reduce_items,
            "shift_symbols": shift_symbols,
            "transitions_out": self.get_transitions_from_state(state_index),
            "transitions_in": self.get_transitions_to_state(state_index),
        }

    def find_conflicts(self) -> list[dict]:
        """Find conflicts in the automaton (shift-reduce and reduce-reduce)."""
        conflicts = []

        for state_index, state in enumerate(self.states):
            reduce_items = state.get_reduce_items()
            shift_symbols = state.get_shift_symbols()

            # Check for shift-reduce conflicts
            shift_reduce_conflicts = [
                {
                    "type": "shift_reduce",
                    "state": state_index,
                    "symbol": symbol,
                    "shift_transition": self.get_transition(
                        state_index,
                        symbol,
                    ),
                    "reduce_item": reduce_item,
                    "production_index": self.grammar.productions.index(
                        reduce_item.production,
                    ),
                }
                for symbol in shift_symbols
                for reduce_item in reduce_items
                if reduce_item.lookahead == symbol
            ]
            conflicts.extend(shift_reduce_conflicts)

            # Check for reduce-reduce conflicts
            if len(reduce_items) > 1:
                # Group reduce items by lookahead
                lookahead_groups = {}
                for item in reduce_items:
                    lookahead = item.lookahead
                    if lookahead not in lookahead_groups:
                        lookahead_groups[lookahead] = []
                    lookahead_groups[lookahead].append(item)

                # Check for multiple reduce items with same lookahead
                for lookahead, items in lookahead_groups.items():
                    if len(items) > 1:
                        conflicts.append(
                            {
                                "type": "reduce_reduce",
                                "state": state_index,
                                "symbol": lookahead,
                                "reduce_items": items,
                                "production_indices": [self.grammar.productions.index(item.production) for item in items],
                            },
                        )

        return conflicts

    def is_lr1_grammar(self) -> bool:
        """Check if the grammar is LR(1) by checking for conflicts."""
        conflicts = self.find_conflicts()
        return len(conflicts) == 0

    def get_grammar_type(self) -> str:
        """Determine the grammar type based on conflicts."""
        conflicts = self.find_conflicts()

        if not conflicts:
            return "LR(1)"

        conflict_types = {conflict["type"] for conflict in conflicts}

        if "reduce_reduce" in conflict_types:
            return "Not LR(k) for any k"
        if "shift_reduce" in conflict_types:
            return "LALR(1) or SLR(1) (has shift-reduce conflicts)"
        return "Unknown"

    def __str__(self) -> str:
        """Return string representation of the automaton."""
        lines = []
        lines.append("LR(1) Automaton:")
        lines.append(f"Number of states: {len(self.states)}")
        lines.append(f"Number of transitions: {len(self.transitions)}")
        lines.append("")

        for i, state in enumerate(self.states):
            lines.append(f"State {i}:")
            lines.append(str(state))
            lines.append("")

        lines.append("Transitions:")
        lines.extend(str(transition) for transition in self.transitions)

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Return string representation of the automaton."""
        return f"Automaton({len(self.states)} states, {len(self.transitions)} transitions)"
