/** Debug mode hook with keyboard shortcuts and settings. */

import { useState, useEffect, useCallback } from 'react';
import { logger } from '../utils/logger';
import { apiDebugger } from '../utils/apiDebug';

export interface DebugModeConfig {
    enabled: boolean;
    logLevel: 'ERROR' | 'WARN' | 'INFO' | 'DEBUG';
    showDebugPanel: boolean;
    enableApiLogging: boolean;
    enableValidation: boolean;
    enableTiming: boolean;
    maxLogs: number;
}

const DEFAULT_CONFIG: DebugModeConfig = {
    enabled: false,
    logLevel: 'DEBUG',
    showDebugPanel: false,
    enableApiLogging: true,
    enableValidation: true,
    enableTiming: true,
    maxLogs: 1000,
};

const STORAGE_KEY = 'lr1-visualizer-debug-config';

export function useDebugMode() {
    const [config, setConfig] = useState<DebugModeConfig>(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                return { ...DEFAULT_CONFIG, ...JSON.parse(stored) };
            }
        } catch (error) {
            logger.warn('DEBUG_MODE', 'Failed to load debug config from localStorage', { error });
        }
        return DEFAULT_CONFIG;
    });

    // Save config to localStorage when it changes
    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
        } catch (error) {
            logger.warn('DEBUG_MODE', 'Failed to save debug config to localStorage', { error });
        }
    }, [config]);

    // Update logger configuration when config changes
    useEffect(() => {
        if (config.enabled) {
            logger.setConfig({
                level: config.logLevel === 'ERROR' ? 0 : config.logLevel === 'WARN' ? 1 : config.logLevel === 'INFO' ? 2 : 3,
                enableConsole: true,
                enableFile: true,
                maxEntries: config.maxLogs,
                enableColors: true,
            });

            apiDebugger.setConfig({
                enableLogging: config.enableApiLogging,
                enableValidation: config.enableValidation,
                enableTiming: config.enableTiming,
                logLevel: config.logLevel === 'ERROR' ? 0 : config.logLevel === 'WARN' ? 1 : config.logLevel === 'INFO' ? 2 : 3,
                maxRequests: config.maxLogs,
            });

            logger.info('DEBUG_MODE', 'Debug mode enabled', config);
        } else {
            logger.info('DEBUG_MODE', 'Debug mode disabled');
        }
    }, [config]);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            // Ctrl+Shift+D to toggle debug mode
            if (event.ctrlKey && event.shiftKey && event.key === 'D') {
                event.preventDefault();
                toggleDebugMode();
            }

            // Ctrl+Shift+P to toggle debug panel
            if (event.ctrlKey && event.shiftKey && event.key === 'P') {
                event.preventDefault();
                toggleDebugPanel();
            }

            // Ctrl+Shift+L to export logs
            if (event.ctrlKey && event.shiftKey && event.key === 'L') {
                event.preventDefault();
                exportLogs();
            }

            // Ctrl+Shift+C to clear logs
            if (event.ctrlKey && event.shiftKey && event.key === 'C') {
                event.preventDefault();
                clearLogs();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    const toggleDebugMode = useCallback(() => {
        setConfig(prev => ({
            ...prev,
            enabled: !prev.enabled,
        }));
    }, []);

    const toggleDebugPanel = useCallback(() => {
        setConfig(prev => ({
            ...prev,
            showDebugPanel: !prev.showDebugPanel,
        }));
    }, []);

    const setLogLevel = useCallback((level: DebugModeConfig['logLevel']) => {
        setConfig(prev => ({
            ...prev,
            logLevel: level,
        }));
    }, []);

    const setApiLogging = useCallback((enabled: boolean) => {
        setConfig(prev => ({
            ...prev,
            enableApiLogging: enabled,
        }));
    }, []);

    const setValidation = useCallback((enabled: boolean) => {
        setConfig(prev => ({
            ...prev,
            enableValidation: enabled,
        }));
    }, []);

    const setTiming = useCallback((enabled: boolean) => {
        setConfig(prev => ({
            ...prev,
            enableTiming: enabled,
        }));
    }, []);

    const setMaxLogs = useCallback((maxLogs: number) => {
        setConfig(prev => ({
            ...prev,
            maxLogs: Math.max(100, Math.min(10000, maxLogs)),
        }));
    }, []);

    const exportLogs = useCallback(() => {
        try {
            const filename = logger.exportLogs('json');
            logger.info('DEBUG_MODE', `Logs exported as ${filename}`);
        } catch (error) {
            logger.error('DEBUG_MODE', 'Failed to export logs', { error });
        }
    }, []);

    const exportApiLogs = useCallback(() => {
        try {
            const data = apiDebugger.exportData();
            const blob = new Blob([data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `api-logs-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            logger.info('DEBUG_MODE', 'API logs exported');
        } catch (error) {
            logger.error('DEBUG_MODE', 'Failed to export API logs', { error });
        }
    }, []);

    const clearLogs = useCallback(() => {
        logger.clearLogs();
        apiDebugger.clearHistory();
        logger.info('DEBUG_MODE', 'All logs cleared');
    }, []);

    const getStats = useCallback(() => {
        return {
            logger: logger.getStats(),
            api: apiDebugger.getStats(),
            config,
        };
    }, [config]);

    const getRecentLogs = useCallback((limit: number = 50) => {
        return {
            logger: logger.getRecentLogs(limit),
            api: apiDebugger.getRecentResponses(limit),
        };
    }, []);

    const resetConfig = useCallback(() => {
        setConfig(DEFAULT_CONFIG);
        logger.info('DEBUG_MODE', 'Debug config reset to defaults');
    }, []);

    return {
        // State
        config,
        isEnabled: config.enabled,
        showDebugPanel: config.showDebugPanel,

        // Actions
        toggleDebugMode,
        toggleDebugPanel,
        setLogLevel,
        setApiLogging,
        setValidation,
        setTiming,
        setMaxLogs,
        exportLogs,
        exportApiLogs,
        clearLogs,
        resetConfig,

        // Data
        getStats,
        getRecentLogs,

        // Keyboard shortcuts info
        shortcuts: {
            toggleDebug: 'Ctrl+Shift+D',
            togglePanel: 'Ctrl+Shift+P',
            exportLogs: 'Ctrl+Shift+L',
            clearLogs: 'Ctrl+Shift+C',
        },
    };
}
