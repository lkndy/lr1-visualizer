/** Zustand store for parser state management. */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import {
  ParserState,
  ParserActions,
  GrammarValidationResponse,
  ParsingTableResponse,
  ParsingResponse,
  ExampleGrammar,
  ExampleGrammarsResponse
} from '../types/parser';
import debug from '../utils/debug';

// API base URL
const API_BASE = 'http://localhost:8000/api/v1';

// Initial state
const initialState: ParserState = {
  // Grammar state
  grammarText: '',
  startSymbol: 'S',
  grammarValid: false,
  grammarErrors: [],
  grammarInfo: undefined,

  // Parsing table state
  actionTable: undefined,
  gotoTable: undefined,
  tableSummary: undefined,
  tableConflicts: [],

  // Parsing state
  inputString: '',
  selectedSampleString: '',
  availableSampleStrings: [],
  currentStep: 0,
  totalSteps: 0,
  parsingSteps: [],
  ast: undefined,
  parsingValid: false,
  parsingError: undefined,

  // UI state
  isPlaying: false,
  playSpeed: 1,
  selectedExample: undefined,
  activeTab: 'grammar-config',
  showConflicts: false,

  // Loading states
  isValidatingGrammar: false,
  isGeneratingTable: false,
  isParsing: false,
};

// API functions
async function validateGrammar(grammarText: string, startSymbol: string): Promise<GrammarValidationResponse> {
  debug.api.request('POST', '/grammar/validate', { startSymbol, grammarLength: grammarText.length });

  const response = await fetch(`${API_BASE}/grammar/validate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      grammar_text: grammarText,
      start_symbol: startSymbol,
    }),
  });

  debug.api.response('/grammar/validate', response.status);

  if (!response.ok) {
    throw new Error(`Grammar validation failed: ${response.statusText}`);
  }

  const result = await response.json();
  debug.log('Grammar validation result', { valid: result.valid, errors: result.errors?.length });

  return result;
}

async function generateParsingTable(grammarText: string, startSymbol: string): Promise<ParsingTableResponse> {
  const response = await fetch(`${API_BASE}/parser/table`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      grammar_text: grammarText,
      start_symbol: startSymbol,
    }),
  });

  if (!response.ok) {
    throw new Error(`Table generation failed: ${response.statusText}`);
  }

  return response.json();
}

async function parseInput(grammarText: string, inputString: string, startSymbol: string): Promise<ParsingResponse> {
  const response = await fetch(`${API_BASE}/parser/parse`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      grammar_text: grammarText,
      input_string: inputString,
      start_symbol: startSymbol,
    }),
  });

  if (!response.ok) {
    throw new Error(`Parsing failed: ${response.statusText}`);
  }

  return response.json();
}

async function getExampleGrammars(): Promise<ExampleGrammarsResponse> {
  const response = await fetch(`${API_BASE}/examples`);

  if (!response.ok) {
    throw new Error(`Failed to fetch examples: ${response.statusText}`);
  }

  return response.json();
}

// Store definition
export const useParserStore = create<ParserState & ParserActions>()(
  devtools(
    (set, get) => ({
      ...initialState,

      // Grammar actions
      setGrammarText: (text: string) => {
        debug.store.action('setGrammarText', { textLength: text.length });
        set({ grammarText: text });
        // Auto-validate grammar when text changes
        const { validateGrammar } = get();
        setTimeout(() => validateGrammar(), 500);
      },

      setStartSymbol: (symbol: string) => {
        set({ startSymbol: symbol });
      },

      validateGrammar: async () => {
        const { grammarText, startSymbol } = get();

        debug.store.action('validateGrammar', { grammarLength: grammarText.length, startSymbol });

        if (!grammarText.trim()) {
          debug.log('Empty grammar text, skipping validation');
          set({
            grammarValid: false,
            grammarErrors: [],
            grammarInfo: undefined,
            isValidatingGrammar: false,
          });
          return;
        }

        set({ isValidatingGrammar: true });

        try {
          const response = await validateGrammar(grammarText, startSymbol);

          set({
            grammarValid: response.valid,
            grammarErrors: response.errors,
            grammarInfo: response.grammar_info,
            availableSampleStrings: response.grammar_info?.sample_strings || [],
            isValidatingGrammar: false,
          });

          // If grammar is valid, also generate the parsing table automatically
          if (response.valid && response.grammar_info?.parsing_table_preview) {
            set({
              actionTable: response.grammar_info.parsing_table_preview.action_table,
              gotoTable: response.grammar_info.parsing_table_preview.goto_table,
              tableSummary: {
                num_states: response.grammar_info.num_states,
                num_terminals: response.grammar_info.num_terminals,
                num_non_terminals: response.grammar_info.num_non_terminals,
                action_entries: 0, // Will be calculated from table
                goto_entries: 0, // Will be calculated from table
                has_conflicts: response.grammar_info.has_conflicts,
                conflicts: response.grammar_info.conflict_summary,
              },
              tableConflicts: [], // Will be populated from conflicts
            });
          }
        } catch (error) {
          set({
            grammarValid: false,
            grammarErrors: [{
              type: 'api_error',
              message: error instanceof Error ? error.message : 'Unknown error',
            }],
            grammarInfo: undefined,
            isValidatingGrammar: false,
          });
        }
      },

      // Table actions
      generateParsingTable: async () => {
        const { grammarText, startSymbol, grammarValid } = get();

        if (!grammarValid || !grammarText.trim()) {
          return;
        }

        set({ isGeneratingTable: true });

        try {
          const response = await generateParsingTable(grammarText, startSymbol);

          set({
            actionTable: response.action_table,
            gotoTable: response.goto_table,
            tableSummary: response.summary,
            tableConflicts: response.conflicts,
            isGeneratingTable: false,
          });
        } catch (error) {
          set({
            actionTable: undefined,
            gotoTable: undefined,
            tableSummary: undefined,
            tableConflicts: [],
            isGeneratingTable: false,
          });
        }
      },

      // Parsing actions
      setInputString: (input: string) => {
        set({ inputString: input });
      },

      selectSampleString: (sample: string) => {
        set({
          selectedSampleString: sample,
          inputString: sample
        });
      },

      parseInput: async () => {
        const { grammarText, inputString, startSymbol, grammarValid } = get();

        if (!grammarValid || !grammarText.trim() || !inputString.trim()) {
          return;
        }

        set({ isParsing: true });

        try {
          const response = await parseInput(grammarText, inputString, startSymbol);

          set({
            parsingSteps: response.steps,
            totalSteps: response.steps.length,
            currentStep: 0,
            ast: response.ast,
            parsingValid: response.valid,
            parsingError: response.error,
            isParsing: false,
          });
        } catch (error) {
          set({
            parsingSteps: [],
            totalSteps: 0,
            currentStep: 0,
            ast: undefined,
            parsingValid: false,
            parsingError: error instanceof Error ? error.message : 'Unknown error',
            isParsing: false,
          });
        }
      },

      setCurrentStep: (step: number) => {
        const { totalSteps } = get();
        const clampedStep = Math.max(0, Math.min(step, totalSteps - 1));
        set({ currentStep: clampedStep });
      },

      nextStep: () => {
        const { currentStep, totalSteps } = get();
        if (currentStep < totalSteps - 1) {
          set({ currentStep: currentStep + 1 });
        }
      },

      previousStep: () => {
        const { currentStep } = get();
        if (currentStep > 0) {
          set({ currentStep: currentStep - 1 });
        }
      },

      play: () => {
        set({ isPlaying: true });
      },

      pause: () => {
        set({ isPlaying: false });
      },

      reset: () => {
        set({
          currentStep: 0,
          isPlaying: false,
          parsingSteps: [],
          totalSteps: 0,
          ast: undefined,
          parsingValid: false,
          parsingError: undefined,
        });
      },

      // UI actions
      setPlaySpeed: (speed: number) => {
        set({ playSpeed: Math.max(0.1, Math.min(5, speed)) });
      },

      selectExample: (example: string) => {
        set({ selectedExample: example });
      },

      setActiveTab: (tab: ParserState['activeTab']) => {
        set({ activeTab: tab });
      },

      setShowConflicts: (show: boolean) => {
        set({ showConflicts: show });
      },

      // Utility actions
      loadExample: (example: ExampleGrammar) => {
        set({
          grammarText: example.grammar,
          startSymbol: example.start_symbol,
          inputString: example.sample_inputs[0] || '',
          selectedSampleString: example.sample_inputs[0] || '',
          availableSampleStrings: example.sample_inputs,
          selectedExample: example.name,
          activeTab: 'grammar-config',
        });

        // Validate grammar after loading example
        const { validateGrammar } = get();
        setTimeout(() => validateGrammar(), 100);
      },

      clearAll: () => {
        set({
          ...initialState,
          activeTab: get().activeTab, // Keep current tab
        });
      },
    }),
    {
      name: 'parser-store',
    }
  )
);

// Export API functions for external use
export { validateGrammar, generateParsingTable, parseInput, getExampleGrammars };
