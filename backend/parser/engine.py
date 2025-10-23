"""LR(1) parsing engine for step-by-step execution and AST building."""

from dataclasses import dataclass
from typing import Any

from parser.grammar_v2 import Grammar
from parser.table import ParsingTable
from parser.types import ActionType, ASTNode, ParsingAction, ParsingStep, Production, SymbolType


@dataclass
class ParseState:
    """Represents the current state of the parser."""

    stack: list[tuple[int, str]]  # (state, symbol)
    input_tokens: list[str]
    input_pointer: int
    step_number: int
    ast_nodes: dict[str, ASTNode]  # node_id -> ASTNode
    ast_stack: list[str]  # Stack of AST node IDs corresponding to parser stack
    next_node_id: int


class ParserEngine:
    """LR(1) parsing engine for step-by-step execution."""

    def __init__(self, grammar: Grammar, parsing_table: ParsingTable) -> None:
        """Initialize parser engine with grammar and parsing table."""
        self.grammar = grammar
        self.parsing_table = parsing_table
        self.automaton = parsing_table.automaton

        # Validate that table is conflict-free
        if parsing_table.has_conflicts():
            msg = "Cannot create parser with conflicting parsing table"
            raise ValueError(msg)

    def parse(self, input_string: str) -> list[ParsingStep]:
        """Parse input string and return list of all parsing steps."""
        tokens = self._tokenize(input_string)
        return self._parse_tokens(tokens)

    def parse_interactive(self, input_string: str) -> dict[str, Any]:
        """Parse input string and return detailed interactive derivation information."""
        tokens = self._tokenize(input_string)
        steps = self._parse_tokens(tokens)
        print("TOKENS:", tokens)
        print("LAST ACTION:", steps[-1].action.action_type if steps else None)
        # Build final AST from all steps
        final_ast = self.get_ast(steps)

        # Create detailed derivation information
        derivation_info = {
            "input_string": input_string,
            "tokens": tokens,
            "total_steps": len(steps),
            "success": len(steps) > 0 and steps[-1].action.action_type == ActionType.ACCEPT.value,
            "steps": [],
            "ast": final_ast,  # Add the complete AST here
        }

        for i, step in enumerate(steps):
            step_info = {
                "step_number": i + 1,
                "stack": step.stack.copy(),
                "input_remaining": tokens[step.input_pointer :] if step.input_pointer < len(tokens) else [],
                "current_token": step.current_token,
                "action": {
                    "type": step.action.action_type,
                    "target": step.action.target,
                    "description": self._get_action_description(step.action),
                },
                "explanation": step.explanation,
                "ast_nodes": step.ast_nodes.copy() if step.ast_nodes else [],
                "derivation_so_far": self._get_derivation_so_far(step.stack, step.ast_nodes),
            }
            derivation_info["steps"].append(step_info)

        return derivation_info

    def _get_action_description(self, action: ParsingAction) -> str:
        """Get a human-readable description of the parsing action."""
        if action.action_type == ActionType.SHIFT.value:
            return f"Shift to state {action.target}"
        elif action.action_type == ActionType.REDUCE.value:
            production = self.grammar.productions[action.target]
            return f"Reduce by {production.lhs.name} → {' '.join(str(s) for s in production.rhs) if production.rhs else 'ε'}"
        elif action.action_type == ActionType.ACCEPT.value:
            return "Accept - parsing complete"
        else:
            return "Error"

    def _get_derivation_so_far(self, stack: list[tuple[int, str]], ast_nodes: list[dict[str, Any]]) -> str:
        """Get the current derivation string from the stack and AST nodes."""
        if not stack:
            return ""

        # Get the top of the stack (current state and symbol)
        current_state, current_symbol = stack[-1]

        # If we have AST nodes, try to build a derivation from them
        if ast_nodes:
            # Find the root node (the one that's not a child of any other)
            root_nodes = [node for node in ast_nodes if not any(node["id"] in other.get("children", []) for other in ast_nodes)]
            if root_nodes:
                return self._build_derivation_from_ast(root_nodes[0], ast_nodes)

        # Fallback: return the current symbol
        return current_symbol

    def _build_derivation_from_ast(self, root_node: dict[str, Any], all_nodes: list[dict[str, Any]]) -> str:
        """Build a derivation string from the AST nodes."""
        if not root_node:
            return ""

        # If it's a terminal, return its value
        if root_node.get("symbol_type") == "terminal":
            return root_node.get("symbol", "")

        # If it's a non-terminal, build from children
        children = root_node.get("children", [])
        if not children:
            return root_node.get("symbol", "")

        # Get child nodes
        child_nodes = [node for node in all_nodes if node["id"] in children]
        child_nodes.sort(key=lambda x: children.index(x["id"]))

        # Build derivation from children
        parts = []
        for child in child_nodes:
            child_derivation = self._build_derivation_from_ast(child, all_nodes)
            if child_derivation:
                parts.append(child_derivation)

        return " ".join(parts) if parts else root_node.get("symbol", "")

    def _tokenize(self, input_string: str) -> list[str]:
        """Tokenize input string based on grammar terminals."""
        # Simple tokenization - split on whitespace and handle special characters
        tokens = []
        current_token = ""

        i = 0
        while i < len(input_string):
            char = input_string[i]

            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            elif char in "()[]{}+-*/=<>!&|":
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append(char)
            else:
                current_token += char

            i += 1

        if current_token:
            tokens.append(current_token)

        # Add end marker
        tokens.append("$")

        return tokens

    def _parse_tokens(self, tokens: list[str]) -> list[ParsingStep]:
        """Parse token list and return all parsing steps."""
        steps = []

        # Initialize parse state
        parse_state = ParseState(
            stack=[(0, "")],  # Start with state 0 and empty symbol
            input_tokens=tokens,
            input_pointer=0,
            step_number=0,
            ast_nodes={},
            ast_stack=[],  # Track AST nodes corresponding to stack
            next_node_id=0,
        )

        max_steps = len(tokens) * 10  # Safety limit to prevent infinite loops
        step_count = 0

        while step_count < max_steps:
            step = self._execute_step(parse_state)
            steps.append(step)
              # DEBUG
            print(
                f"[STEP {step.step_number}] action={step.action.action_type} "
                f"target={step.action.target} token={step.current_token} "
                f"stack={step.stack} ip={step.input_pointer} ast_nodes_created={step.ast_nodes}"
            )
            step_count += 1

            if step.action.action_type in (ActionType.ACCEPT.value, ActionType.ERROR.value):
                break

            # Update parse state for next iteration
            parse_state = self._update_parse_state(parse_state, step)

        # If we hit the limit, add an error step
        if step_count >= max_steps:
            error_step = ParsingStep(
                step_number=step_count,
                stack=parse_state.stack.copy(),
                input_pointer=parse_state.input_pointer,
                current_token=parse_state.input_tokens[parse_state.input_pointer]
                if parse_state.input_pointer < len(parse_state.input_tokens)
                else None,
                action=ParsingAction(action_type=ActionType.ERROR, target=None),
                explanation="Error: Maximum parsing steps exceeded - possible infinite loop",
                ast_nodes=[],
            )
            steps.append(error_step)

        return steps

    def _execute_step(self, parse_state: ParseState) -> ParsingStep:
        """Execute one parsing step and return the step information."""
        current_state = parse_state.stack[-1][0] if parse_state.stack else 0
        current_token = None
        action = None
        explanation = ""
        ast_nodes_created = []

        if parse_state.input_pointer < len(parse_state.input_tokens):
            current_token = parse_state.input_tokens[parse_state.input_pointer]
            action = self.parsing_table.get_action(
                current_state,
                current_token,
            )

        if action is None:
            action = ParsingAction(action_type=ActionType.ERROR, target=None)
            explanation = f"No action defined for state {current_state} and symbol '{current_token}'"
        elif action.action_type == ActionType.SHIFT.value:
            explanation = f"Shift: Move to state {action.target} and push '{current_token}' onto stack"
            ast_nodes_created = self._handle_shift(
                parse_state,
                current_token,
                action.target,
            )

        elif action.action_type == ActionType.REDUCE.value:
            production = self.grammar.productions[action.target]
            explanation = f"Reduce: Apply production {production}"
            ast_nodes_created = self._handle_reduce(
                parse_state,
                production,
                action.target,
            )

        elif action.action_type == ActionType.ACCEPT.value:
            explanation = "Accept: Input successfully parsed"

        else:
            explanation = "Error: Invalid action"

        return ParsingStep(
            step_number=parse_state.step_number,
            stack=parse_state.stack.copy(),
            input_pointer=parse_state.input_pointer,
            current_token=current_token,
            action=action,
            explanation=explanation,
            ast_nodes=ast_nodes_created,
        )

    def _handle_shift(self, parse_state: ParseState, token: str, target_state: int) -> list[dict[str, Any]]:
        """Handle shift action and return created AST nodes."""
        ast_nodes_created = []
        _ = target_state  # Unused parameter

        # Create AST node for terminal
        node_id = f"node_{parse_state.next_node_id}"
        parse_state.next_node_id += 1

        ast_node = ASTNode(
            id=node_id,
            symbol=token,
            symbol_type=SymbolType.TERMINAL,
            children=[],
            parent=None,
            production_used=None,
        )

        parse_state.ast_nodes[node_id] = ast_node
        parse_state.ast_stack.append(node_id)  # Track node on AST stack
        
        # Use model_dump() instead of dict() for Pydantic v2 compatibility
        ast_nodes_created.append(ast_node.model_dump())

        return ast_nodes_created

    def _handle_reduce(self, parse_state: ParseState, production: Production, production_index: int) -> list[dict[str, Any]]:
        """Handle reduce action and return created AST nodes."""
        ast_nodes_created = []

        # Create AST node for non-terminal
        node_id = f"node_{parse_state.next_node_id}"
        parse_state.next_node_id += 1

        # Get child nodes from AST stack (corresponding to RHS of production)
        rhs_length = len(production.rhs)
        child_node_ids = []
        
        if rhs_length > 0:
            # Get child nodes from the top of AST stack
            child_node_ids = parse_state.ast_stack[-rhs_length:] if len(parse_state.ast_stack) >= rhs_length else []
            # Remove them from AST stack
            parse_state.ast_stack = parse_state.ast_stack[:-rhs_length] if len(parse_state.ast_stack) >= rhs_length else []

        ast_node = ASTNode(
            id=node_id,
            symbol=production.lhs.name,
            symbol_type=SymbolType.NON_TERMINAL,
            children=child_node_ids.copy(),
            parent=None,
            production_used=production_index,
        )

        # Update parent relationships
        for child_id in child_node_ids:
            if child_id in parse_state.ast_nodes:
                child_node = parse_state.ast_nodes[child_id]
                # Create updated node with parent set
                updated_child = ASTNode(
                    id=child_node.id,
                    symbol=child_node.symbol,
                    symbol_type=child_node.symbol_type,
                    children=child_node.children,
                    parent=node_id,
                    production_used=child_node.production_used,
                )
                parse_state.ast_nodes[child_id] = updated_child

        parse_state.ast_nodes[node_id] = ast_node
        parse_state.ast_stack.append(node_id)  # Add new node to AST stack
        
        # Use model_dump() instead of dict() for Pydantic v2 compatibility
        ast_nodes_created.append(ast_node.model_dump())

        return ast_nodes_created

    def _update_parse_state(self, parse_state: ParseState, step: ParsingStep) -> ParseState:
        """Update parse state after executing a step."""
        # Create a new parse state without deep copying to avoid circular references
        new_parse_state = ParseState(
            stack=parse_state.stack.copy(),
            input_tokens=parse_state.input_tokens.copy(),
            input_pointer=parse_state.input_pointer,
            step_number=parse_state.step_number + 1,
            ast_nodes=parse_state.ast_nodes.copy(),
            ast_stack=parse_state.ast_stack.copy(),
            next_node_id=parse_state.next_node_id,
        )

        if step.action.action_type == ActionType.SHIFT.value:
            # Push new state and symbol onto stack
            new_parse_state.stack.append((step.action.target, step.current_token))
            new_parse_state.input_pointer += 1

        elif step.action.action_type == ActionType.REDUCE.value:
            # Pop symbols from stack and push new symbol
            production = self.grammar.productions[step.action.target]
            rhs_length = len(production.rhs)

            # Pop RHS length from stack
            for _ in range(rhs_length):
                if new_parse_state.stack:
                    new_parse_state.stack.pop()

            # Get new state from GOTO table
            current_state = new_parse_state.stack[-1][0] if new_parse_state.stack else 0
            new_state = self.parsing_table.get_goto(current_state, production.lhs.name)

            if new_state is not None:
                new_parse_state.stack.append((new_state, production.lhs.name))

        new_parse_state.step_number += 1
        return new_parse_state

    def get_ast(self, steps: list[ParsingStep]) -> dict[str, Any]:
        """Build final AST from parsing steps."""
        print(f"DEBUG: get_ast called with {len(steps)} steps")
        ast_nodes = {}
        
        # Collect all AST nodes from all steps
        for step in steps:
            for node_data in step.ast_nodes:
                ast_nodes[node_data["id"]] = node_data

        # Find root node (should be the start symbol)
        root_id = self._find_root_node(ast_nodes)
        print(f"DEBUG: Root node found: {root_id}") 
        
        result = {
        "nodes": ast_nodes,
        "root": root_id
        }   
        print(f"DEBUG: Returning AST: {result}")
        return result


    def _find_root_node(self, ast_nodes: dict[str, Any]) -> str | None:
        """Find the root node of the AST."""
        start = self.grammar.start_symbol.name
        keys = list(ast_nodes.keys())

        # 1) Buscar en orden inverso la ÚLTIMA reducción del símbolo inicial (p.ej., 'S')
        for node_id in reversed(keys):
            if ast_nodes[node_id]["symbol"] == start:
                return node_id

        # 2) Fallback: último no terminal sin padre y con hijos
        non_terms = {nt.name for nt in self.grammar.non_terminals}
        for node_id in reversed(keys):
            nd = ast_nodes[node_id]
            if nd.get("parent") is None and nd.get("children") and nd["symbol"] in non_terms:
                return node_id

        # 3) Último recurso: último nodo sin padre
        for node_id in reversed(keys):
            if ast_nodes[node_id].get("parent") is None:
                return node_id

        return None


    def validate_input(self, input_string: str) -> dict[str, Any]:
        """Validate input string and return parsing result."""
        try:
            steps = self.parse(input_string)

            if not steps:
                return {
                    "valid": False,
                    "error": "No parsing steps generated",
                    "steps": [],
                }

            last_step = steps[-1]

            if last_step.action.action_type == ActionType.ACCEPT:
                return {
                    "valid": True,
                    "error": None,
                    "steps": [step.model_dump() for step in steps],
                    "ast": self.get_ast(steps),
                }
            return {
                "valid": False,
                "error": last_step.explanation,
                "steps": [step.model_dump() for step in steps],
                "ast": None,
            }

        except (ValueError, KeyError, IndexError) as e:
            return {"valid": False, "error": str(e), "steps": [], "ast": None}

    def get_parsing_summary(self, input_string: str) -> dict[str, Any]:
        """Get a summary of the parsing process."""
        validation_result = self.validate_input(input_string)

        return {
            "input": input_string,
            "valid": validation_result["valid"],
            "error": validation_result["error"],
            "num_steps": len(validation_result["steps"]),
            "grammar_type": self.automaton.get_grammar_type(),
            "num_states": len(self.automaton.states),
            "num_productions": len(self.grammar.productions),
        }