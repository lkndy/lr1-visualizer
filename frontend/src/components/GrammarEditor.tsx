import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useParserStore } from '../store/parserStore';
import { LoadingSpinner } from './LoadingSpinner';

export const GrammarEditor: React.FC = () => {
  const {
    grammarText,
    setGrammarText,
    startSymbol,
    setStartSymbol,
    grammarValid,
    grammarErrors,
    isValidatingGrammar,
    generateParsingTable,
    isGeneratingTable,
  } = useParserStore();

  const [showPreview, setShowPreview] = useState(false);

  const handleGrammarChange = (value: string) => {
    setGrammarText(value);
  };

  const handleStartSymbolChange = (value: string) => {
    setStartSymbol(value);
  };

  const handleGenerateTable = () => {
    if (grammarValid) {
      generateParsingTable();
    }
  };

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Grammar Definition</h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="btn-secondary text-sm"
          >
            {showPreview ? 'Hide Preview' : 'Show Preview'}
          </button>
        </div>
      </div>

      {/* Start Symbol Input */}
      <div className="mb-4">
        <label htmlFor="start-symbol" className="block text-sm font-medium text-gray-700 mb-1">
          Start Symbol
        </label>
        <input
          id="start-symbol"
          type="text"
          value={startSymbol}
          onChange={(e) => handleStartSymbolChange(e.target.value)}
          className="input-field max-w-xs"
          placeholder="S"
        />
      </div>

      {/* Grammar Text Editor */}
      <div className="mb-4">
        <label htmlFor="grammar-text" className="block text-sm font-medium text-gray-700 mb-1">
          Grammar Rules
        </label>
        <textarea
          id="grammar-text"
          value={grammarText}
          onChange={(e) => handleGrammarChange(e.target.value)}
          className="textarea-field font-mono text-sm"
          rows={12}
          placeholder={`Enter grammar rules here. Example:

E -> E + T | E - T | T
T -> T * F | T / F | F
F -> ( E ) | id | num

Use -> or → for production rules.
Use | for alternatives.
Use ε or empty for epsilon productions.`}
        />
      </div>

      {/* Validation Status */}
      <div className="mb-4">
        {isValidatingGrammar ? (
          <div className="flex items-center space-x-2 text-blue-600">
            <LoadingSpinner size="sm" />
            <span className="text-sm">Validating grammar...</span>
          </div>
        ) : grammarValid ? (
          <div className="text-green-600 text-sm">
            ✅ Grammar is valid
          </div>
        ) : grammarText.trim() ? (
          <div className="text-red-600 text-sm">
            ❌ Grammar has errors
          </div>
        ) : null}
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-3">
        <button
          onClick={handleGenerateTable}
          disabled={!grammarValid || isGeneratingTable}
          className="btn-primary flex items-center space-x-2"
        >
          {isGeneratingTable ? (
            <>
              <LoadingSpinner size="sm" />
              <span>Generating...</span>
            </>
          ) : (
            <span>Generate Parsing Table</span>
          )}
        </button>
      </div>

      {/* Grammar Preview */}
      {showPreview && grammarText.trim() && (
        <div className="mt-6">
          <h3 className="text-lg font-medium mb-3">Grammar Preview</h3>
          <div className="bg-gray-900 rounded-lg p-4 overflow-auto">
            <SyntaxHighlighter
              language="bnf"
              style={tomorrow}
              customStyle={{
                margin: 0,
                background: 'transparent',
                fontSize: '14px',
              }}
            >
              {grammarText}
            </SyntaxHighlighter>
          </div>
        </div>
      )}

      {/* Grammar Help */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-800 mb-2">Grammar Syntax Help</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Use <code className="bg-blue-100 px-1 rounded">-></code> or <code className="bg-blue-100 px-1 rounded">→</code> for production rules</li>
          <li>• Use <code className="bg-blue-100 px-1 rounded">|</code> to separate alternatives</li>
          <li>• Use <code className="bg-blue-100 px-1 rounded">ε</code> or leave empty for epsilon productions</li>
          <li>• Non-terminals: uppercase letters (e.g., <code className="bg-blue-100 px-1 rounded">E</code>, <code className="bg-blue-100 px-1 rounded">T</code>)</li>
          <li>• Terminals: lowercase letters, operators, keywords (e.g., <code className="bg-blue-100 px-1 rounded">id</code>, <code className="bg-blue-100 px-1 rounded">+</code>)</li>
        </ul>
      </div>
    </div>
  );
};
