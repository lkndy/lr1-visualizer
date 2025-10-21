import React, { useEffect } from 'react';
import { useParserStore } from './store/parserStore';
import { Header } from './components/Header';
import { GrammarConfigTab } from './components/GrammarConfigTab';
import { ParsingVisualizationTab } from './components/ParsingVisualizationTab';
import { ErrorDisplay } from './components/ErrorDisplay';
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  const {
    activeTab,
    setActiveTab,
    grammarValid,
  } = useParserStore();

  const tabs = [
    { id: 'grammar-config', label: 'Grammar Configuration', icon: '⚙️' },
    { id: 'parsing-viz', label: 'Parsing Visualization', icon: '🎯' },
  ] as const;

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <Header />

        <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
          {/* Tab Navigation */}
          <div className="mb-8">
            <nav className="flex space-x-1 bg-white rounded-lg p-1 shadow-sm max-w-md">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as 'grammar-config' | 'parsing-viz')}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                    }`}
                >
                  <span>{tab.icon}</span>
                  <span className="text-sm font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Error Display */}
          <ErrorDisplay />

          {/* Main Content */}
          <div className="space-y-6">
            {activeTab === 'grammar-config' && <GrammarConfigTab />}
            {activeTab === 'parsing-viz' && <ParsingVisualizationTab />}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default App;
