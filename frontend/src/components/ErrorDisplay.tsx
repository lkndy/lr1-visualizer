import React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { useParserStore } from '../store/parserStore';

export const ErrorDisplay: React.FC = () => {
  const { grammarErrors, parsingError, showConflicts, setShowConflicts } = useParserStore();

  const hasErrors = grammarErrors.length > 0 || parsingError;

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
              <h3 className="text-sm font-medium text-red-800 mb-2">
                Grammar Validation Errors
              </h3>
              <ul className="space-y-1">
                {grammarErrors.map((error, index) => (
                  <li key={index} className="text-sm text-red-700">
                    <span className="font-medium">{error.type}:</span> {error.message}
                    {error.line_number && (
                      <span className="text-red-600"> (Line {error.line_number})</span>
                    )}
                  </li>
                ))}
              </ul>
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
              <p className="text-sm text-red-700">{parsingError}</p>
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
                <p className="text-sm text-yellow-700">
                  This grammar has shift-reduce or reduce-reduce conflicts. 
                  Parsing may not work correctly.
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowConflicts(false)}
              className="text-yellow-600 hover:text-yellow-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
