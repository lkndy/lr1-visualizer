import React, { useState } from 'react';
import { AlertTriangle, X, ChevronDown, ChevronRight, Info, Bug } from 'lucide-react';
import { useParserStore } from '../store/parserStore';

export const ErrorDisplay: React.FC = () => {
  const { grammarErrors, parsingError, showConflicts, setShowConflicts } = useParserStore();
  const [expandedErrors, setExpandedErrors] = useState<Set<number>>(new Set());
  const [showErrorDetails, setShowErrorDetails] = useState(false);

  const hasErrors = grammarErrors.length > 0 || parsingError;

  const toggleErrorExpansion = (index: number) => {
    const newExpanded = new Set(expandedErrors);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedErrors(newExpanded);
  };

  if (!hasErrors) {
    return null;
  }

  return (
    <div className="mb-6 space-y-4">
      {/* Grammar Errors */}
      {grammarErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-red-800">
                  Grammar Validation Errors ({grammarErrors.length})
                </h3>
                <button
                  onClick={() => setShowErrorDetails(!showErrorDetails)}
                  className="text-xs text-red-600 hover:text-red-800 flex items-center space-x-1"
                >
                  <span>{showErrorDetails ? 'Hide' : 'Show'} Details</span>
                  {showErrorDetails ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                </button>
              </div>

              <div className="space-y-2">
                {grammarErrors.map((error, index) => (
                  <div key={index} className="bg-red-100 border border-red-200 rounded p-3">
                    <div className="flex items-start space-x-2">
                      <Bug className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="text-sm text-red-800">
                          <span className="font-medium">{error.type}:</span> {error.message}
                        </div>
                        {error.line_number && (
                          <div className="text-xs text-red-600 mt-1">
                            Line {error.line_number}
                          </div>
                        )}
                        {showErrorDetails && (
                          <div className="mt-2 text-xs text-red-700 bg-red-200 p-2 rounded">
                            <strong>Error Details:</strong> This error occurred during grammar validation.
                            Please check the grammar syntax and ensure all productions are properly defined.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Parsing Errors */}
      {parsingError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800 mb-2">
                Parsing Error
              </h3>
              <div className="bg-red-100 border border-red-200 rounded p-3">
                <p className="text-sm text-red-700 mb-2">{parsingError}</p>
                <div className="text-xs text-red-600 bg-red-200 p-2 rounded">
                  <strong>Tip:</strong> Check that the input string is valid according to the grammar rules.
                  Make sure all tokens are properly defined and the grammar is unambiguous.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Conflicts Warning */}
      {showConflicts && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-yellow-800 mb-2">
                  Grammar Conflicts Detected
                </h3>
                <div className="bg-yellow-100 border border-yellow-200 rounded p-3">
                  <p className="text-sm text-yellow-700 mb-2">
                    This grammar has shift-reduce or reduce-reduce conflicts.
                    Parsing may not work correctly.
                  </p>
                  <div className="text-xs text-yellow-600 bg-yellow-200 p-2 rounded">
                    <strong>Resolution:</strong> Consider using precedence rules or restructuring the grammar
                    to resolve conflicts. LR(1) grammars should be unambiguous.
                  </div>
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowConflicts(false)}
              className="text-yellow-600 hover:text-yellow-800 p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
