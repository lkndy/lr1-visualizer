import React, { useEffect } from 'react';
import { useParserStore } from './store/parserStore';
import { Header } from './components/Header';
import { GrammarEditor } from './components/GrammarEditor';
import { ParsingTable } from './components/ParsingTable';
import { AutomatonView } from './components/AutomatonView';
import { StackVisualizer } from './components/StackVisualizer';
import { ASTVisualizer } from './components/ASTVisualizer';
import { StepControls } from './components/StepControls';
import { InputPanel } from './components/InputPanel';
import { ExamplesPanel } from './components/ExamplesPanel';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ErrorDisplay } from './components/ErrorDisplay';

function App() {
  const {
    activeTab,
    setActiveTab,
    grammarValid,
    isGeneratingTable,
    generateParsingTable,
    actionTable,
    gotoTable,
    parsingSteps,
    currentStep,
    totalSteps,
    isPlaying,
    playSpeed,
    setPlaySpeed,
    nextStep,
    previousStep,
    play,
    pause,
    reset,
    inputString,
    setInputString,
    parseInput,
    isParsing,
    parsingValid,
    parsingError,
  } = useParserStore();

  // Auto-generate parsing table when grammar becomes valid
  useEffect(() => {
    if (grammarValid && !actionTable && !isGeneratingTable) {
      generateParsingTable();
    }
  }, [grammarValid, actionTable, isGeneratingTable, generateParsingTable]);

  // Auto-play functionality
  useEffect(() => {
    if (isPlaying && currentStep < totalSteps - 1) {
      const interval = setInterval(() => {
        nextStep();
      }, 1000 / playSpeed);

      return () => clearInterval(interval);
    } else if (isPlaying && currentStep >= totalSteps - 1) {
      pause();
    }
  }, [isPlaying, currentStep, totalSteps, playSpeed, nextStep, pause]);

  const tabs = [
    { id: 'grammar', label: 'Grammar', icon: '📝' },
    { id: 'table', label: 'Parsing Table', icon: '📊' },
    { id: 'automaton', label: 'Automaton', icon: '🔄' },
    { id: 'parse', label: 'Parse', icon: '⚡' },
  ] as const;

  const currentStepData = parsingSteps[currentStep];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Examples Panel */}
        <ExamplesPanel />
        
        {/* Tab Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-1 bg-white rounded-lg p-1 shadow-sm">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`tab-button flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'tab-button-active'
                    : 'tab-button-inactive'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Error Display */}
        <ErrorDisplay />

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Grammar Editor and Controls */}
          <div className="lg:col-span-1 space-y-6">
            {activeTab === 'grammar' && <GrammarEditor />}
            
            {activeTab === 'parse' && (
              <>
                <InputPanel />
                <StepControls />
              </>
            )}
          </div>

          {/* Right Column - Visualizations */}
          <div className="lg:col-span-2 space-y-6">
            {/* Loading States */}
            {isGeneratingTable && (
              <div className="card p-6 text-center">
                <LoadingSpinner />
                <p className="mt-4 text-gray-600">Generating parsing table...</p>
              </div>
            )}

            {isParsing && (
              <div className="card p-6 text-center">
                <LoadingSpinner />
                <p className="mt-4 text-gray-600">Parsing input...</p>
              </div>
            )}

            {/* Tab Content */}
            {activeTab === 'grammar' && (
              <div className="card p-6">
                <h2 className="text-xl font-semibold mb-4">Grammar Information</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {useParserStore.getState().grammarInfo?.num_productions || 0}
                    </div>
                    <div className="text-sm text-blue-600">Productions</div>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {useParserStore.getState().grammarInfo?.num_terminals || 0}
                    </div>
                    <div className="text-sm text-green-600">Terminals</div>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {useParserStore.getState().grammarInfo?.num_non_terminals || 0}
                    </div>
                    <div className="text-sm text-purple-600">Non-terminals</div>
                  </div>
                  <div className="bg-orange-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {useParserStore.getState().grammarInfo?.num_states || 0}
                    </div>
                    <div className="text-sm text-orange-600">States</div>
                  </div>
                </div>
                
                <div className="mt-6">
                  <div className="text-sm text-gray-600 mb-2">Grammar Type:</div>
                  <div className="text-lg font-medium">
                    {useParserStore.getState().grammarInfo?.grammar_type || 'Unknown'}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'table' && (
              <>
                <ParsingTable />
              </>
            )}

            {activeTab === 'automaton' && (
              <>
                <AutomatonView />
              </>
            )}

            {activeTab === 'parse' && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <StackVisualizer />
                  <ASTVisualizer />
                </div>
                
                {/* Parsing Steps Information */}
                {parsingSteps.length > 0 && (
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold mb-4">
                      Step {currentStep + 1} of {totalSteps}
                    </h3>
                    
                    {currentStepData && (
                      <div className="space-y-4">
                        <div>
                          <div className="text-sm text-gray-600 mb-1">Action:</div>
                          <div className="font-medium">
                            {currentStepData.action.action_type.toUpperCase()}
                            {currentStepData.action.target !== undefined && 
                              ` ${currentStepData.action.target}`
                            }
                          </div>
                        </div>
                        
                        <div>
                          <div className="text-sm text-gray-600 mb-1">Explanation:</div>
                          <div className="text-gray-800">{currentStepData.explanation}</div>
                        </div>
                        
                        {currentStepData.current_token && (
                          <div>
                            <div className="text-sm text-gray-600 mb-1">Current Token:</div>
                            <div className="font-mono bg-gray-100 px-2 py-1 rounded">
                              {currentStepData.current_token}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
