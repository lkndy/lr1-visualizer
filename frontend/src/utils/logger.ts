/** Centralized logging utility for both console and file output. */

export enum LogLevel {
    ERROR = 0,
    WARN = 1,
    INFO = 2,
    DEBUG = 3,
}

export interface LogEntry {
    id: string;
    timestamp: string;
    level: LogLevel;
    category: string;
    message: string;
    data?: any;
    context?: Record<string, any>;
}

export interface LoggerConfig {
    level: LogLevel;
    enableConsole: boolean;
    enableFile: boolean;
    maxEntries: number;
    enableColors: boolean;
}

class Logger {
    private config: LoggerConfig;
    private logs: LogEntry[] = [];
    private requestId: string | null = null;

    constructor(config: Partial<LoggerConfig> = {}) {
        this.config = {
            level: LogLevel.INFO,
            enableConsole: true,
            enableFile: true,
            maxEntries: 1000,
            enableColors: true,
            ...config,
        };
    }

    private generateId(): string {
        return Math.random().toString(36).substr(2, 9);
    }

    private formatTimestamp(): string {
        return new Date().toISOString();
    }

    private getColorCode(level: LogLevel): string {
        if (!this.config.enableColors) return '';

        switch (level) {
            case LogLevel.ERROR: return '\x1b[31m'; // Red
            case LogLevel.WARN: return '\x1b[33m';  // Yellow
            case LogLevel.INFO: return '\x1b[36m';  // Cyan
            case LogLevel.DEBUG: return '\x1b[90m'; // Gray
            default: return '';
        }
    }

    private getResetColor(): string {
        return this.config.enableColors ? '\x1b[0m' : '';
    }

    private getEmoji(level: LogLevel): string {
        switch (level) {
            case LogLevel.ERROR: return '❌';
            case LogLevel.WARN: return '⚠️';
            case LogLevel.INFO: return 'ℹ️';
            case LogLevel.DEBUG: return '🐛';
            default: return '';
        }
    }

    private getLevelName(level: LogLevel): string {
        switch (level) {
            case LogLevel.ERROR: return 'ERROR';
            case LogLevel.WARN: return 'WARN';
            case LogLevel.INFO: return 'INFO';
            case LogLevel.DEBUG: return 'DEBUG';
            default: return 'UNKNOWN';
        }
    }

    private shouldLog(level: LogLevel): boolean {
        return level <= this.config.level;
    }

    private addLog(level: LogLevel, category: string, message: string, data?: any, context?: Record<string, any>): void {
        if (!this.shouldLog(level)) return;

        const logEntry: LogEntry = {
            id: this.generateId(),
            timestamp: this.formatTimestamp(),
            level,
            category,
            message,
            data,
            context: {
                ...context,
                requestId: this.requestId,
            },
        };

        this.logs.push(logEntry);

        // Keep only the most recent entries
        if (this.logs.length > this.config.maxEntries) {
            this.logs.shift();
        }

        // Console output
        if (this.config.enableConsole) {
            this.logToConsole(logEntry);
        }
    }

    private logToConsole(entry: LogEntry): void {
        const color = this.getColorCode(entry.level);
        const reset = this.getResetColor();
        const emoji = this.getEmoji(entry.level);
        const levelName = this.getLevelName(entry.level);
        const requestId = entry.context?.requestId ? `[${entry.context.requestId}]` : '';

        const timestamp = new Date(entry.timestamp).toLocaleTimeString();
        const prefix = `${color}${emoji} [${timestamp}] ${levelName}${requestId} [${entry.category}]${reset}`;

        if (entry.data) {
            console.log(prefix, entry.message, entry.data);
        } else {
            console.log(prefix, entry.message);
        }
    }

    // Public logging methods
    error(category: string, message: string, data?: any, context?: Record<string, any>): void {
        this.addLog(LogLevel.ERROR, category, message, data, context);
    }

    warn(category: string, message: string, data?: any, context?: Record<string, any>): void {
        this.addLog(LogLevel.WARN, category, message, data, context);
    }

    info(category: string, message: string, data?: any, context?: Record<string, any>): void {
        this.addLog(LogLevel.INFO, category, message, data, context);
    }

    debug(category: string, message: string, data?: any, context?: Record<string, any>): void {
        this.addLog(LogLevel.DEBUG, category, message, data, context);
    }

    // API-specific logging methods
    apiRequest(method: string, endpoint: string, data?: any, requestId?: string): void {
        this.setRequestId(requestId);
        this.info('API', `${method} ${endpoint}`, data, { method, endpoint });
    }

    apiResponse(endpoint: string, status: number, duration: number, data?: any, requestId?: string): void {
        const level = status >= 400 ? LogLevel.ERROR : status >= 300 ? LogLevel.WARN : LogLevel.INFO;
        const emoji = status >= 400 ? '❌' : status >= 300 ? '⚠️' : '✅';
        this.addLog(level, 'API', `${emoji} ${endpoint} ${status} (${duration}ms)`, data, {
            endpoint,
            status,
            duration,
            requestId
        });
    }

    apiError(endpoint: string, error: string, requestId?: string): void {
        this.error('API', `❌ ${endpoint} failed: ${error}`, null, { endpoint, requestId });
    }

    // Validation logging
    validationError(component: string, message: string, data?: any): void {
        this.error('VALIDATION', `${component}: ${message}`, data, { component });
    }

    validationWarn(component: string, message: string, data?: any): void {
        this.warn('VALIDATION', `${component}: ${message}`, data, { component });
    }

    // State management logging
    stateChange(store: string, action: string, data?: any): void {
        this.debug('STORE', `${store}: ${action}`, data, { store, action });
    }

    // Component lifecycle logging
    componentMount(component: string, props?: any): void {
        this.debug('COMPONENT', `Mount: ${component}`, props, { component, lifecycle: 'mount' });
    }

    componentUnmount(component: string): void {
        this.debug('COMPONENT', `Unmount: ${component}`, null, { component, lifecycle: 'unmount' });
    }

    componentError(component: string, error: string, props?: any): void {
        this.error('COMPONENT', `${component} error: ${error}`, props, { component });
    }

    // Configuration methods
    setLevel(level: LogLevel): void {
        this.config.level = level;
    }

    setRequestId(requestId: string | null): void {
        this.requestId = requestId;
    }

    setConfig(config: Partial<LoggerConfig>): void {
        this.config = { ...this.config, ...config };
    }

    // Log management
    getLogs(level?: LogLevel, category?: string, limit?: number): LogEntry[] {
        let filtered = this.logs;

        if (level !== undefined) {
            filtered = filtered.filter(log => log.level === level);
        }

        if (category) {
            filtered = filtered.filter(log => log.category === category);
        }

        if (limit) {
            filtered = filtered.slice(-limit);
        }

        return filtered;
    }

    getRecentLogs(limit: number = 50): LogEntry[] {
        return this.getLogs(undefined, undefined, limit);
    }

    clearLogs(): void {
        this.logs = [];
        this.info('LOGGER', 'Logs cleared');
    }

    // Export functionality
    exportLogs(format: 'json' | 'csv' = 'json'): string {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `debug-logs-${timestamp}.${format}`;

        if (format === 'json') {
            const data = JSON.stringify(this.logs, null, 2);
            this.downloadFile(filename, data, 'application/json');
        } else if (format === 'csv') {
            const csv = this.logsToCSV(this.logs);
            this.downloadFile(filename, csv, 'text/csv');
        }

        this.info('LOGGER', `Logs exported as ${filename}`);
        return filename;
    }

    private logsToCSV(logs: LogEntry[]): string {
        if (logs.length === 0) return '';

        const headers = ['timestamp', 'level', 'category', 'message', 'data', 'context'];
        const rows = logs.map(log => [
            log.timestamp,
            this.getLevelName(log.level),
            log.category,
            log.message,
            log.data ? JSON.stringify(log.data) : '',
            log.context ? JSON.stringify(log.context) : '',
        ]);

        return [headers, ...rows]
            .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
            .join('\n');
    }

    private downloadFile(filename: string, content: string, mimeType: string): void {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    // Statistics
    getStats(): Record<string, number> {
        const stats: Record<string, number> = {};

        this.logs.forEach(log => {
            const level = this.getLevelName(log.level);
            stats[level] = (stats[level] || 0) + 1;

            const categoryKey = `${level}_${log.category}`;
            stats[categoryKey] = (stats[categoryKey] || 0) + 1;
        });

        stats.total = this.logs.length;
        return stats;
    }
}

// Create singleton instance
export const logger = new Logger({
    level: LogLevel.DEBUG,
    enableConsole: true,
    enableFile: true,
    maxEntries: 1000,
    enableColors: true,
});

// Export types and utilities
export { Logger };
export type { LogEntry, LoggerConfig };
