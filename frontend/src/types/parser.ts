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

// NEW: Interactive derivation types matching backend response
export interface InteractiveDerivationStep {
  step_number: number;
  stack: [number, string][];
  input_remaining: string[];
  current_token: string | null;
  action: {
    type: 'shift' | 'reduce' | 'accept' | 'error';
    target: number | null;
    description: string; // Human-readable: "Shift to state 4"
  };
  explanation: string;
  ast_nodes: ASTNode[];
  derivation_so_far: string; // NEW: Derivation progress
}

export interface InteractiveDerivationResponse {
  valid: boolean;
  error: string | null;
  input_string: string;
  tokens: string[]; // NEW: Tokenized input
  total_steps: number;
  success: boolean;
  steps: InteractiveDerivationStep[];
  summary: {
    total_steps: number;
    success: boolean;
    grammar_type: string; // "LR(1)", "SLR(1)", etc.
    num_states: number;
    num_productions: number;
  };
}

// Legacy types for backward compatibility (deprecated)
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

// ENHANCED: LR(1) state type matching backend response
export interface LR1State {
  state_number: number;
  items: string[]; // Formatted items: "E → • E + T , $"
  shift_symbols: string[];
  reduce_items: string[];
  transitions: Array<{
    to_state: number;
    symbol: string;
  }>;
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
    terminals_list: Array<{ name: string; type: string }>;
    non_terminals_list: Array<{ name: string; type: string }>;
    productions_detailed: Array<{
      lhs: string;
      rhs: string[];
      index: number;
    }>;
    first_sets: Record<string, string[]>; // NEW: FIRST sets
    follow_sets: Record<string, string[]>; // NEW: FOLLOW sets
    lr1_states: LR1State[]; // NEW: Full automaton data
    sample_strings: string[];
    parsing_table_preview: {
      action_table: {
        headers: string[];
        rows: string[][];
      };
      goto_table: {
        headers: string[];
        rows: string[][];
      };
    };
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
  sample_inputs: string[];
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

  // Parsing state - UPDATED for interactive derivation
  inputString: string;
  selectedSampleString: string;
  availableSampleStrings: string[];
  currentStep: number;
  totalSteps: number;
  parsingSteps: InteractiveDerivationStep[]; // UPDATED: Use new type
  ast?: ParsingResponse['ast'];
  parsingValid: boolean;
  parsingError?: string;

  // NEW: Interactive derivation fields
  tokens: string[]; // Tokenized input
  currentToken: string | null; // Token being processed
  derivationProgress: string; // Current derivation string
  currentStateInAutomaton: number | null; // Current state for automaton highlighting

  // UI state
  isPlaying: boolean;
  playSpeed: number;
  selectedExample?: string;
  activeTab: 'grammar-config' | 'parsing-viz';
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
  selectSampleString: (sample: string) => void;
  parseInput: () => Promise<void>;
  setCurrentStep: (step: number) => void;
  nextStep: () => void;
  previousStep: () => void;
  play: () => void;
  pause: () => void;
  reset: () => void;

  // NEW: Computed selectors for interactive derivation
  getCurrentStepData: () => InteractiveDerivationStep | null;
  getCurrentState: () => number | null;
  getCurrentAction: () => InteractiveDerivationStep['action'] | null;

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
