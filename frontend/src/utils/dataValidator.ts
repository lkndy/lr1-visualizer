/** Runtime data validators with type checking and user-friendly error messages. */

import { logger } from './logger';
import {
    GrammarValidationResponse,
    ParsingTableResponse,
    InteractiveDerivationResponse,
    InteractiveDerivationStep,
    LR1State,
    GrammarError,
    ConflictInfo
} from '../types/parser';

export interface ValidationError {
    field: string;
    message: string;
    expected: string;
    actual: any;
    suggestion?: string;
}

export interface ValidationResult {
    isValid: boolean;
    errors: ValidationError[];
    warnings: ValidationError[];
}

class DataValidator {
    private showUserErrors: boolean = true;

    constructor(showUserErrors: boolean = true) {
        this.showUserErrors = showUserErrors;
    }

    private createError(field: string, message: string, expected: string, actual: any, suggestion?: string): ValidationError {
        return { field, message, expected, actual, suggestion };
    }

    private logValidationError(component: string, error: ValidationError): void {
        logger.validationError(component, `${error.field}: ${error.message}`, {
            expected: error.expected,
            actual: error.actual,
            suggestion: error.suggestion,
        });
    }

    private logValidationWarning(component: string, warning: ValidationError): void {
        logger.validationWarn(component, `${warning.field}: ${warning.message}`, {
            expected: warning.expected,
            actual: warning.actual,
            suggestion: warning.suggestion,
        });
    }

    // Grammar validation response validator
    validateGrammarResponse(data: any, component: string = 'GrammarResponse'): ValidationResult {
        const errors: ValidationError[] = [];
        const warnings: ValidationError[] = [];

        if (!data || typeof data !== 'object') {
            const error = this.createError(
                'root',
                'Response must be an object',
                'object',
                typeof data,
                'Check if the API response is properly formatted'
            );
            errors.push(error);
            this.logValidationError(component, error);
            return { isValid: false, errors, warnings };
        }

        // Validate required fields
        if (typeof data.valid !== 'boolean') {
            const error = this.createError(
                'valid',
                'Missing or invalid valid field',
                'boolean',
                typeof data.valid,
                'The valid field should be true or false'
            );
            errors.push(error);
            this.logValidationError(component, error);
        }

        if (!Array.isArray(data.errors)) {
            const error = this.createError(
                'errors',
                'Missing or invalid errors field',
                'array',
                typeof data.errors,
                'The errors field should be an array of error objects'
            );
            errors.push(error);
            this.logValidationError(component, error);
        }

        // Validate grammar_info if present
        if (data.grammar_info) {
            const grammarInfoResult = this.validateGrammarInfo(data.grammar_info, `${component}.grammar_info`);
            errors.push(...grammarInfoResult.errors);
            warnings.push(...grammarInfoResult.warnings);
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    private validateGrammarInfo(data: any, component: string): ValidationResult {
        const errors: ValidationError[] = [];
        const warnings: ValidationError[] = [];

        if (!data || typeof data !== 'object') {
            const error = this.createError(
                'grammar_info',
                'Grammar info must be an object',
                'object',
                typeof data
            );
            errors.push(error);
            this.logValidationError(component, error);
            return { isValid: false, errors, warnings };
        }

        // Validate numeric fields
        const numericFields = ['num_productions', 'num_terminals', 'num_non_terminals', 'num_states'];
        for (const field of numericFields) {
            if (field in data && (typeof data[field] !== 'number' || data[field] < 0)) {
                const error = this.createError(
                    field,
                    `Invalid ${field} value`,
                    'positive number',
                    data[field],
                    `${field} should be a non-negative number`
                );
                errors.push(error);
                this.logValidationError(component, error);
            }
        }

        // Validate boolean fields
        if ('has_conflicts' in data && typeof data.has_conflicts !== 'boolean') {
            const error = this.createError(
                'has_conflicts',
                'Invalid has_conflicts value',
                'boolean',
                typeof data.has_conflicts
            );
            errors.push(error);
            this.logValidationError(component, error);
        }

        // Validate parsing table preview
        if (data.parsing_table_preview) {
            const tableResult = this.validateParsingTablePreview(data.parsing_table_preview, `${component}.parsing_table_preview`);
            errors.push(...tableResult.errors);
            warnings.push(...tableResult.warnings);
        }

        // Validate LR1 states
        if (data.lr1_states) {
            const statesResult = this.validateLR1States(data.lr1_states, `${component}.lr1_states`);
            errors.push(...statesResult.errors);
            warnings.push(...statesResult.warnings);
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    private validateParsingTablePreview(data: any, component: string): ValidationResult {
        const errors: ValidationError[] = [];
        const warnings: ValidationError[] = [];

        if (!data || typeof data !== 'object') {
            const error = this.createError(
                'parsing_table_preview',
                'Parsing table preview must be an object',
                'object',
                typeof data
            );
            errors.push(error);
            this.logValidationError(component, error);
            return { isValid: false, errors, warnings };
        }

        // Validate action table
        if (data.action_table) {
            const actionResult = this.validateTableStructure(data.action_table, `${component}.action_table`);
            errors.push(...actionResult.errors);
            warnings.push(...actionResult.warnings);
        } else {
            const warning = this.createError(
                'action_table',
                'Missing action table in preview',
                'object',
                'undefined',
                'Action table should be included in grammar validation response'
            );
            warnings.push(warning);
            this.logValidationWarn(component, warning);
        }

        // Validate goto table
        if (data.goto_table) {
            const gotoResult = this.validateTableStructure(data.goto_table, `${component}.goto_table`);
            errors.push(...gotoResult.errors);
            warnings.push(...gotoResult.warnings);
        } else {
            const warning = this.createError(
                'goto_table',
                'Missing goto table in preview',
                'object',
                'undefined',
                'Goto table should be included in grammar validation response'
            );
            warnings.push(warning);
            this.logValidationWarn(component, warning);
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    validateTableStructure(table: any, component: string): ValidationResult {
        const errors: ValidationError[] = [];
        const warnings: ValidationError[] = [];

        if (!table || typeof table !== 'object') {
            const error = this.createError(
                'table',
                'Table must be an object',
                'object',
                typeof table
            );
            errors.push(error);
            this.logValidationError(component, error);
            return { isValid: false, errors, warnings };
        }

        // Validate headers
        if (!Array.isArray(table.headers)) {
            const error = this.createError(
                'headers',
                'Table headers must be an array',
                'array',
                typeof table.headers,
                'Headers should be an array of string column names'
            );
            errors.push(error);
            this.logValidationError(component, error);
        } else if (table.headers.length === 0) {
            const warning = this.createError(
                'headers',
                'Table has no headers',
                'non-empty array',
                table.headers,
                'Table should have at least one column header'
            );
            warnings.push(warning);
            this.logValidationWarn(component, warning);
        }

        // Validate rows
        if (!Array.isArray(table.rows)) {
            const error = this.createError(
                'rows',
                'Table rows must be an array',
                'array',
                typeof table.rows,
                'Rows should be an array of row arrays'
            );
            errors.push(error);
            this.logValidationError(component, error);
        } else {
            // Check if table is empty
            const hasData = table.rows.some((row: any[]) =>
                row && row.some((cell: any) => cell && cell !== '-' && cell !== '')
            );

            if (!hasData) {
                const warning = this.createError(
                    'rows',
                    'Table appears to be empty',
                    'table with data',
                    'all cells empty or "-"',
                    'Check if the parsing table generation is working correctly'
                );
                warnings.push(warning);
                this.logValidationWarn(component, warning);
            }

            // Validate each row structure
            table.rows.forEach((row: any, index: number) => {
                if (!Array.isArray(row)) {
                    const error = this.createError(
                        `rows[${index}]`,
                        'Each row must be an array',
                        'array',
                        typeof row,
                        `Row ${index} should be an array of cell values`
                    );
                    errors.push(error);
                    this.logValidationError(component, error);
                } else if (table.headers && row.length !== table.headers.length) {
                    const warning = this.createError(
                        `rows[${index}]`,
                        'Row length does not match header count',
                        `${table.headers.length} cells`,
                        row.length,
                        `Row ${index} should have ${table.headers.length} cells to match headers`
                    );
                    warnings.push(warning);
                    this.logValidationWarn(component, warning);
                }
            });
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    validateLR1States(states: any, component: string): ValidationResult {
        const errors: ValidationError[] = [];
        const warnings: ValidationError[] = [];

        if (!Array.isArray(states)) {
            const error = this.createError(
                'lr1_states',
                'LR1 states must be an array',
                'array',
                typeof states,
                'LR1 states should be an array of state objects'
            );
            errors.push(error);
            this.logValidationError(component, error);
            return { isValid: false, errors, warnings };
        }

        if (states.length === 0) {
            const warning = this.createError(
                'lr1_states',
                'No LR1 states provided',
                'non-empty array',
                states,
                'Grammar should generate at least one LR1 state'
            );
            warnings.push(warning);
            this.logValidationWarn(component, warning);
        }

        states.forEach((state: any, index: number) => {
            if (!state || typeof state !== 'object') {
                const error = this.createError(
                    `states[${index}]`,
                    'Each state must be an object',
                    'object',
                    typeof state,
                    `State ${index} should be an object with state information`
                );
                errors.push(error);
                this.logValidationError(component, error);
                return;
            }

            // Validate required state fields
            if (typeof state.state_number !== 'number') {
                const error = this.createError(
                    `states[${index}].state_number`,
                    'State number must be a number',
                    'number',
                    typeof state.state_number,
                    `State ${index} should have a numeric state_number`
                );
                errors.push(error);
                this.logValidationError(component, error);
            }

            if (!Array.isArray(state.items)) {
                const error = this.createError(
                    `states[${index}].items`,
                    'State items must be an array',
                    'array',
                    typeof state.items,
                    `State ${index} should have an items array`
                );
                errors.push(error);
                this.logValidationError(component, error);
            }

            if (!Array.isArray(state.transitions)) {
                const warning = this.createError(
                    `states[${index}].transitions`,
                    'State transitions should be an array',
                    'array',
                    typeof state.transitions,
                    `State ${index} should have a transitions array (can be empty)`
                );
                warnings.push(warning);
                this.logValidationWarn(component, warning);
            }
        });

        return { isValid: errors.length === 0, errors, warnings };
    }

    validateParsingResponse(data: any, component: string = 'ParsingResponse'): ValidationResult {
        const errors: ValidationError[] = [];
        const warnings: ValidationError[] = [];

        if (!data || typeof data !== 'object') {
            const error = this.createError(
                'root',
                'Response must be an object',
                'object',
                typeof data
            );
            errors.push(error);
            this.logValidationError(component, error);
            return { isValid: false, errors, warnings };
        }

        // Validate required fields
        if (typeof data.valid !== 'boolean') {
            const error = this.createError(
                'valid',
                'Missing or invalid valid field',
                'boolean',
                typeof data.valid
            );
            errors.push(error);
            this.logValidationError(component, error);
        }

        if (!Array.isArray(data.steps)) {
            const error = this.createError(
                'steps',
                'Missing or invalid steps field',
                'array',
                typeof data.steps
            );
            errors.push(error);
            this.logValidationError(component, error);
        } else {
            // Validate steps
            data.steps.forEach((step: any, index: number) => {
                const stepResult = this.validateDerivationStep(step, `${component}.steps[${index}]`);
                errors.push(...stepResult.errors);
                warnings.push(...stepResult.warnings);
            });
        }

        if (typeof data.total_steps !== 'number') {
            const error = this.createError(
                'total_steps',
                'Missing or invalid total_steps field',
                'number',
                typeof data.total_steps
            );
            errors.push(error);
            this.logValidationError(component, error);
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    private validateDerivationStep(step: any, component: string): ValidationResult {
        const errors: ValidationError[] = [];
        const warnings: ValidationError[] = [];

        if (!step || typeof step !== 'object') {
            const error = this.createError(
                'step',
                'Step must be an object',
                'object',
                typeof step
            );
            errors.push(error);
            this.logValidationError(component, error);
            return { isValid: false, errors, warnings };
        }

        // Validate required fields
        if (typeof step.step_number !== 'number') {
            const error = this.createError(
                'step_number',
                'Step number must be a number',
                'number',
                typeof step.step_number
            );
            errors.push(error);
            this.logValidationError(component, error);
        }

        if (!Array.isArray(step.stack)) {
            const error = this.createError(
                'stack',
                'Step stack must be an array',
                'array',
                typeof step.stack
            );
            errors.push(error);
            this.logValidationError(component, error);
        }

        if (!step.action || typeof step.action !== 'object') {
            const error = this.createError(
                'action',
                'Step action must be an object',
                'object',
                typeof step.action
            );
            errors.push(error);
            this.logValidationError(component, error);
        } else {
            // Validate action structure
            if (typeof step.action.type !== 'string') {
                const error = this.createError(
                    'action.type',
                    'Action type must be a string',
                    'string',
                    typeof step.action.type
                );
                errors.push(error);
                this.logValidationError(component, error);
            } else if (!['shift', 'reduce', 'accept', 'error'].includes(step.action.type)) {
                const error = this.createError(
                    'action.type',
                    'Invalid action type',
                    'shift, reduce, accept, or error',
                    step.action.type,
                    'Action type should be one of: shift, reduce, accept, error'
                );
                errors.push(error);
                this.logValidationError(component, error);
            }
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    // Type guards
    isGrammarValidationResponse(data: any): data is GrammarValidationResponse {
        const result = this.validateGrammarResponse(data);
        return result.isValid;
    }

    isParsingTableResponse(data: any): data is ParsingTableResponse {
        if (!data || typeof data !== 'object') return false;

        const actionResult = this.validateTableStructure(data.action_table, 'action_table');
        const gotoResult = this.validateTableStructure(data.goto_table, 'goto_table');

        return actionResult.isValid && gotoResult.isValid;
    }

    isInteractiveDerivationResponse(data: any): data is InteractiveDerivationResponse {
        const result = this.validateParsingResponse(data);
        return result.isValid;
    }

    isLR1State(data: any): data is LR1State {
        if (!data || typeof data !== 'object') return false;

        return typeof data.state_number === 'number' &&
            Array.isArray(data.items) &&
            Array.isArray(data.shift_symbols) &&
            Array.isArray(data.reduce_items) &&
            Array.isArray(data.transitions);
    }

    isInteractiveDerivationStep(data: any): data is InteractiveDerivationStep {
        if (!data || typeof data !== 'object') return false;

        return typeof data.step_number === 'number' &&
            Array.isArray(data.stack) &&
            Array.isArray(data.input_remaining) &&
            data.action && typeof data.action === 'object' &&
            typeof data.explanation === 'string';
    }

    // User-friendly error messages
    getUserFriendlyMessage(error: ValidationError): string {
        const suggestions = {
            'table appears to be empty': 'The parsing table is not being generated correctly. This might be due to a grammar parsing issue or backend error.',
            'missing action table': 'The grammar validation response is missing the action table. Check if the backend is generating tables correctly.',
            'missing goto table': 'The grammar validation response is missing the goto table. Check if the backend is generating tables correctly.',
            'invalid lr1_states format': 'The automaton states are not in the expected format. This will cause the automaton visualization to fail.',
            'missing step action': 'A parsing step is missing its action information. This will cause the step-by-step visualization to fail.',
        };

        const key = error.message.toLowerCase();
        const suggestion = Object.entries(suggestions).find(([k]) => key.includes(k))?.[1];

        return suggestion || error.message;
    }

    // Show user-friendly error notification
    showUserError(error: ValidationError, component: string): void {
        if (!this.showUserErrors) return;

        const message = this.getUserFriendlyMessage(error);
        logger.error('USER_ERROR', `${component}: ${message}`, {
            field: error.field,
            suggestion: error.suggestion,
        });

        // In a real app, you might show a toast notification here
        console.error(`🚨 ${component} Error: ${message}`);
    }

    // Batch validation with user notifications
    validateWithUserFeedback(data: any, component: string, validator: (data: any, component: string) => ValidationResult): ValidationResult {
        const result = validator(data, component);

        if (!result.isValid) {
            result.errors.forEach(error => this.showUserError(error, component));
        }

        if (result.warnings.length > 0) {
            result.warnings.forEach(warning => {
                logger.warn('USER_WARNING', `${component}: ${warning.message}`, {
                    field: warning.field,
                    suggestion: warning.suggestion,
                });
            });
        }

        return result;
    }
}

// Create singleton instance
export const dataValidator = new DataValidator(true);

// Export types and utilities
export { DataValidator };
export type { ValidationError, ValidationResult };
