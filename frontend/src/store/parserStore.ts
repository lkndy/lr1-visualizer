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
  ExampleGrammarsResponse,
  InteractiveDerivationStep
} from '../types/parser';
import { validateGrammar, parseInteractive, getExampleGrammars, APIError } from '../api/client';
import debug from '../utils/debug';
import { dataValidator } from '../utils/dataValidator';
import { logger } from '../utils/logger';

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

  // Parsing state - UPDATED for interactive derivation
  inputString: '',
  selectedSampleString: '',
  availableSampleStrings: [],
  currentStep: 0,
  totalSteps: 0,
  parsingSteps: [],
  ast: undefined,
  parsingValid: false,
  parsingError: undefined,

  // NEW: Interactive derivation fields
  tokens: [],
  currentToken: null,
  derivationProgress: '',
  currentStateInAutomaton: null,

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

// API functions are now imported from api/client.ts

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

          // Validate response before setting state
          const validation = dataValidator.validateWithUserFeedback(
            response,
            'GrammarValidation',
            (data, component) => dataValidator.validateGrammarResponse(data, component)
          );

          if (!validation.isValid) {
            logger.error('STORE', 'Grammar validation response failed validation', validation.errors);
            set({
              grammarValid: false,
              grammarErrors: [{
                type: 'validation_error',
                message: 'Response validation failed. Check console for details.',
              }],
              grammarInfo: undefined,
              isValidatingGrammar: false,
            });
            return;
          }

          logger.stateChange('ParserStore', 'validateGrammar', {
            valid: response.valid,
            hasGrammarInfo: !!response.grammar_info
          });

          set({
            grammarValid: response.valid,
            grammarErrors: response.errors,
            grammarInfo: response.grammar_info,
            availableSampleStrings: response.grammar_info?.sample_strings || [],
            isValidatingGrammar: false,
          });

          // If grammar is valid, store the parsing table from the enhanced response
          if (response.valid && response.grammar_info?.parsing_table_preview) {
            // Validate table data before storing
            const actionTableValid = dataValidator.isParsingTableResponse({
              action_table: response.grammar_info.parsing_table_preview.action_table,
              goto_table: response.grammar_info.parsing_table_preview.goto_table,
            });

            if (!actionTableValid) {
              logger.warn('STORE', 'Parsing table data validation failed', {
                actionTable: response.grammar_info.parsing_table_preview.action_table,
                gotoTable: response.grammar_info.parsing_table_preview.goto_table,
              });
            }

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
          const errorMessage = error instanceof APIError
            ? error.message
            : error instanceof Error
              ? error.message
              : 'Unknown error';

          set({
            grammarValid: false,
            grammarErrors: [{
              type: 'api_error',
              message: errorMessage,
            }],
            grammarInfo: undefined,
            isValidatingGrammar: false,
          });
        }
      },

      // Table actions - DEPRECATED: Table data now comes from grammar validation
      generateParsingTable: async () => {
        console.warn('generateParsingTable is deprecated - table data is now included in grammar validation response');
        // Table data is automatically populated when grammar is validated
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
          const response = await parseInteractive(grammarText, inputString, startSymbol);

          // Validate response before setting state
          const validation = dataValidator.validateWithUserFeedback(
            response,
            'ParsingResponse',
            (data, component) => dataValidator.validateParsingResponse(data, component)
          );

          if (!validation.isValid) {
            logger.error('STORE', 'Parsing response failed validation', validation.errors);
            set({
              parsingSteps: [],
              totalSteps: 0,
              currentStep: 0,
              ast: undefined,
              parsingValid: false,
              parsingError: 'Response validation failed. Check console for details.',
              tokens: [],
              currentToken: null,
              derivationProgress: '',
              currentStateInAutomaton: null,
              isParsing: false,
            });
            return;
          }

          logger.stateChange('ParserStore', 'parseInput', {
            success: response.success,
            totalSteps: response.total_steps,
            hasSteps: response.steps.length > 0
          });

          // Update parsing state with new interactive derivation data
          set({
            parsingSteps: response.steps,
            totalSteps: response.total_steps,
            currentStep: 0,
            ast: undefined, // AST is now embedded in steps
            parsingValid: response.success,
            parsingError: response.error,
            tokens: response.tokens,
            currentToken: response.steps[0]?.current_token || null,
            derivationProgress: response.steps[0]?.derivation_so_far || '',
            currentStateInAutomaton: response.steps[0]?.stack[response.steps[0].stack.length - 1]?.[0] || null,
            isParsing: false,
          });
        } catch (error) {
          const errorMessage = error instanceof APIError
            ? error.message
            : error instanceof Error
              ? error.message
              : 'Unknown error';

          set({
            parsingSteps: [],
            totalSteps: 0,
            currentStep: 0,
            ast: undefined,
            parsingValid: false,
            parsingError: errorMessage,
            tokens: [],
            currentToken: null,
            derivationProgress: '',
            currentStateInAutomaton: null,
            isParsing: false,
          });
        }
      },

      setCurrentStep: (step: number) => {
        const { totalSteps, parsingSteps } = get();
        const clampedStep = Math.max(0, Math.min(step, totalSteps - 1));
        const stepData = parsingSteps[clampedStep];

        set({
          currentStep: clampedStep,
          currentToken: stepData?.current_token || null,
          derivationProgress: stepData?.derivation_so_far || '',
          currentStateInAutomaton: stepData?.stack[stepData.stack.length - 1]?.[0] || null,
        });
      },

      nextStep: () => {
        const { currentStep, totalSteps, parsingSteps } = get();
        if (currentStep < totalSteps - 1) {
          const newStep = currentStep + 1;
          const stepData = parsingSteps[newStep];
          set({
            currentStep: newStep,
            currentToken: stepData?.current_token || null,
            derivationProgress: stepData?.derivation_so_far || '',
            currentStateInAutomaton: stepData?.stack[stepData.stack.length - 1]?.[0] || null,
          });
        }
      },

      previousStep: () => {
        const { currentStep, parsingSteps } = get();
        if (currentStep > 0) {
          const newStep = currentStep - 1;
          const stepData = parsingSteps[newStep];
          set({
            currentStep: newStep,
            currentToken: stepData?.current_token || null,
            derivationProgress: stepData?.derivation_so_far || '',
            currentStateInAutomaton: stepData?.stack[stepData.stack.length - 1]?.[0] || null,
          });
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
          tokens: [],
          currentToken: null,
          derivationProgress: '',
          currentStateInAutomaton: null,
        });
      },

      // NEW: Computed selectors for interactive derivation
      getCurrentStepData: () => {
        const { parsingSteps, currentStep } = get();
        return parsingSteps[currentStep] || null;
      },

      getCurrentState: () => {
        const stepData = get().getCurrentStepData();
        if (!stepData || stepData.stack.length === 0) return null;
        return stepData.stack[stepData.stack.length - 1][0]; // Top of stack state
      },

      getCurrentAction: () => {
        const stepData = get().getCurrentStepData();
        return stepData?.action || null;
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

// API functions are now exported from api/client.ts
