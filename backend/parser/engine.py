"""LR(1) parsing engine for step-by-step execution and AST building."""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import copy

from parser.types import ParsingStep, ParsingAction, ActionType, ASTNode, SymbolType
from parser.grammar import Grammar
from parser.automaton import Automaton
from parser.table import ParsingTable


@dataclass
class ParseState:
    """Represents the current state of the parser."""
    stack: List[Tuple[int, str]]  # (state, symbol)
    input_tokens: List[str]
    input_pointer: int
    step_number: int
    ast_nodes: Dict[str, ASTNode]  # node_id -> ASTNode
    next_node_id: int


class ParserEngine:
    """LR(1) parsing engine for step-by-step execution."""
    
    def __init__(self, grammar, parsing_table):
        """Initialize parser engine with grammar and parsing table."""
        self.grammar = grammar
        self.parsing_table = parsing_table
        self.automaton = parsing_table.automaton
        
        # Validate that table is conflict-free
        if parsing_table.has_conflicts():
            raise ValueError("Cannot create parser with conflicting parsing table")
    
    def parse(self, input_string: str) -> List[ParsingStep]:
        """Parse input string and return list of all parsing steps."""
        tokens = self._tokenize(input_string)
        return self._parse_tokens(tokens)
    
    def _tokenize(self, input_string: str) -> List[str]:
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
            elif char in '()[]{}+-*/=<>!&|':
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
    
    def _parse_tokens(self, tokens: List[str]) -> List[ParsingStep]:
        """Parse token list and return all parsing steps."""
        steps = []
        
        # Initialize parse state
        parse_state = ParseState(
            stack=[(0, "")],  # Start with state 0 and empty symbol
            input_tokens=tokens,
            input_pointer=0,
            step_number=0,
            ast_nodes={},
            next_node_id=0
        )
        
        while True:
            step = self._execute_step(parse_state)
            steps.append(step)
            
            if step.action.action_type == ActionType.ACCEPT:
                break
            elif step.action.action_type == ActionType.ERROR:
                break
            
            # Update parse state for next iteration
            parse_state = self._update_parse_state(parse_state, step)
        
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
            action = self.parsing_table.get_action(current_state, current_token)
        
        if action is None:
            action = ParsingAction(action_type=ActionType.ERROR, target=None)
            explanation = f"No action defined for state {current_state} and symbol '{current_token}'"
        else:
            if action.action_type == ActionType.SHIFT:
                explanation = f"Shift: Move to state {action.target} and push '{current_token}' onto stack"
                ast_nodes_created = self._handle_shift(parse_state, current_token, action.target)
                
            elif action.action_type == ActionType.REDUCE:
                production = self.grammar.productions[action.target]
                explanation = f"Reduce: Apply production {production}"
                ast_nodes_created = self._handle_reduce(parse_state, production, action.target)
                
            elif action.action_type == ActionType.ACCEPT:
                explanation = "Accept: Input successfully parsed"
                
            else:
                explanation = "Error: Invalid action"
        
        return ParsingStep(
            step_number=parse_state.step_number,
            stack=copy.deepcopy(parse_state.stack),
            input_pointer=parse_state.input_pointer,
            current_token=current_token,
            action=action,
            explanation=explanation,
            ast_nodes=ast_nodes_created
        )
    
    def _handle_shift(self, parse_state: ParseState, token: str, target_state: int) -> List[Dict[str, Any]]:
        """Handle shift action and return created AST nodes."""
        ast_nodes_created = []
        
        # Create AST node for terminal
        node_id = f"node_{parse_state.next_node_id}"
        parse_state.next_node_id += 1
        
        ast_node = ASTNode(
            id=node_id,
            symbol=token,
            symbol_type=SymbolType.TERMINAL,
            children=[],
            parent=None,
            production_used=None
        )
        
        parse_state.ast_nodes[node_id] = ast_node
        ast_nodes_created.append(ast_node.dict())
        
        return ast_nodes_created
    
    def _handle_reduce(self, parse_state: ParseState, production, production_index: int) -> List[Dict[str, Any]]:
        """Handle reduce action and return created AST nodes."""
        ast_nodes_created = []
        
        # Create AST node for non-terminal
        node_id = f"node_{parse_state.next_node_id}"
        parse_state.next_node_id += 1
        
        ast_node = ASTNode(
            id=node_id,
            symbol=production.lhs.name,
            symbol_type=SymbolType.NON_TERMINAL,
            children=[],
            parent=None,
            production_used=production_index
        )
        
        parse_state.ast_nodes[node_id] = ast_node
        ast_nodes_created.append(ast_node.dict())
        
        return ast_nodes_created
    
    def _update_parse_state(self, parse_state: ParseState, step: ParsingStep) -> ParseState:
        """Update parse state after executing a step."""
        new_parse_state = copy.deepcopy(parse_state)
        
        if step.action.action_type == ActionType.SHIFT:
            # Push new state and symbol onto stack
            new_parse_state.stack.append((step.action.target, step.current_token))
            new_parse_state.input_pointer += 1
            
        elif step.action.action_type == ActionType.REDUCE:
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
    
    def get_ast(self, steps: List[ParsingStep]) -> Dict[str, Any]:
        """Build final AST from parsing steps."""
        # This is a simplified AST building - in a real implementation,
        # you'd need to track parent-child relationships during parsing
        
        ast_nodes = {}
        for step in steps:
            for node_data in step.ast_nodes:
                ast_nodes[node_data["id"]] = node_data
        
        return {
            "nodes": ast_nodes,
            "root": self._find_root_node(ast_nodes)
        }
    
    def _find_root_node(self, ast_nodes: Dict[str, Any]) -> Optional[str]:
        """Find the root node of the AST."""
        # The root should be the start symbol
        for node_id, node_data in ast_nodes.items():
            if node_data["symbol"] == self.grammar.start_symbol.name:
                return node_id
        return None
    
    def validate_input(self, input_string: str) -> Dict[str, Any]:
        """Validate input string and return parsing result."""
        try:
            steps = self.parse(input_string)
            
            if not steps:
                return {
                    "valid": False,
                    "error": "No parsing steps generated",
                    "steps": []
                }
            
            last_step = steps[-1]
            
            if last_step.action.action_type == ActionType.ACCEPT:
                return {
                    "valid": True,
                    "error": None,
                    "steps": [step.dict() for step in steps],
                    "ast": self.get_ast(steps)
                }
            else:
                return {
                    "valid": False,
                    "error": last_step.explanation,
                    "steps": [step.dict() for step in steps],
                    "ast": None
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "steps": [],
                "ast": None
            }
    
    def get_parsing_summary(self, input_string: str) -> Dict[str, Any]:
        """Get a summary of the parsing process."""
        validation_result = self.validate_input(input_string)
        
        return {
            "input": input_string,
            "valid": validation_result["valid"],
            "error": validation_result["error"],
            "num_steps": len(validation_result["steps"]),
            "grammar_type": self.automaton.get_grammar_type(),
            "num_states": len(self.automaton.states),
            "num_productions": len(self.grammar.productions)
        }
