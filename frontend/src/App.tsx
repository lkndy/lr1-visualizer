import React, { useEffect, useState } from 'react';
import { Reorder, motion } from 'framer-motion';
import { useParserStore } from './store/parserStore';
import { Header } from './components/Header';
import { GrammarConfigTab } from './components/GrammarConfigTab';
import { ParsingVisualizationTab } from './components/ParsingVisualizationTab';
import { AutomatonTab } from './components/AutomatonTab';
import { ErrorDisplay } from './components/ErrorDisplay';
import { ErrorBoundary } from './components/ErrorBoundary';
import { DebugPanel } from './components/DebugPanel';
import { useDebugMode } from './hooks/useDebugMode';

function App() {
  const {
    activeTab,
    setActiveTab,
    grammarValid,
  } = useParserStore();

  const { showDebugPanel } = useDebugMode();

  // Define tabs with reordering support
  const [tabs, setTabs] = useState([
    { id: 'grammar-config', label: 'Grammar Configuration', icon: '⚙️' },
    { id: 'parsing-viz', label: 'Parsing Visualization', icon: '🎯' },
    { id: 'automaton', label: 'LR(1) Automaton', icon: '🔄' },
  ]);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <Header />

        <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
          {/* Tab Navigation - Centered with Reordering */}
          <div className="mb-8 flex justify-center">
            <nav className="bg-white rounded-lg p-1 shadow-sm">
              <Reorder.Group
                axis="x"
                values={tabs}
                onReorder={setTabs}
                className="flex space-x-1"
                layoutScroll
              >
                {tabs.map((tab) => (
                  <Reorder.Item
                    key={tab.id}
                    value={tab}
                    className="cursor-grab active:cursor-grabbing"
                    whileDrag={{
                      scale: 1.05,
                      zIndex: 1000,
                      rotate: 2,
                      boxShadow: "0 10px 25px rgba(0,0,0,0.2)"
                    }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  >
                    <button
                      onClick={() => setActiveTab(tab.id as 'grammar-config' | 'parsing-viz' | 'automaton')}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all duration-200 ease-in-out ${activeTab === tab.id
                          ? 'bg-blue-600 text-white shadow-sm transform scale-105'
                          : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100 hover:transform hover:scale-102'
                        }`}
                    >
                      <span className="text-lg">{tab.icon}</span>
                      <span className="text-sm font-medium">{tab.label}</span>
                    </button>
                  </Reorder.Item>
                ))}
              </Reorder.Group>
            </nav>
          </div>

          {/* Error Display */}
          <ErrorDisplay />

          {/* Main Content with Smooth Transitions */}
          <div className="space-y-6">
            <div className="relative">
              {activeTab === 'grammar-config' && (
                <motion.div
                  key="grammar-config"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                >
                  <GrammarConfigTab />
                </motion.div>
              )}
              {activeTab === 'parsing-viz' && (
                <motion.div
                  key="parsing-viz"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                >
                  <ParsingVisualizationTab />
                </motion.div>
              )}
              {activeTab === 'automaton' && (
                <motion.div
                  key="automaton"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                >
                  <AutomatonTab />
                </motion.div>
              )}
            </div>
          </div>
        </div>

        {/* Debug Panel */}
        {showDebugPanel && <DebugPanel />}
      </div>
    </ErrorBoundary>
  );
}

export default App;
