import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { useParserStore } from '../store/parserStore';
import { LoadingSpinner, SkeletonTable } from './LoadingSpinner';
import { dataValidator } from '../utils/dataValidator';
import { logger } from '../utils/logger';

export const ParsingTable: React.FC = () => {
  const {
    actionTable,
    gotoTable,
    tableSummary,
    tableConflicts,
    showConflicts,
    setShowConflicts,
    isGeneratingTable,
    getCurrentStepData,
    getCurrentState,
    getCurrentAction,
  } = useParserStore();

  const [activeTable, setActiveTable] = useState<'action' | 'goto'>('action');
  const [hoveredCell, setHoveredCell] = useState<{ row: number, col: number, table: 'action' | 'goto' } | null>(null);
  const [tableValidationErrors, setTableValidationErrors] = useState<string[]>([]);

  // Use computed selectors for current state and action
  const currentStepData = getCurrentStepData();
  const currentState = getCurrentState();
  const currentAction = getCurrentAction();
  const currentToken = currentStepData?.current_token;

  // Validate table data on mount and when tables change
  useEffect(() => {
    logger.componentMount('ParsingTable', {
      hasActionTable: !!actionTable,
      hasGotoTable: !!gotoTable,
      activeTable
    });

    const errors: string[] = [];

    if (actionTable) {
      const actionValidation = dataValidator.validateTableStructure(actionTable, 'ParsingTable.actionTable');
      if (!actionValidation.isValid) {
        errors.push(...actionValidation.errors.map(e => `Action Table: ${e.message}`));
        logger.validationError('ParsingTable', 'Action table validation failed', actionValidation.errors);
      }
    }

    if (gotoTable) {
      const gotoValidation = dataValidator.validateTableStructure(gotoTable, 'ParsingTable.gotoTable');
      if (!gotoValidation.isValid) {
        errors.push(...gotoValidation.errors.map(e => `Goto Table: ${e.message}`));
        logger.validationError('ParsingTable', 'Goto table validation failed', gotoValidation.errors);
      }
    }

    setTableValidationErrors(errors);

    if (errors.length > 0) {
      logger.warn('COMPONENT', 'ParsingTable has validation issues', { errors });
    }
  }, [actionTable, gotoTable, activeTable]);

  const getCellClassName = useCallback((rowIndex: number, colIndex: number, tableType: 'action' | 'goto') => {
    let className = 'px-2 sm:px-3 py-2 text-xs sm:text-sm border border-gray-200 transition-all duration-200 ';

    // Validate inputs
    if (typeof rowIndex !== 'number' || typeof colIndex !== 'number' || rowIndex < 0 || colIndex < 0) {
      logger.warn('COMPONENT', 'Invalid cell coordinates', { rowIndex, colIndex, tableType });
      return className + 'bg-red-100 text-red-800 ';
    }

    if (tableType === 'action' && activeTable === 'action' && actionTable) {
      // Check if this cell corresponds to current state and token
      if (rowIndex > 0 && colIndex > 0) {
        const state = rowIndex - 1; // Adjust for header row
        const symbol = actionTable.headers?.[colIndex];

        // Validate table structure
        if (!Array.isArray(actionTable.headers) || !Array.isArray(actionTable.rows)) {
          logger.warn('COMPONENT', 'Invalid action table structure', {
            headers: actionTable.headers,
            rows: actionTable.rows
          });
          return className + 'bg-red-100 text-red-800 ';
        }

        // Highlight current action cell with enhanced styling
        if (state === currentState && symbol === currentToken) {
          className += 'bg-yellow-200 border-2 border-yellow-500 font-bold text-yellow-900 animate-pulse-glow shadow-lg ';
        }

        // Add action-specific styling with enhanced colors
        const cellValue = actionTable.rows[rowIndex]?.[colIndex];
        if (cellValue && typeof cellValue === 'string') {
          if (cellValue.startsWith('s')) {
            className += 'bg-blue-100 text-blue-800 hover:bg-blue-200 ';
          } else if (cellValue.startsWith('r')) {
            className += 'bg-green-100 text-green-800 hover:bg-green-200 ';
          } else if (cellValue === 'acc') {
            className += 'bg-purple-100 text-purple-800 hover:bg-purple-200 ';
          } else if (cellValue === '' || cellValue === '-') {
            className += 'bg-red-100 text-red-800 hover:bg-red-200 ';
          } else {
            className += 'bg-gray-100 text-gray-800 hover:bg-gray-200 ';
          }
        } else {
          className += 'bg-gray-50 text-gray-400 hover:bg-gray-100 ';
        }
      }
    } else if (tableType === 'goto' && activeTable === 'goto' && gotoTable) {
      // Similar logic for goto table
      if (rowIndex > 0 && colIndex > 0) {
        const state = rowIndex - 1;
        const symbol = gotoTable.headers?.[colIndex];

        // Validate table structure
        if (!Array.isArray(gotoTable.headers) || !Array.isArray(gotoTable.rows)) {
          logger.warn('COMPONENT', 'Invalid goto table structure', {
            headers: gotoTable.headers,
            rows: gotoTable.rows
          });
          return className + 'bg-red-100 text-red-800 ';
        }

        if (state === currentState && symbol === currentToken) {
          className += 'bg-yellow-200 border-2 border-yellow-500 font-bold text-yellow-900 animate-pulse-glow shadow-lg ';
        }

        const cellValue = gotoTable.rows[rowIndex]?.[colIndex];
        if (cellValue && typeof cellValue === 'string' && cellValue !== '' && cellValue !== '-') {
          className += 'bg-indigo-100 text-indigo-800 hover:bg-indigo-200 ';
        } else {
          className += 'bg-gray-50 text-gray-400 hover:bg-gray-100 ';
        }
      }
    }

    return className;
  }, [activeTable, currentState, currentToken, actionTable, gotoTable]);

  const renderTable = useCallback((table: typeof actionTable | typeof gotoTable, type: 'action' | 'goto') => {
    if (!table) {
      logger.warn('COMPONENT', `No ${type} table data available`);
      return (
        <div className="text-center text-gray-500 py-8">
          <Info className="w-8 h-8 mx-auto mb-2" />
          <p>No {type} table data available</p>
        </div>
      );
    }

    // Validate table structure
    if (!Array.isArray(table.headers) || !Array.isArray(table.rows)) {
      logger.error('COMPONENT', `Invalid ${type} table structure`, {
        headers: table.headers,
        rows: table.rows
      });
      return (
        <div className="text-center text-red-500 py-8">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <p>Invalid {type} table structure</p>
        </div>
      );
    }

    if (table.headers.length === 0 || table.rows.length === 0) {
      logger.warn('COMPONENT', `Empty ${type} table`, {
        headersCount: table.headers.length,
        rowsCount: table.rows.length
      });
      return (
        <div className="text-center text-yellow-500 py-8">
          <Info className="w-8 h-8 mx-auto mb-2" />
          <p>Empty {type} table</p>
        </div>
      );
    }

    return (
      <div className="overflow-x-auto">
        <table className="parsing-table" role="table" aria-label={`${type} parsing table`}>
          <thead>
            <tr>
              {table.headers.map((header, index) => (
                <th key={index} className={index === 0 ? 'state-header' : ''} scope="col">
                  {header || `Column ${index}`}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, rowIndex) => {
              if (!Array.isArray(row)) {
                logger.warn('COMPONENT', `Invalid row at index ${rowIndex}`, { row, rowIndex });
                return null;
              }

              return (
                <tr key={rowIndex}>
                  {row.map((cell, colIndex) => {
                    const cellValue = cell !== null && cell !== undefined ? String(cell) : '-';
                    const header = table.headers[colIndex] || `Col ${colIndex}`;

                    return (
                      <td
                        key={colIndex}
                        className={getCellClassName(rowIndex, colIndex, type)}
                        title={
                          rowIndex > 0 && colIndex > 0 &&
                            (rowIndex - 1) === currentState &&
                            header === currentToken
                            ? currentAction?.description || 'Current action'
                            : undefined
                        }
                        onMouseEnter={() => setHoveredCell({ row: rowIndex, col: colIndex, table: type })}
                        onMouseLeave={() => setHoveredCell(null)}
                        role="gridcell"
                        aria-label={`State ${rowIndex - 1}, Symbol ${header}, Value: ${cellValue}`}
                      >
                        {cellValue}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  }, [getCellClassName, currentAction, currentState, currentToken]);

  if (isGeneratingTable) {
    return (
      <div className="space-y-6">
        <div className="card p-6 text-center">
          <LoadingSpinner size="lg" text="Generating parsing table..." />
        </div>
        <SkeletonTable rows={8} cols={6} />
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
      {/* Validation Errors */}
      {tableValidationErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800 mb-2">
                Table Validation Issues
              </h3>
              <div className="space-y-1">
                {tableValidationErrors.map((error, index) => (
                  <div key={index} className="text-sm text-red-700">
                    • {error}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

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
                {tableSummary.conflicts?.total_conflicts || 0}
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

      {/* Current Action Status */}
      {currentAction && currentState !== null && currentToken && (
        <div className="card p-4 bg-yellow-50 border border-yellow-200">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-yellow-600" />
            <span className="text-sm text-yellow-800">
              <strong>Current Action:</strong> {currentAction?.description || 'No action description'}
            </span>
          </div>
          <div className="text-xs text-yellow-700 mt-1">
            State {currentState} × Token '{currentToken}'
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
              className={`px-3 py-1 text-sm rounded-md transition-colors ${activeTable === 'action'
                ? 'bg-white text-primary-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
                }`}
            >
              ACTION Table
            </button>
            <button
              onClick={() => setActiveTable('goto')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${activeTable === 'goto'
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
              {currentStepData.explanation || 'No explanation available'}
            </div>
          </div>
        )}

        {/* Hover Information */}
        {hoveredCell && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-sm text-blue-800">
              <strong>Cell Information:</strong>
            </div>
            <div className="text-sm text-blue-700 mt-1">
              State: {hoveredCell.row - 1}, Symbol: '{hoveredCell.table === 'action' ? actionTable?.headers[hoveredCell.col] : gotoTable?.headers[hoveredCell.col]}'
            </div>
            <div className="text-sm text-blue-700">
              Value: {hoveredCell.table === 'action' ? actionTable?.rows[hoveredCell.row]?.[hoveredCell.col] : gotoTable?.rows[hoveredCell.row]?.[hoveredCell.col] || 'Empty'}
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
