/** Debug panel component for development tools. */

import React, { useState, useEffect } from 'react';
import { X, Download, Trash2, Settings, Activity, AlertTriangle, Info, Bug } from 'lucide-react';
import { useDebugMode } from '../hooks/useDebugMode';
import { logger } from '../utils/logger';
import { apiDebugger } from '../utils/apiDebug';

export const DebugPanel: React.FC = () => {
    const {
        config,
        isEnabled,
        showDebugPanel,
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
        getStats,
        getRecentLogs,
        shortcuts,
    } = useDebugMode();

    const [activeTab, setActiveTab] = useState<'logs' | 'api' | 'settings' | 'stats'>('logs');
    const [logs, setLogs] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);

    // Update logs and stats periodically
    useEffect(() => {
        if (!showDebugPanel) return;

        const updateData = () => {
            setLogs(getRecentLogs(100));
            setStats(getStats());
        };

        updateData();
        const interval = setInterval(updateData, 1000);
        return () => clearInterval(interval);
    }, [showDebugPanel, getRecentLogs, getStats]);

    if (!isEnabled || !showDebugPanel) {
        return null;
    }

    const logLevels = ['ERROR', 'WARN', 'INFO', 'DEBUG'] as const;

    return (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-full max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200">
                    <div className="flex items-center space-x-2">
                        <Bug className="w-5 h-5 text-blue-600" />
                        <h2 className="text-lg font-semibold">Debug Panel</h2>
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                            Active
                        </span>
                    </div>
                    <button
                        onClick={toggleDebugPanel}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-gray-200">
                    {[
                        { id: 'logs', label: 'Logs', icon: Activity },
                        { id: 'api', label: 'API', icon: Info },
                        { id: 'stats', label: 'Stats', icon: Settings },
                        { id: 'settings', label: 'Settings', icon: Settings },
                    ].map(({ id, label, icon: Icon }) => (
                        <button
                            key={id}
                            onClick={() => setActiveTab(id as any)}
                            className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === id
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            <Icon className="w-4 h-4" />
                            <span>{label}</span>
                        </button>
                    ))}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden">
                    {activeTab === 'logs' && <LogsTab logs={logs} />}
                    {activeTab === 'api' && <ApiTab logs={logs} />}
                    {activeTab === 'stats' && <StatsTab stats={stats} />}
                    {activeTab === 'settings' && (
                        <SettingsTab
                            config={config}
                            setLogLevel={setLogLevel}
                            setApiLogging={setApiLogging}
                            setValidation={setValidation}
                            setTiming={setTiming}
                            setMaxLogs={setMaxLogs}
                            exportLogs={exportLogs}
                            exportApiLogs={exportApiLogs}
                            clearLogs={clearLogs}
                            resetConfig={resetConfig}
                            shortcuts={shortcuts}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

const LogsTab: React.FC<{ logs: any }> = ({ logs }) => {
    const [filter, setFilter] = useState('');
    const [level, setLevel] = useState<string>('ALL');

    const filteredLogs = logs.logger?.filter((log: any) => {
        const matchesFilter = !filter || log.message.toLowerCase().includes(filter.toLowerCase());
        const matchesLevel = level === 'ALL' || log.level === level;
        return matchesFilter && matchesLevel;
    }) || [];

    return (
        <div className="h-full flex flex-col">
            <div className="p-4 border-b border-gray-200">
                <div className="flex space-x-4">
                    <input
                        type="text"
                        placeholder="Filter logs..."
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                    <select
                        value={level}
                        onChange={(e) => setLevel(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                        <option value="ALL">All Levels</option>
                        <option value="ERROR">Error</option>
                        <option value="WARN">Warn</option>
                        <option value="INFO">Info</option>
                        <option value="DEBUG">Debug</option>
                    </select>
                </div>
            </div>
            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-2">
                    {filteredLogs.map((log: any, index: number) => (
                        <div
                            key={index}
                            className={`p-3 rounded-lg text-sm font-mono ${log.level === 'ERROR' ? 'bg-red-50 border-l-4 border-red-500' :
                                    log.level === 'WARN' ? 'bg-yellow-50 border-l-4 border-yellow-500' :
                                        log.level === 'INFO' ? 'bg-blue-50 border-l-4 border-blue-500' :
                                            'bg-gray-50 border-l-4 border-gray-500'
                                }`}
                        >
                            <div className="flex items-center justify-between mb-1">
                                <span className="font-semibold text-gray-700">
                                    [{log.level}] {log.category}
                                </span>
                                <span className="text-xs text-gray-500">
                                    {new Date(log.timestamp).toLocaleTimeString()}
                                </span>
                            </div>
                            <div className="text-gray-800">{log.message}</div>
                            {log.data && (
                                <pre className="mt-2 text-xs text-gray-600 bg-white p-2 rounded border overflow-x-auto">
                                    {JSON.stringify(log.data, null, 2)}
                                </pre>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const ApiTab: React.FC<{ logs: any }> = ({ logs }) => {
    const apiLogs = logs.api || [];

    return (
        <div className="h-full flex flex-col">
            <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold">API Requests & Responses</h3>
            </div>
            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    {apiLogs.map((log: any, index: number) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="font-semibold text-gray-700">
                                    {log.method} {log.endpoint}
                                </span>
                                <span className={`px-2 py-1 rounded text-xs ${log.status >= 400 ? 'bg-red-100 text-red-800' :
                                        log.status >= 300 ? 'bg-yellow-100 text-yellow-800' :
                                            'bg-green-100 text-green-800'
                                    }`}>
                                    {log.status} ({log.duration}ms)
                                </span>
                            </div>
                            {log.data && (
                                <pre className="text-xs text-gray-600 bg-gray-50 p-2 rounded border overflow-x-auto">
                                    {JSON.stringify(log.data, null, 2)}
                                </pre>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const StatsTab: React.FC<{ stats: any }> = ({ stats }) => {
    if (!stats) return <div className="p-4">Loading stats...</div>;

    return (
        <div className="h-full overflow-auto p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3 text-blue-800">Logger Stats</h3>
                    <div className="space-y-2">
                        {Object.entries(stats.logger).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                                <span className="text-sm text-blue-700">{key}:</span>
                                <span className="text-sm font-mono text-blue-900">{String(value)}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3 text-green-800">API Stats</h3>
                    <div className="space-y-2">
                        {Object.entries(stats.api).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                                <span className="text-sm text-green-700">{key}:</span>
                                <span className="text-sm font-mono text-green-900">{String(value)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

const SettingsTab: React.FC<{
    config: any;
    setLogLevel: (level: any) => void;
    setApiLogging: (enabled: boolean) => void;
    setValidation: (enabled: boolean) => void;
    setTiming: (enabled: boolean) => void;
    setMaxLogs: (max: number) => void;
    exportLogs: () => void;
    exportApiLogs: () => void;
    clearLogs: () => void;
    resetConfig: () => void;
    shortcuts: any;
}> = ({
    config,
    setLogLevel,
    setApiLogging,
    setValidation,
    setTiming,
    setMaxLogs,
    exportLogs,
    exportApiLogs,
    clearLogs,
    resetConfig,
    shortcuts,
}) => {
        return (
            <div className="h-full overflow-auto p-4">
                <div className="space-y-6">
                    {/* Log Level */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Log Level
                        </label>
                        <select
                            value={config.logLevel}
                            onChange={(e) => setLogLevel(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        >
                            <option value="ERROR">Error</option>
                            <option value="WARN">Warn</option>
                            <option value="INFO">Info</option>
                            <option value="DEBUG">Debug</option>
                        </select>
                    </div>

                    {/* Features */}
                    <div className="space-y-3">
                        <h3 className="text-lg font-semibold">Features</h3>
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={config.enableApiLogging}
                                onChange={(e) => setApiLogging(e.target.checked)}
                                className="rounded"
                            />
                            <span className="text-sm">Enable API Logging</span>
                        </label>
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={config.enableValidation}
                                onChange={(e) => setValidation(e.target.checked)}
                                className="rounded"
                            />
                            <span className="text-sm">Enable Validation</span>
                        </label>
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={config.enableTiming}
                                onChange={(e) => setTiming(e.target.checked)}
                                className="rounded"
                            />
                            <span className="text-sm">Enable Timing</span>
                        </label>
                    </div>

                    {/* Max Logs */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Max Logs: {config.maxLogs}
                        </label>
                        <input
                            type="range"
                            min="100"
                            max="10000"
                            step="100"
                            value={config.maxLogs}
                            onChange={(e) => setMaxLogs(Number(e.target.value))}
                            className="w-full"
                        />
                    </div>

                    {/* Actions */}
                    <div className="space-y-3">
                        <h3 className="text-lg font-semibold">Actions</h3>
                        <div className="grid grid-cols-2 gap-3">
                            <button
                                onClick={exportLogs}
                                className="flex items-center justify-center space-x-2 px-4 py-2 bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition-colors"
                            >
                                <Download className="w-4 h-4" />
                                <span>Export Logs</span>
                            </button>
                            <button
                                onClick={exportApiLogs}
                                className="flex items-center justify-center space-x-2 px-4 py-2 bg-green-100 text-green-800 rounded-lg hover:bg-green-200 transition-colors"
                            >
                                <Download className="w-4 h-4" />
                                <span>Export API Logs</span>
                            </button>
                            <button
                                onClick={clearLogs}
                                className="flex items-center justify-center space-x-2 px-4 py-2 bg-red-100 text-red-800 rounded-lg hover:bg-red-200 transition-colors"
                            >
                                <Trash2 className="w-4 h-4" />
                                <span>Clear Logs</span>
                            </button>
                            <button
                                onClick={resetConfig}
                                className="flex items-center justify-center space-x-2 px-4 py-2 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition-colors"
                            >
                                <Settings className="w-4 h-4" />
                                <span>Reset Config</span>
                            </button>
                        </div>
                    </div>

                    {/* Keyboard Shortcuts */}
                    <div>
                        <h3 className="text-lg font-semibold mb-3">Keyboard Shortcuts</h3>
                        <div className="space-y-2">
                            {Object.entries(shortcuts).map(([action, shortcut]) => (
                                <div key={action} className="flex justify-between text-sm">
                                    <span className="text-gray-700">{action.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}:</span>
                                    <code className="bg-gray-100 px-2 py-1 rounded text-gray-800">{shortcut}</code>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    };
