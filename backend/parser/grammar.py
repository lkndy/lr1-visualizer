"""Grammar definition, parsing, and validation."""

import re
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass

from parser.types import GrammarError, Production, Symbol, SymbolType
from utils.debug import debug_log, info_log, error_log, debug_timer


@dataclass
class Grammar:
    """Represents a context-free grammar with LR(1) parsing capabilities."""
    
    productions: List[Production]
    start_symbol: Symbol
    terminals: Set[Symbol]
    non_terminals: Set[Symbol]
    
    def __init__(self, productions: List[Production], start_symbol: Symbol):
        """Initialize grammar with productions and start symbol."""
        debug_log("🔧 Initializing Grammar", {
            "num_productions": len(productions),
            "start_symbol": str(start_symbol)
        })
        
        self.productions = productions
        self.start_symbol = start_symbol
        
        # Extract terminals and non-terminals
        self.non_terminals = set()
        self.terminals = set()
        
        # Add start symbol as non-terminal
        self.non_terminals.add(start_symbol)
        
        self._epsilon_symbol = Symbol("ε", SymbolType.EPSILON)
        
        # Extract symbols from productions
        for production in productions:
            self.non_terminals.add(production.lhs)
            for symbol in production.rhs:
                if symbol.symbol_type == SymbolType.TERMINAL:
                    self.terminals.add(symbol)
                elif symbol.symbol_type == SymbolType.NON_TERMINAL:
                    self.non_terminals.add(symbol)
        
        debug_log("✅ Grammar initialized", {
            "terminals": [str(t) for t in self.terminals],
            "non_terminals": [str(nt) for nt in self.non_terminals]
        })
    
    @classmethod
    def from_string(cls, grammar_text: str, start_symbol_name: str = "S") -> "Grammar":
        """Parse grammar from text format.
        
        Expected format:
        S -> A B | C
        A -> a | ε
        B -> b
        """
        productions = []
        errors = []
        
        # Create augmented start symbol
        start_symbol = Symbol(start_symbol_name, SymbolType.NON_TERMINAL)
        augmented_start = Symbol(f"{start_symbol_name}'", SymbolType.NON_TERMINAL)
        
        lines = grammar_text.strip().split('\n')
        all_symbols: Dict[str, Symbol] = {start_symbol_name: start_symbol}
        
        # First pass: collect all LHS symbols as non-terminals
        lhs_names: Set[str] = set()
        for raw_line in lines:
            raw = raw_line.strip()
            if not raw or raw.startswith('#'):
                continue
            if '->' not in raw and '→' not in raw:
                continue
            sep = '->' if '->' in raw else '→'
            lhs_candidate = raw.split(sep, 1)[0].strip()
            if lhs_candidate:
                lhs_names.add(lhs_candidate)
                if lhs_candidate not in all_symbols:
                    all_symbols[lhs_candidate] = Symbol(lhs_candidate, SymbolType.NON_TERMINAL)
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):  # Skip empty lines and comments
                continue
                
            try:
                if '->' not in line and '→' not in line:
                    errors.append(GrammarError(
                        error_type="syntax_error",
                        message=f"Missing '->' or '→' in production",
                        line_number=line_num
                    ))
                    continue
                
                # Split lhs and rhs
                separator = '->' if '->' in line else '→'
                lhs_str, rhs_str = line.split(separator, 1)
                lhs_str = lhs_str.strip()
                rhs_str = rhs_str.strip()
                
                if not lhs_str:
                    errors.append(GrammarError(
                        error_type="syntax_error", 
                        message="Empty left-hand side",
                        line_number=line_num
                    ))
                    continue
                
                # Create or get LHS symbol
                if lhs_str not in all_symbols:
                    all_symbols[lhs_str] = Symbol(lhs_str, SymbolType.NON_TERMINAL)
                lhs = all_symbols[lhs_str]
                
                # Parse RHS (handle alternatives)
                alternatives = [alt.strip() for alt in rhs_str.split('|')]
                
                for alt in alternatives:
                    # Empty alternative (epsilon)
                    if not alt:
                        productions.append(Production(lhs, []))
                        continue
                    # Explicit epsilon token
                    if alt == 'ε' or alt.lower() in ('epsilon', 'eps'):
                        productions.append(Production(lhs, []))
                        continue
                    
                    rhs_symbols = []
                    tokens = cls._tokenize_rhs(alt)
                    
                    for token in tokens:
                        # Skip explicit epsilon within tokenized RHS
                        if token == 'ε' or token.lower() in ('epsilon', 'eps'):
                            continue
                        if token not in all_symbols:
                            # Determine if terminal or non-terminal
                            # Two-pass rule:
                            # - If token was seen on LHS, it's a non-terminal
                            # - Otherwise classify by punctuation/common terminals/heuristic
                            if token in lhs_names:
                                all_symbols[token] = Symbol(token, SymbolType.NON_TERMINAL)
                            else:
                                # Convention: 
                                # - Punctuation/special chars = terminal
                                # - Common terminal names = terminal
                                # - Lowercase words default to terminal
                                # - Otherwise assume non-terminal
                                if (token.islower() or 
                                    token in ['id', 'num', 'string', 'true', 'false', 'null', 'number'] or
                                    token in ['(', ')', '[', ']', '{', '}', '+', '-', '*', '/', '=', '<', '>', '<=', '>=', '==', '!=', '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', '++', '--', '+=', '-=', '*=', '/=', '%=', '^=', '&=', '|=', '<<=', '>>=', '=>', '->', '::', '.', ',', ';', ':', '?', '??', '??=', '...', '..', '..='] or
                                    not token.replace('_', '').replace('-', '').isalnum()):
                                    all_symbols[token] = Symbol(token, SymbolType.TERMINAL)
                                else:
                                    all_symbols[token] = Symbol(token, SymbolType.NON_TERMINAL)
                        
                        rhs_symbols.append(all_symbols[token])
                    
                    productions.append(Production(lhs, rhs_symbols))
                    
            except Exception as e:
                errors.append(GrammarError(
                    error_type="parse_error",
                    message=f"Error parsing line: {str(e)}",
                    line_number=line_num
                ))
        
        # Add augmented production
        productions.insert(0, Production(augmented_start, [start_symbol]))
        
        grammar = cls(productions, augmented_start)
        grammar._parse_errors = errors
        
        return grammar
    
    @staticmethod
    def _tokenize_rhs(rhs: str) -> List[str]:
        """Tokenize the right-hand side of a production."""
        # Simple tokenization - split on whitespace, handle parentheses
        tokens = []
        current_token = ""
        
        for char in rhs:
            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            elif char in '()[]{}':
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append(char)
            else:
                current_token += char
        
        if current_token:
            tokens.append(current_token)
            
        return tokens
    
    @debug_timer
    def validate(self) -> List[GrammarError]:
        """Validate the grammar and return any errors."""
        debug_log("🔍 Validating grammar")
        errors = []
        
        # Check for undefined symbols
        defined_symbols = set()
        for production in self.productions:
            defined_symbols.add(production.lhs)
            for symbol in production.rhs:
                defined_symbols.add(symbol)
        
        # Check that all non-terminals have productions
        non_terminals_with_productions = set(p.lhs for p in self.productions)
        epsilon_symbol = self._epsilon_symbol
        for non_terminal in self.non_terminals:
            if non_terminal in self.terminals or non_terminal == epsilon_symbol:
                continue  # Skip terminals mistakenly added
            if non_terminal not in non_terminals_with_productions:
                errors.append(GrammarError(
                    error_type="undefined_non_terminal",
                    message=f"Non-terminal '{non_terminal.name}' has no productions"
                ))
        
        # Check for unreachable symbols
        reachable = self._find_reachable_symbols()
        for non_terminal in self.non_terminals:
            if non_terminal not in reachable:
                errors.append(GrammarError(
                    error_type="unreachable_non_terminal", 
                    message=f"Non-terminal '{non_terminal.name}' is unreachable from start symbol"
                ))
        
        # Left recursion is acceptable for LR parsers; log informationally only
        left_recursive = self._find_left_recursive_symbols()
        if left_recursive:
            info_log("ℹ️ Left recursion detected (allowed for LR parsers)", {
                "symbols": [s.name for s in left_recursive]
            })
        
        return errors
    
    def _find_reachable_symbols(self) -> Set[Symbol]:
        """Find all symbols reachable from the start symbol."""
        reachable = {self.start_symbol}
        changed = True
        
        while changed:
            changed = False
            for production in self.productions:
                if production.lhs in reachable:
                    for symbol in production.rhs:
                        if symbol not in reachable:
                            reachable.add(symbol)
                            changed = True
        
        return reachable
    
    def _find_left_recursive_symbols(self) -> Set[Symbol]:
        """Find symbols with left recursion."""
        left_recursive = set()
        
        for production in self.productions:
            if production.rhs and production.rhs[0] == production.lhs:
                left_recursive.add(production.lhs)
        
        return left_recursive
    
    def get_productions_for_symbol(self, symbol: Symbol) -> List[Production]:
        """Get all productions with the given symbol as LHS."""
        return [p for p in self.productions if p.lhs == symbol]
    
    def is_terminal(self, symbol: Symbol) -> bool:
        """Check if symbol is a terminal."""
        return symbol.symbol_type == SymbolType.TERMINAL
    
    def is_non_terminal(self, symbol: Symbol) -> bool:
        """Check if symbol is a non-terminal."""
        return symbol.symbol_type == SymbolType.NON_TERMINAL
    
    def __str__(self) -> str:
        """String representation of the grammar."""
        lines = []
        current_lhs = None
        
        for production in self.productions:
            if production.lhs != current_lhs:
                if current_lhs is not None:
                    lines.append("")
                lines.append(f"{production.lhs.name} →")
                current_lhs = production.lhs
            else:
                lines.append("    |")
            
            rhs_str = " ".join(str(symbol) for symbol in production.rhs) if production.rhs else "ε"
            lines.append(f"    {rhs_str}")
        
        return "\n".join(lines)
