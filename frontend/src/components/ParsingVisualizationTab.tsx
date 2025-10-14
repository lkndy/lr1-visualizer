import React, { useState } from 'react';
import { Play, Pause, RotateCcw, ChevronLeft, ChevronRight, Zap, Target, Info } from 'lucide-react';
import { useParserStore } from '../store/parserStore';
import { StackVisualizer } from './StackVisualizer';
import { ASTVisualizer } from './ASTVisualizer';
import { StepControls } from './StepControls';
import { LoadingSpinner } from './LoadingSpinner';

export const ParsingVisualizationTab: React.FC = () => {
    const {
        grammarValid,
        inputString,
        selectedSampleString,
        availableSampleStrings,
        parsingSteps,
        currentStep,
        totalSteps,
        isPlaying,
        playSpeed,
        isParsing,
        parsingValid,
        parsingError,
        currentStepData,
        setInputString,
        selectSampleString,
        parseInput,
        setCurrentStep,
        nextStep,
        previousStep,
        play,
        pause,
        reset,
        setPlaySpeed,
    } = useParserStore();

    const [customInput, setCustomInput] = useState('');

    const handleSampleSelect = (sample: string) => {
        selectSampleString(sample);
        setCustomInput('');
    };

    const handleCustomInput = (input: string) => {
        setCustomInput(input);
        setInputString(input);
    };

    const handleParse = async () => {
        await parseInput();
    };

    if (!grammarValid) {
        return (
            <div className="card p-12 text-center">
                <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">Grammar Required</h3>
                <p className="text-gray-600">
                    Please configure a valid grammar in the Grammar Configuration tab before parsing strings.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Input Panel */}
            <div className="card p-6">
                <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
                    <Zap className="w-5 h-5 text-blue-600" />
                    <span>Input String</span>
                </h2>

                {/* Sample Strings */}
                {availableSampleStrings.length > 0 && (
                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Sample Strings
                        </label>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                            {availableSampleStrings.map((sample, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleSampleSelect(sample)}
                                    className={`p-3 text-left rounded-lg border transition-colors ${selectedSampleString === sample
                                        ? 'border-blue-500 bg-blue-50 text-blue-900'
                                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                        }`}
                                >
                                    <code className="text-sm font-mono">{sample}</code>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Custom Input */}
                <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Custom Input
                    </label>
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={customInput}
                            onChange={(e) => handleCustomInput(e.target.value)}
                            placeholder="Enter a string to parse..."
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <button
                            onClick={handleParse}
                            disabled={!inputString.trim() || isParsing}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                        >
                            {isParsing ? (
                                <LoadingSpinner />
                            ) : (
                                <Play className="w-4 h-4" />
                            )}
                            <span>Parse</span>
                        </button>
                    </div>
                </div>

                {/* Current Input Display */}
                {inputString && (
                    <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                        <div className="text-sm text-gray-600 mb-1">Current Input:</div>
                        <code className="text-lg font-mono text-gray-900">{inputString}</code>
                    </div>
                )}
            </div>

            {/* Error Display */}
            {parsingError && (
                <div className="card p-6 bg-red-50 border border-red-200">
                    <div className="flex items-center space-x-2 text-red-800">
                        <Info className="w-5 h-5" />
                        <span className="font-medium">Parsing Error</span>
                    </div>
                    <p className="mt-2 text-red-700">{parsingError}</p>
                </div>
            )}

            {/* Parsing Results */}
            {parsingSteps.length > 0 && (
                <>
                    {/* Step Controls */}
                    <div className="card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold">Parsing Steps</h3>
                            <div className="flex items-center space-x-4">
                                <span className="text-sm text-gray-600">
                                    Step {currentStep + 1} of {totalSteps}
                                </span>
                                <div className="flex items-center space-x-2">
                                    <button
                                        onClick={previousStep}
                                        disabled={currentStep === 0}
                                        className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <ChevronLeft className="w-4 h-4" />
                                    </button>

                                    {isPlaying ? (
                                        <button
                                            onClick={pause}
                                            className="p-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                                        >
                                            <Pause className="w-4 h-4" />
                                        </button>
                                    ) : (
                                        <button
                                            onClick={play}
                                            disabled={currentStep >= totalSteps - 1}
                                            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            <Play className="w-4 h-4" />
                                        </button>
                                    )}

                                    <button
                                        onClick={nextStep}
                                        disabled={currentStep >= totalSteps - 1}
                                        className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <ChevronRight className="w-4 h-4" />
                                    </button>

                                    <button
                                        onClick={reset}
                                        className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50"
                                    >
                                        <RotateCcw className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Speed Control */}
                        <div className="flex items-center space-x-4 mb-4">
                            <label className="text-sm text-gray-600">Speed:</label>
                            <input
                                type="range"
                                min="0.1"
                                max="3"
                                step="0.1"
                                value={playSpeed}
                                onChange={(e) => setPlaySpeed(parseFloat(e.target.value))}
                                className="flex-1 max-w-32"
                            />
                            <span className="text-sm text-gray-600">{playSpeed}x</span>
                        </div>

                        {/* Step Information */}
                        {currentStepData && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                <div>
                                    <div className="text-sm text-blue-600 mb-1">Action:</div>
                                    <div className="font-medium text-blue-900">
                                        {currentStepData.action.action_type.toUpperCase()}
                                        {currentStepData.action.target !== undefined &&
                                            ` ${currentStepData.action.target}`
                                        }
                                    </div>
                                </div>

                                <div>
                                    <div className="text-sm text-blue-600 mb-1">Current Token:</div>
                                    <div className="font-mono text-blue-900">
                                        {currentStepData.current_token || 'None'}
                                    </div>
                                </div>

                                <div className="md:col-span-2">
                                    <div className="text-sm text-blue-600 mb-1">Explanation:</div>
                                    <div className="text-blue-800">{currentStepData.explanation}</div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Visualizations */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Stack Visualizer */}
                        <div className="card p-6">
                            <h3 className="text-lg font-semibold mb-4">Parser Stack</h3>
                            <StackVisualizer />
                        </div>

                        {/* AST Visualizer */}
                        <div className="card p-6">
                            <h3 className="text-lg font-semibold mb-4">Abstract Syntax Tree</h3>
                            <ASTVisualizer />
                        </div>
                    </div>

                    {/* Parsing Summary */}
                    <div className="card p-6">
                        <h3 className="text-lg font-semibold mb-4">Parsing Summary</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-green-50 p-4 rounded-lg">
                                <div className="text-2xl font-bold text-green-600">
                                    {parsingValid ? '✓' : '✗'}
                                </div>
                                <div className="text-sm text-green-600">Status</div>
                            </div>
                            <div className="bg-blue-50 p-4 rounded-lg">
                                <div className="text-2xl font-bold text-blue-600">
                                    {totalSteps}
                                </div>
                                <div className="text-sm text-blue-600">Steps</div>
                            </div>
                            <div className="bg-purple-50 p-4 rounded-lg">
                                <div className="text-2xl font-bold text-purple-600">
                                    {inputString.split(' ').length}
                                </div>
                                <div className="text-sm text-purple-600">Tokens</div>
                            </div>
                            <div className="bg-orange-50 p-4 rounded-lg">
                                <div className="text-2xl font-bold text-orange-600">
                                    {currentStep + 1}
                                </div>
                                <div className="text-sm text-orange-600">Current</div>
                            </div>
                        </div>
                    </div>
                </>
            )}

            {/* No Input State */}
            {parsingSteps.length === 0 && inputString && (
                <div className="card p-12 text-center">
                    <Play className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-700 mb-2">Ready to Parse</h3>
                    <p className="text-gray-600 mb-4">
                        Click the "Parse" button to start parsing the input string.
                    </p>
                    <button
                        onClick={handleParse}
                        disabled={isParsing}
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 mx-auto"
                    >
                        {isParsing ? (
                            <LoadingSpinner />
                        ) : (
                            <Play className="w-5 h-5" />
                        )}
                        <span>Parse String</span>
                    </button>
                </div>
            )}
        </div>
    );
};
