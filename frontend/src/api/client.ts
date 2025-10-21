/** Typed API client for LR(1) parser backend. */

import { GrammarValidationResponse, InteractiveDerivationResponse, ExampleGrammarsResponse } from '../types/parser';

// API configuration
const API_BASE = 'http://localhost:8000/api/v1';
const TIMEOUTS = {
    validation: 10000, // 10s for grammar validation
    parsing: 15000,    // 15s for parsing
    examples: 5000,    // 5s for examples
} as const;

// Error types
export class APIError extends Error {
    constructor(
        message: string,
        public status?: number,
        public endpoint?: string
    ) {
        super(message);
        this.name = 'APIError';
    }
}

export class TimeoutError extends Error {
    constructor(endpoint: string, timeout: number) {
        super(`Request to ${endpoint} timed out after ${timeout}ms`);
        this.name = 'TimeoutError';
    }
}

// Request/Response logging
function logRequest(method: string, endpoint: string, data?: any) {
    console.log(`🌐 [API] ${method} ${endpoint}`, data ? { dataSize: JSON.stringify(data).length } : '');
}

function logResponse(endpoint: string, status: number, duration: number) {
    const emoji = status >= 200 && status < 300 ? '✅' : '❌';
    console.log(`${emoji} [API] ${endpoint} ${status} (${duration}ms)`);
}

// Fetch wrapper with timeout and error handling
async function fetchWithTimeout(
    url: string,
    options: RequestInit,
    timeout: number
): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error instanceof Error && error.name === 'AbortError') {
            throw new TimeoutError(url, timeout);
        }
        throw error;
    }
}

// Retry logic for network failures
async function fetchWithRetry(
    url: string,
    options: RequestInit,
    timeout: number,
    maxRetries = 2
): Promise<Response> {
    let lastError: Error;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetchWithTimeout(url, options, timeout);

            // Don't retry on client errors (4xx)
            if (response.status >= 400 && response.status < 500) {
                return response;
            }

            // Don't retry on success
            if (response.ok) {
                return response;
            }

            // Retry on server errors (5xx) or network errors
            if (attempt === maxRetries) {
                return response;
            }

            // Wait before retry (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));

        } catch (error) {
            lastError = error as Error;

            if (attempt === maxRetries) {
                break;
            }

            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        }
    }

    throw lastError!;
}

// Generic API call function
async function apiCall<T>(
    endpoint: string,
    options: RequestInit,
    timeout: number
): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const startTime = Date.now();

    logRequest(options.method || 'GET', endpoint, options.body ? JSON.parse(options.body as string) : undefined);

    try {
        const response = await fetchWithRetry(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        const duration = Date.now() - startTime;
        logResponse(endpoint, response.status, duration);

        if (!response.ok) {
            let errorMessage = `Request failed with status ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
            } catch {
                // If we can't parse the error response, use the status text
                errorMessage = response.statusText || errorMessage;
            }

            throw new APIError(errorMessage, response.status, endpoint);
        }

        const data = await response.json();
        return data as T;

    } catch (error) {
        const duration = Date.now() - startTime;
        logResponse(endpoint, 0, duration);

        if (error instanceof APIError || error instanceof TimeoutError) {
            throw error;
        }

        throw new APIError(
            `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
            undefined,
            endpoint
        );
    }
}

// API functions
export async function validateGrammar(
    grammarText: string,
    startSymbol: string
): Promise<GrammarValidationResponse> {
    return apiCall<GrammarValidationResponse>(
        '/grammar/validate',
        {
            method: 'POST',
            body: JSON.stringify({
                grammar_text: grammarText,
                start_symbol: startSymbol,
            }),
        },
        TIMEOUTS.validation
    );
}

export async function parseInteractive(
    grammarText: string,
    inputString: string,
    startSymbol: string
): Promise<InteractiveDerivationResponse> {
    return apiCall<InteractiveDerivationResponse>(
        '/parse/interactive',
        {
            method: 'POST',
            body: JSON.stringify({
                grammar_text: grammarText,
                input_string: inputString,
                start_symbol: startSymbol,
            }),
        },
        TIMEOUTS.parsing
    );
}

export async function getExampleGrammars(): Promise<ExampleGrammarsResponse> {
    return apiCall<ExampleGrammarsResponse>(
        '/examples',
        {
            method: 'GET',
        },
        TIMEOUTS.examples
    );
}

// Legacy function for backward compatibility (deprecated)
export async function parseInput(
    grammarText: string,
    inputString: string,
    startSymbol: string
): Promise<InteractiveDerivationResponse> {
    console.warn('parseInput is deprecated, use parseInteractive instead');
    return parseInteractive(grammarText, inputString, startSymbol);
}

// Utility function to check if API is available
export async function checkAPIHealth(): Promise<boolean> {
    try {
        await fetch(`${API_BASE}/examples`, { method: 'GET' });
        return true;
    } catch {
        return false;
    }
}
