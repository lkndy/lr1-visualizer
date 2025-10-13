/** Type definitions for the LR(1) parser visualizer. */

export interface Symbol {
  name: string;
  symbol_type: 'terminal' | 'non_terminal' | 'epsilon';
}

export interface Production {
  lhs: Symbol;
  rhs: Symbol[];
}

export interface LR1Item {
  production: Production;
  dot_position: number;
  lookahead: Symbol;
}

export interface ParsingAction {
  action_type: 'shift' | 'reduce' | 'accept' | 'error';
  target?: number;
}

export interface ParsingStep {
  step_number: number;
  stack: [number, string][];
  input_pointer: number;
  current_token?: string;
  action: ParsingAction;
  explanation: string;
  ast_nodes: ASTNode[];
}

export interface ASTNode {
  id: string;
  symbol: string;
  symbol_type: 'terminal' | 'non_terminal' | 'epsilon';
  children: string[];
  parent?: string;
  production_used?: number;
}

export interface GrammarError {
  type: string;
  message: string;
  line_number?: number;
  symbol?: string;
}

export interface ConflictInfo {
  state: number;
  symbol: string;
  actions: ParsingAction[];
  conflict_type: string;
}

export interface GrammarValidationResponse {
  valid: boolean;
  errors: GrammarError[];
  grammar_info?: {
    num_productions: number;
    num_terminals: number;
    num_non_terminals: number;
    num_states: number;
    grammar_type: string;
    has_conflicts: boolean;
    conflict_summary: any;
  };
}

export interface ParsingTableResponse {
  action_table: {
    headers: string[];
    rows: string[][];
  };
  goto_table: {
    headers: string[];
    rows: string[][];
  };
  summary: {
    num_states: number;
    num_terminals: number;
    num_non_terminals: number;
    action_entries: number;
    goto_entries: number;
    has_conflicts: boolean;
    conflicts: any;
  };
  conflicts: ConflictInfo[];
}

export interface ParsingResponse {
  valid: boolean;
  error?: string;
  steps: ParsingStep[];
  ast?: {
    nodes: Record<string, ASTNode>;
    root?: string;
  };
  summary: {
    input: string;
    valid: boolean;
    error?: string;
    num_steps: number;
    grammar_type: string;
    num_states: number;
    num_productions: number;
  };
}

export interface ExampleGrammar {
  name: string;
  description: string;
  grammar: string;
  start_symbol: string;
  example_input: string;
}

export interface ExampleGrammarsResponse {
  examples: Record<string, ExampleGrammar>;
}

// State management types
export interface ParserState {
  // Grammar state
  grammarText: string;
  startSymbol: string;
  grammarValid: boolean;
  grammarErrors: GrammarError[];
  grammarInfo?: GrammarValidationResponse['grammar_info'];
  
  // Parsing table state
  actionTable?: ParsingTableResponse['action_table'];
  gotoTable?: ParsingTableResponse['goto_table'];
  tableSummary?: ParsingTableResponse['summary'];
  tableConflicts: ConflictInfo[];
  
  // Parsing state
  inputString: string;
  currentStep: number;
  totalSteps: number;
  parsingSteps: ParsingStep[];
  ast?: ParsingResponse['ast'];
  parsingValid: boolean;
  parsingError?: string;
  
  // UI state
  isPlaying: boolean;
  playSpeed: number;
  selectedExample?: string;
  activeTab: 'grammar' | 'table' | 'automaton' | 'parse';
  showConflicts: boolean;
  
  // Loading states
  isValidatingGrammar: boolean;
  isGeneratingTable: boolean;
  isParsing: boolean;
}

export interface ParserActions {
  // Grammar actions
  setGrammarText: (text: string) => void;
  setStartSymbol: (symbol: string) => void;
  validateGrammar: () => Promise<void>;
  
  // Table actions
  generateParsingTable: () => Promise<void>;
  
  // Parsing actions
  setInputString: (input: string) => void;
  parseInput: () => Promise<void>;
  setCurrentStep: (step: number) => void;
  nextStep: () => void;
  previousStep: () => void;
  play: () => void;
  pause: () => void;
  reset: () => void;
  
  // UI actions
  setPlaySpeed: (speed: number) => void;
  selectExample: (example: string) => void;
  setActiveTab: (tab: ParserState['activeTab']) => void;
  setShowConflicts: (show: boolean) => void;
  
  // Utility actions
  loadExample: (example: ExampleGrammar) => void;
  clearAll: () => void;
}

// Animation and visualization types
export interface AnimationConfig {
  duration: number;
  easing: string;
  delay?: number;
}

export interface NodePosition {
  x: number;
  y: number;
}

export interface EdgePosition {
  source: NodePosition;
  target: NodePosition;
}

export interface ASTVisualizationNode {
  id: string;
  symbol: string;
  position: NodePosition;
  color: string;
  size: number;
  isHighlighted: boolean;
  isNew: boolean;
}

export interface ASTVisualizationEdge {
  id: string;
  source: string;
  target: string;
  color: string;
  isHighlighted: boolean;
  isNew: boolean;
}

export interface StackItem {
  id: string;
  state: number;
  symbol: string;
  isNew: boolean;
  isRemoved: boolean;
}

export interface AutomatonNode {
  id: string;
  state: number;
  items: LR1Item[];
  position: { x: number; y: number };
  isCurrent: boolean;
  isHighlighted: boolean;
}

export interface AutomatonEdge {
  id: string;
  source: string;
  target: string;
  symbol: string;
  isActive: boolean;
  isHighlighted: boolean;
}
