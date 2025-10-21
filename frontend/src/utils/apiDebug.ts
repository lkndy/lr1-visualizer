/** API debug utilities with request/response interception and validation. */

import { logger } from './logger';
import { LogLevel } from './logger';

export interface APIRequest {
    id: string;
    method: string;
    endpoint: string;
    url: string;
    data?: any;
    headers?: Record<string, string>;
    timestamp: string;
    duration?: number;
}

export interface APIResponse {
    id: string;
    requestId: string;
    status: number;
    statusText: string;
    data?: any;
    error?: string;
    duration: number;
    timestamp: string;
    size: number;
}

export interface APIDebugConfig {
    enableLogging: boolean;
    enableValidation: boolean;
    enableTiming: boolean;
    logLevel: LogLevel;
    maxRequests: number;
}

class APIDebugger {
    private config: APIDebugConfig;
    private requests: Map<string, APIRequest> = new Map();
    private responses: APIResponse[] = [];
    private requestCounter = 0;

    constructor(config: Partial<APIDebugConfig> = {}) {
        this.config = {
            enableLogging: true,
            enableValidation: true,
            enableTiming: true,
            logLevel: LogLevel.DEBUG,
            maxRequests: 100,
            ...config,
        };
    }

    private generateRequestId(): string {
        return `req_${++this.requestCounter}_${Date.now()}`;
    }

    private shouldLog(): boolean {
        return this.config.enableLogging && logger.getLogs().length > 0;
    }

    private logRequest(request: APIRequest): void {
        if (!this.shouldLog()) return;

        logger.apiRequest(
            request.method,
            request.endpoint,
            request.data,
            request.id
        );

        if (this.config.enableTiming) {
            logger.debug('API', `Request ${request.id} started`, {
                method: request.method,
                endpoint: request.endpoint,
                url: request.url,
            });
        }
    }

    private logResponse(response: APIResponse): void {
        if (!this.shouldLog()) return;

        logger.apiResponse(
            response.requestId,
            response.status,
            response.duration,
            response.data,
            response.requestId
        );

        if (response.error) {
            logger.apiError(response.requestId, response.error, response.requestId);
        }

        if (this.config.enableTiming) {
            logger.debug('API', `Response ${response.requestId} completed`, {
                status: response.status,
                duration: response.duration,
                size: response.size,
            });
        }
    }

    private validateResponse(response: APIResponse): string[] {
        if (!this.config.enableValidation) return [];

        const errors: string[] = [];

        // Basic response validation
        if (response.status < 100 || response.status >= 600) {
            errors.push(`Invalid status code: ${response.status}`);
        }

        if (response.duration < 0) {
            errors.push(`Invalid duration: ${response.duration}ms`);
        }

        if (response.size < 0) {
            errors.push(`Invalid response size: ${response.size} bytes`);
        }

        // Content validation based on endpoint
        if (response.data) {
            const endpointErrors = this.validateResponseData(response.requestId, response.data);
            errors.push(...endpointErrors);
        }

        return errors;
    }

    private validateResponseData(endpoint: string, data: any): string[] {
        const errors: string[] = [];

        try {
            if (endpoint.includes('/grammar/validate')) {
                errors.push(...this.validateGrammarResponse(data));
            } else if (endpoint.includes('/parse/interactive')) {
                errors.push(...this.validateParsingResponse(data));
            } else if (endpoint.includes('/parser/table')) {
                errors.push(...this.validateTableResponse(data));
            }
        } catch (error) {
            errors.push(`Validation error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }

        return errors;
    }

    private validateGrammarResponse(data: any): string[] {
        const errors: string[] = [];

        if (!data || typeof data !== 'object') {
            errors.push('Response data must be an object');
            return errors;
        }

        if (typeof data.valid !== 'boolean') {
            errors.push('Missing or invalid "valid" field');
        }

        if (!Array.isArray(data.errors)) {
            errors.push('Missing or invalid "errors" field');
        }

        if (data.grammar_info && typeof data.grammar_info === 'object') {
            const grammarInfo = data.grammar_info;

            if (grammar_info.parsing_table_preview) {
                const preview = grammar_info.parsing_table_preview;

                if (!preview.action_table || !preview.goto_table) {
                    errors.push('Missing parsing table preview data');
                } else {
                    errors.push(...this.validateTableStructure(preview.action_table, 'action_table'));
                    errors.push(...this.validateTableStructure(preview.goto_table, 'goto_table'));
                }
            }

            if (grammar_info.lr1_states && !Array.isArray(grammar_info.lr1_states)) {
                errors.push('Invalid lr1_states format');
            }
        }

        return errors;
    }

    private validateParsingResponse(data: any): string[] {
        const errors: string[] = [];

        if (!data || typeof data !== 'object') {
            errors.push('Response data must be an object');
            return errors;
        }

        if (typeof data.valid !== 'boolean') {
            errors.push('Missing or invalid "valid" field');
        }

        if (!Array.isArray(data.steps)) {
            errors.push('Missing or invalid "steps" field');
        }

        if (typeof data.total_steps !== 'number') {
            errors.push('Missing or invalid "total_steps" field');
        }

        if (typeof data.success !== 'boolean') {
            errors.push('Missing or invalid "success" field');
        }

        // Validate steps structure
        if (Array.isArray(data.steps)) {
            data.steps.forEach((step: any, index: number) => {
                if (!step || typeof step !== 'object') {
                    errors.push(`Invalid step at index ${index}`);
                    return;
                }

                if (typeof step.step_number !== 'number') {
                    errors.push(`Step ${index}: missing step_number`);
                }

                if (!Array.isArray(step.stack)) {
                    errors.push(`Step ${index}: invalid stack format`);
                }

                if (!step.action || typeof step.action !== 'object') {
                    errors.push(`Step ${index}: missing or invalid action`);
                }
            });
        }

        return errors;
    }

    private validateTableResponse(data: any): string[] {
        const errors: string[] = [];

        if (!data || typeof data !== 'object') {
            errors.push('Response data must be an object');
            return errors;
        }

        if (data.action_table) {
            errors.push(...this.validateTableStructure(data.action_table, 'action_table'));
        }

        if (data.goto_table) {
            errors.push(...this.validateTableStructure(data.goto_table, 'goto_table'));
        }

        return errors;
    }

    private validateTableStructure(table: any, tableName: string): string[] {
        const errors: string[] = [];

        if (!table || typeof table !== 'object') {
            errors.push(`${tableName} must be an object`);
            return errors;
        }

        if (!Array.isArray(table.headers)) {
            errors.push(`${tableName}.headers must be an array`);
        }

        if (!Array.isArray(table.rows)) {
            errors.push(`${tableName}.rows must be an array`);
        } else {
            // Validate each row
            table.rows.forEach((row: any, index: number) => {
                if (!Array.isArray(row)) {
                    errors.push(`${tableName}.rows[${index}] must be an array`);
                }
            });

            // Check if table is empty (all cells are empty or "-")
            const hasData = table.rows.some((row: any[]) =>
                row.some((cell: any) => cell && cell !== '-' && cell !== '')
            );

            if (!hasData) {
                errors.push(`${tableName} appears to be empty (all cells are empty or "-")`);
            }
        }

        return errors;
    }

    // Public methods
    startRequest(method: string, endpoint: string, url: string, data?: any, headers?: Record<string, string>): string {
        const requestId = this.generateRequestId();
        const request: APIRequest = {
            id: requestId,
            method,
            endpoint,
            url,
            data,
            headers,
            timestamp: new Date().toISOString(),
        };

        this.requests.set(requestId, request);
        this.logRequest(request);

        return requestId;
    }

    endRequest(requestId: string, status: number, statusText: string, data?: any, error?: string): void {
        const request = this.requests.get(requestId);
        if (!request) {
            logger.warn('API', `Request ${requestId} not found for completion`);
            return;
        }

        const duration = Date.now() - new Date(request.timestamp).getTime();
        const response: APIResponse = {
            id: `resp_${Date.now()}`,
            requestId,
            status,
            statusText,
            data,
            error,
            duration,
            timestamp: new Date().toISOString(),
            size: data ? JSON.stringify(data).length : 0,
        };

        // Update request with duration
        request.duration = duration;
        this.requests.set(requestId, request);

        // Add response
        this.responses.push(response);
        if (this.responses.length > this.config.maxRequests) {
            this.responses.shift();
        }

        // Validate response
        if (this.config.enableValidation) {
            const validationErrors = this.validateResponse(response);
            if (validationErrors.length > 0) {
                logger.validationWarn('API', `Response validation failed: ${validationErrors.join(', ')}`, {
                    requestId,
                    errors: validationErrors,
                });
            }
        }

        this.logResponse(response);
    }

    getRequest(requestId: string): APIRequest | undefined {
        return this.requests.get(requestId);
    }

    getRecentRequests(limit: number = 50): APIRequest[] {
        return Array.from(this.requests.values()).slice(-limit);
    }

    getRecentResponses(limit: number = 50): APIResponse[] {
        return this.responses.slice(-limit);
    }

    getFailedRequests(): APIResponse[] {
        return this.responses.filter(response => response.status >= 400);
    }

    getSlowRequests(threshold: number = 1000): APIResponse[] {
        return this.responses.filter(response => response.duration > threshold);
    }

    getStats(): Record<string, any> {
        const totalRequests = this.requests.size;
        const totalResponses = this.responses.length;
        const failedRequests = this.getFailedRequests().length;
        const slowRequests = this.getSlowRequests().length;

        const statusCounts: Record<number, number> = {};
        this.responses.forEach(response => {
            statusCounts[response.status] = (statusCounts[response.status] || 0) + 1;
        });

        const avgDuration = this.responses.length > 0
            ? this.responses.reduce((sum, r) => sum + r.duration, 0) / this.responses.length
            : 0;

        return {
            totalRequests,
            totalResponses,
            failedRequests,
            slowRequests,
            successRate: totalResponses > 0 ? ((totalResponses - failedRequests) / totalResponses) * 100 : 0,
            avgDuration: Math.round(avgDuration),
            statusCounts,
        };
    }

    clearHistory(): void {
        this.requests.clear();
        this.responses = [];
        this.requestCounter = 0;
        logger.info('API', 'Request/response history cleared');
    }

    setConfig(config: Partial<APIDebugConfig>): void {
        this.config = { ...this.config, ...config };
    }

    exportData(): string {
        const data = {
            requests: Array.from(this.requests.values()),
            responses: this.responses,
            stats: this.getStats(),
            timestamp: new Date().toISOString(),
        };

        return JSON.stringify(data, null, 2);
    }
}

// Create singleton instance
export const apiDebugger = new APIDebugger();

// Export types and utilities
export { APIDebugger };
export type { APIRequest, APIResponse, APIDebugConfig };
