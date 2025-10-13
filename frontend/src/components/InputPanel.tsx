import React from 'react';
import { Play, RotateCcw } from 'lucide-react';
import { useParserStore } from '../store/parserStore';
import { LoadingSpinner } from './LoadingSpinner';

export const InputPanel: React.FC = () => {
  const {
    inputString,
    setInputString,
    parseInput,
    isParsing,
    parsingValid,
    parsingError,
    reset,
    grammarValid,
  } = useParserStore();

  const handleParse = () => {
    if (inputString.trim() && grammarValid) {
      parseInput();
    }
  };

  const handleReset = () => {
    reset();
  };

  const handleInputChange = (value: string) => {
    setInputString(value);
  };

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Input String</h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleReset}
            className="btn-secondary flex items-center space-x-1 text-sm"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Input Field */}
      <div className="mb-4">
        <label htmlFor="input-string" className="block text-sm font-medium text-gray-700 mb-1">
          Enter input string to parse
        </label>
        <input
          id="input-string"
          type="text"
          value={inputString}
          onChange={(e) => handleInputChange(e.target.value)}
          className="input-field font-mono"
          placeholder="e.g., id + id * id"
        />
      </div>

      {/* Parse Button */}
      <div className="mb-4">
        <button
          onClick={handleParse}
          disabled={!inputString.trim() || !grammarValid || isParsing}
          className="btn-primary w-full flex items-center justify-center space-x-2"
        >
          {isParsing ? (
            <>
              <LoadingSpinner size="sm" />
              <span>Parsing...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Parse Input</span>
            </>
          )}
        </button>
      </div>

      {/* Parse Status */}
      <div className="mb-4">
        {parsingValid ? (
          <div className="text-green-600 text-sm">
            ✅ Input parsed successfully
          </div>
        ) : parsingError ? (
          <div className="text-red-600 text-sm">
            ❌ Parsing failed: {parsingError}
          </div>
        ) : null}
      </div>

      {/* Help Text */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-800 mb-2">Input Format</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Separate tokens with spaces</li>
          <li>• Use terminal symbols from your grammar</li>
          <li>• Example: <code className="bg-gray-200 px-1 rounded">id + id * ( id - id )</code></li>
        </ul>
      </div>
    </div>
  );
};
