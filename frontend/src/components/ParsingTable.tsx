import React, { useState } from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { useParserStore } from '../store/parserStore';
import { LoadingSpinner } from './LoadingSpinner';

export const ParsingTable: React.FC = () => {
  const {
    actionTable,
    gotoTable,
    tableSummary,
    tableConflicts,
    showConflicts,
    setShowConflicts,
    isGeneratingTable,
    currentStep,
    parsingSteps,
  } = useParserStore();

  const [activeTable, setActiveTable] = useState<'action' | 'goto'>('action');

  const currentStepData = parsingSteps[currentStep];
  const currentState = currentStepData?.stack[currentStepData.stack.length - 1]?.[0];
  const currentToken = currentStepData?.current_token;

  const getCellClassName = (rowIndex: number, colIndex: number, tableType: 'action' | 'goto') => {
    let className = '';
    
    if (tableType === 'action' && activeTable === 'action') {
      // Check if this cell corresponds to current state and token
      if (rowIndex > 0 && colIndex > 0) {
        const state = rowIndex - 1; // Adjust for header row
        const symbol = actionTable?.headers[colIndex];
        
        if (state === currentState && symbol === currentToken) {
          className += ' cell-highlighted ';
        }
        
        // Add action-specific styling
        const cellValue = actionTable?.rows[rowIndex]?.[colIndex];
        if (cellValue) {
          if (cellValue.startsWith('s')) {
            className += ' action-shift ';
          } else if (cellValue.startsWith('r')) {
            className += ' action-reduce ';
          } else if (cellValue === 'acc') {
            className += ' action-accept ';
          } else if (cellValue === '') {
            className += ' action-error ';
          }
        }
      }
    }
    
    return className;
  };

  const renderTable = (table: typeof actionTable | typeof gotoTable, type: 'action' | 'goto') => {
    if (!table) return null;

    return (
      <div className="overflow-x-auto">
        <table className="parsing-table">
          <thead>
            <tr>
              {table.headers.map((header, index) => (
                <th key={index} className={index === 0 ? 'state-header' : ''}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, colIndex) => (
                  <td
                    key={colIndex}
                    className={getCellClassName(rowIndex, colIndex, type)}
                  >
                    {cell || '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  if (isGeneratingTable) {
    return (
      <div className="card p-6 text-center">
        <LoadingSpinner />
        <p className="mt-4 text-gray-600">Generating parsing table...</p>
      </div>
    );
  }

  if (!actionTable || !gotoTable) {
    return (
      <div className="card p-6 text-center">
        <Info className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Parsing Table</h3>
        <p className="text-gray-600">
          Define and validate a grammar to generate the parsing table.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Table Summary */}
      {tableSummary && (
        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-4">Parsing Table Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {tableSummary.num_states}
              </div>
              <div className="text-sm text-blue-600">States</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {tableSummary.num_terminals}
              </div>
              <div className="text-sm text-green-600">Terminals</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {tableSummary.num_non_terminals}
              </div>
              <div className="text-sm text-purple-600">Non-terminals</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {tableSummary.conflicts.total_conflicts}
              </div>
              <div className="text-sm text-orange-600">Conflicts</div>
            </div>
          </div>
        </div>
      )}

      {/* Conflicts Warning */}
      {tableConflicts.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-yellow-800">
                  {tableConflicts.length} Conflict{tableConflicts.length !== 1 ? 's' : ''} Detected
                </h3>
                <button
                  onClick={() => setShowConflicts(!showConflicts)}
                  className="text-sm text-yellow-700 hover:text-yellow-900"
                >
                  {showConflicts ? 'Hide' : 'Show'} Details
                </button>
              </div>
              
              {showConflicts && (
                <div className="mt-3 space-y-2">
                  {tableConflicts.map((conflict, index) => (
                    <div key={index} className="text-sm text-yellow-700">
                      <strong>State {conflict.state}, Symbol '{conflict.symbol}':</strong> {conflict.conflict_type}
                      <div className="ml-4">
                        {conflict.actions.map((action, actionIndex) => (
                          <div key={actionIndex}>
                            - {action.action_type} {action.target}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Table Tabs */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Parsing Tables</h2>
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActiveTable('action')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                activeTable === 'action'
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              ACTION Table
            </button>
            <button
              onClick={() => setActiveTable('goto')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                activeTable === 'goto'
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              GOTO Table
            </button>
          </div>
        </div>

        {/* Current Step Info */}
        {currentStepData && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-sm text-blue-800">
              <strong>Current Step:</strong> State {currentState}, Token '{currentToken}'
            </div>
            <div className="text-sm text-blue-700 mt-1">
              {currentStepData.explanation}
            </div>
          </div>
        )}

        {/* Table Content */}
        {activeTable === 'action' && renderTable(actionTable, 'action')}
        {activeTable === 'goto' && renderTable(gotoTable, 'goto')}

        {/* Table Legend */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-100 border border-blue-300 rounded"></div>
            <span className="text-sm text-gray-600">Shift (s)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-100 border border-green-300 rounded"></div>
            <span className="text-sm text-gray-600">Reduce (r)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-100 border border-yellow-300 rounded"></div>
            <span className="text-sm text-gray-600">Accept (acc)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-primary-100 border border-primary-300 rounded"></div>
            <span className="text-sm text-gray-600">Current Cell</span>
          </div>
        </div>
      </div>
    </div>
  );
};
