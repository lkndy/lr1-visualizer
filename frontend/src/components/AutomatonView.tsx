import React, { useEffect, useCallback, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useParserStore } from '../store/parserStore';
import { dataValidator } from '../utils/dataValidator';
import { logger } from '../utils/logger';

interface AutomatonNodeData {
  state: number;
  items: string[];
  isCurrent: boolean;
  isHighlighted: boolean;
}

interface AutomatonEdgeData {
  symbol: string;
  isActive: boolean;
  isHighlighted: boolean;
}

export const AutomatonView: React.FC = () => {
  const {
    currentStep,
    parsingSteps,
    grammarInfo,
    isGeneratingTable,
    getCurrentState,
    getCurrentStepData
  } = useParserStore();

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [tooltip, setTooltip] = useState<{ visible: boolean; x: number; y: number; data: AutomatonNodeData | null }>({
    visible: false,
    x: 0,
    y: 0,
    data: null
  });

  // Get current state data for rendering
  const currentStepData = getCurrentStepData();
  const currentState = getCurrentState();

  useEffect(() => {
    logger.componentMount('AutomatonView', {
      isGeneratingTable,
      hasGrammarInfo: !!grammarInfo,
      hasLR1States: !!grammarInfo?.lr1_states
    });

    if (isGeneratingTable || !grammarInfo?.lr1_states) {
      logger.debug('COMPONENT', 'AutomatonView: No data available, clearing nodes and edges', {
        isGeneratingTable,
        hasGrammarInfo: !!grammarInfo,
        hasLR1States: !!grammarInfo?.lr1_states
      });
      setNodes([]);
      setEdges([]);
      return;
    }

    // Validate LR1 states data
    const statesValidation = dataValidator.validateLR1States(grammarInfo.lr1_states, 'AutomatonView.lr1_states');
    if (!statesValidation.isValid) {
      logger.componentError('AutomatonView', 'Invalid LR1 states data', {
        errors: statesValidation.errors,
        states: grammarInfo.lr1_states
      });
      setNodes([]);
      setEdges([]);
      return;
    }

    // Get current state from parsing stack with null checks

    // Validate currentStepData before using it
    if (currentStepData && !dataValidator.isInteractiveDerivationStep(currentStepData)) {
      logger.warn('COMPONENT', 'AutomatonView: Invalid currentStepData structure', {
        currentStepData,
        currentState
      });
    }

    // Create nodes from LR(1) states data with validation
    const automatonNodes: Node<AutomatonNodeData>[] = grammarInfo.lr1_states.map((state, index) => {
      // Validate state structure
      if (!state || typeof state.state_number !== 'number') {
        logger.warn('COMPONENT', `AutomatonView: Invalid state at index ${index}`, { state, index });
        return null;
      }

      // Calculate position using a more compact grid layout
      const cols = Math.ceil(Math.sqrt(grammarInfo.lr1_states.length));
      const row = Math.floor(index / cols);
      const col = index % cols;
      const x = col * 180 + 30; // More compact spacing
      const y = row * 140 + 30; // More compact spacing

      return {
        id: state.state_number.toString(),
        type: 'default',
        position: { x, y },
        data: {
          state: state.state_number,
          items: Array.isArray(state.items) ? state.items : [],
          isCurrent: currentState === state.state_number,
          isHighlighted: false,
        },
      };
    }).filter(Boolean) as Node<AutomatonNodeData>[];

    // Create edges from transitions data - IMPROVED APPROACH
    const automatonEdges: Edge<AutomatonEdgeData>[] = [];

    logger.debug('COMPONENT', 'Creating edges from transitions', {
      statesCount: grammarInfo.lr1_states.length
    });

    // First, let's log the actual data structure to understand what we have
    grammarInfo.lr1_states.forEach((state, stateIndex) => {
      logger.debug('COMPONENT', `State ${stateIndex} data structure`, {
        stateNumber: state.state_number,
        hasTransitions: !!state.transitions,
        transitionsLength: state.transitions?.length || 0,
        transitions: state.transitions,
        shiftSymbols: state.shift_symbols,
        items: state.items?.length || 0
      });
    });

    grammarInfo.lr1_states.forEach((state, stateIndex) => {
      if (!state || typeof state.state_number !== 'number') {
        logger.warn('COMPONENT', `Skipping invalid state for edge creation`, { state });
        return;
      }

      // Use the transitions array if available
      if (state.transitions && Array.isArray(state.transitions) && state.transitions.length > 0) {
        logger.debug('COMPONENT', `Creating edges from transitions for state ${state.state_number}`, {
          transitionsCount: state.transitions.length
        });

        state.transitions.forEach((transition, index) => {
          if (!transition || typeof transition.to_state !== 'number' || !transition.symbol) {
            logger.warn('COMPONENT', `Invalid transition at index ${index}`, { transition, state: state.state_number });
            return;
          }

          // Check if this edge is part of the current parsing path
          const isActive = Boolean(currentStepData &&
            state.state_number === currentState &&
            currentStepData.action?.type === 'shift' &&
            currentStepData.current_token === transition.symbol);

          const edgeId = `e${state.state_number}-${transition.to_state}-${transition.symbol}`;

          logger.debug('COMPONENT', `Creating edge: ${edgeId}`, {
            source: state.state_number.toString(),
            target: transition.to_state.toString(),
            symbol: transition.symbol,
            isActive
          });

          automatonEdges.push({
            id: edgeId,
            source: state.state_number.toString(),
            target: transition.to_state.toString(),
            label: transition.symbol,
            type: 'smoothstep', // Use smoothstep for better visual flow
            animated: isActive,
            style: {
              stroke: isActive ? '#f59e0b' : '#3b82f6',
              strokeWidth: isActive ? 3 : 2,
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: isActive ? '#f59e0b' : '#3b82f6',
            },
            data: {
              symbol: transition.symbol,
              isActive,
              isHighlighted: false,
            },
          });
        });
      } else {
        // If no transitions, create edges based on shift symbols and next states
        logger.debug('COMPONENT', `No transitions for state ${state.state_number}, creating basic connections`, {
          shiftSymbols: state.shift_symbols
        });

        if (Array.isArray(state.shift_symbols) && state.shift_symbols.length > 0) {
          state.shift_symbols.forEach((symbol) => {
            if (typeof symbol === 'string') {
              // Create connections to the next few states (simple approach)
              const nextStates = [stateIndex + 1, stateIndex + 2].filter(nextIndex =>
                nextIndex < grammarInfo.lr1_states.length
              );

              nextStates.forEach((nextIndex, symbolIndex) => {
                const targetState = grammarInfo.lr1_states[nextIndex].state_number;
                const edgeId = `e${state.state_number}-${targetState}-${symbol}-${symbolIndex}`;

                logger.debug('COMPONENT', `Creating fallback edge: ${edgeId}`, {
                  source: state.state_number.toString(),
                  target: targetState.toString(),
                  symbol
                });

                automatonEdges.push({
                  id: edgeId,
                  source: state.state_number.toString(),
                  target: targetState.toString(),
                  label: symbol,
                  type: 'smoothstep',
                  style: {
                    stroke: '#3b82f6',
                    strokeWidth: 2,
                  },
                  markerEnd: {
                    type: MarkerType.ArrowClosed,
                    color: '#3b82f6',
                  },
                  data: {
                    symbol,
                    isActive: false,
                    isHighlighted: false,
                  },
                });
              });
            }
          });
        }
      }
    });

    // Comprehensive debugging for edge creation
    logger.debug('COMPONENT', 'Created edges', {
      edgesCount: automatonEdges.length,
      nodesCount: automatonNodes.length,
      edges: automatonEdges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        type: e.type
      })),
      nodeIds: automatonNodes.map(n => n.id)
    });

    // Verify that all edge sources and targets exist in nodes
    const nodeIds = new Set(automatonNodes.map(n => n.id));
    const invalidEdges = automatonEdges.filter(e =>
      !nodeIds.has(e.source) || !nodeIds.has(e.target)
    );

    if (invalidEdges.length > 0) {
      logger.warn('COMPONENT', 'Found edges with invalid source/target IDs', {
        invalidEdges: invalidEdges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceExists: nodeIds.has(e.source),
          targetExists: nodeIds.has(e.target)
        })),
        availableNodeIds: Array.from(nodeIds)
      });
    }

    // Additional debugging for edge creation
    if (automatonEdges.length === 0) {
      logger.warn('COMPONENT', 'No edges created! This might be why transitions are not visible', {
        statesWithTransitions: grammarInfo.lr1_states.filter(s => s.transitions && s.transitions.length > 0).length,
        totalStates: grammarInfo.lr1_states.length
      });

      // Create a test edge to verify ReactFlow is working
      if (automatonNodes.length >= 2) {
        logger.debug('COMPONENT', 'Creating test edge to verify ReactFlow functionality', {
          sourceNode: automatonNodes[0].id,
          targetNode: automatonNodes[1].id
        });
        automatonEdges.push({
          id: 'test-edge',
          source: automatonNodes[0].id,
          target: automatonNodes[1].id,
          label: 'TEST',
          type: 'smoothstep',
          style: {
            stroke: '#ff0000',
            strokeWidth: 3,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#ff0000',
          },
          data: {
            symbol: 'TEST',
            isActive: false,
            isHighlighted: false,
          },
        });
      }
    }

    setNodes(automatonNodes);
    setEdges(automatonEdges);
  }, [currentStep, isGeneratingTable, grammarInfo, getCurrentState, getCurrentStepData]);

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge(params, eds));
  }, [setEdges]);

  // Debug edge changes
  useEffect(() => {
    logger.debug('COMPONENT', 'Edges updated', {
      edgesCount: edges.length,
      edges: edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        type: e.type,
        animated: e.animated
      }))
    });
  }, [edges]);

  const handleNodeMouseEnter = useCallback((event: React.MouseEvent, data: AutomatonNodeData) => {
    setTooltip({
      visible: true,
      x: event.clientX,
      y: event.clientY,
      data
    });
  }, []);

  const handleNodeMouseLeave = useCallback(() => {
    setTooltip(prev => ({ ...prev, visible: false }));
  }, []);

  const handleNodeMouseMove = useCallback((event: React.MouseEvent) => {
    setTooltip(prev => ({
      ...prev,
      x: event.clientX,
      y: event.clientY
    }));
  }, []);

  const nodeTypes = {
    default: ({ data }: { data: AutomatonNodeData }) => (
      <div
        className={`px-2 py-1 bg-white border-2 rounded shadow-sm min-w-[100px] max-w-[140px] transition-all duration-300 cursor-pointer ${data.isCurrent
          ? 'border-blue-500 bg-blue-50 shadow-lg transform scale-105'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-md hover:transform hover:scale-102'
          }`}
        onMouseEnter={(e) => handleNodeMouseEnter(e, data)}
        onMouseLeave={handleNodeMouseLeave}
        onMouseMove={handleNodeMouseMove}
      >
        <div className="text-center mb-1">
          <div className={`text-sm font-bold ${data.isCurrent ? 'text-blue-900' : 'text-gray-900'}`}>
            {data.state}
          </div>
        </div>

        <div className="space-y-0.5 max-h-32 overflow-y-auto">
          {data.items.slice(0, 2).map((item, index) => (
            <div
              key={index}
              className={`text-xs font-mono px-1 py-0.5 rounded text-gray-700 break-words transition-colors duration-200 ${data.isCurrent ? 'bg-blue-100' : 'bg-gray-100 hover:bg-gray-200'
                }`}
              title={item}
            >
              <div className="line-clamp-2 text-xs leading-tight">
                {item.length > 30 ? item.substring(0, 30) + '...' : item}
              </div>
            </div>
          ))}
          {data.items.length > 2 && (
            <div className="text-xs text-gray-500 text-center">
              +{data.items.length - 2} more
            </div>
          )}
        </div>

        {data.isCurrent && (
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-ping"></div>
        )}
      </div>
    ),
  };

  const edgeOptions = {
    style: {
      strokeWidth: 2,
      stroke: '#3b82f6',
    },
    labelStyle: {
      fontSize: 12,
      fontWeight: 'bold',
      fill: '#1f2937',
    },
    labelBgStyle: {
      fill: '#ffffff',
      fillOpacity: 0.8,
    },
  };


  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">LR(1) Automaton</h2>
        <div className="text-sm text-gray-600">
          {nodes.length} state{nodes.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Current State Info */}
      {parsingSteps.length > 0 && currentStep < parsingSteps.length && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm text-blue-800">
              <strong>Current State:</strong> {
                nodes.find(n => n.data?.isCurrent)?.data?.state || 'Unknown'
              }
            </div>
            <div className="text-xs text-blue-600">
              Step {currentStep + 1} of {parsingSteps.length}
            </div>
          </div>
          <div className="text-sm text-blue-700 mb-2">
            {parsingSteps[currentStep]?.explanation || 'No explanation available'}
          </div>
          {currentStepData?.current_token && (
            <div className="text-sm text-blue-700">
              <strong>Current Token:</strong> {currentStepData.current_token}
            </div>
          )}
        </div>
      )}

      {/* ReactFlow Component */}
      <div style={{ height: '500px' }} className="border border-gray-200 rounded-lg">
        {nodes.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-lg mb-2">🔄</div>
              <div className="text-sm">No automaton data</div>
              <div className="text-xs text-gray-400 mt-1">
                Generate parsing table to see the automaton
              </div>
            </div>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            defaultEdgeOptions={edgeOptions}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.1}
            maxZoom={2}
            attributionPosition="bottom-left"
          >
            <Controls />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        )}
      </div>

      {/* Tooltip */}
      {tooltip.visible && tooltip.data && (
        <div
          className="fixed z-50 bg-gray-900 text-white p-4 rounded-lg shadow-lg max-w-md pointer-events-none"
          style={{
            left: tooltip.x + 10,
            top: tooltip.y - 10,
            transform: 'translateY(-100%)'
          }}
        >
          <div className="font-bold mb-2 text-blue-300">State {tooltip.data.state}</div>
          <div className="space-y-2">
            <div className="text-xs text-gray-300">
              Items ({tooltip.data.items.length}):
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {tooltip.data.items.map((item, index) => (
                <div key={index} className="text-xs font-mono bg-gray-800 px-2 py-1 rounded break-words">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-primary-100 border-2 border-primary-300 rounded"></div>
          <span className="text-sm text-gray-600">Current state</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-gray-100 border-2 border-gray-300 rounded"></div>
          <span className="text-sm text-gray-600">Other states</span>
        </div>
      </div>

      {/* State Details Panel */}
      {currentStepData && (
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-800 mb-2">Current State Details</h4>
          <div className="space-y-2">
            <div className="text-xs text-gray-600">
              <strong>Stack:</strong> {
                Array.isArray(currentStepData?.stack)
                  ? currentStepData.stack.map(([state, symbol]) => `${state}${symbol ? `,${symbol}` : ''}`).join(' | ')
                  : 'Invalid stack data'
              }
            </div>
            <div className="text-xs text-gray-600">
              <strong>Input Remaining:</strong> {
                Array.isArray(currentStepData?.input_remaining)
                  ? currentStepData.input_remaining.join(' ')
                  : 'None'
              }
            </div>
            {currentStepData?.action && (
              <div className="text-xs text-gray-600">
                <strong>Action:</strong> {currentStepData.action.type} {currentStepData.action.target ? `(${currentStepData.action.target})` : ''}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-4 text-xs text-gray-500">
        💡 Drag nodes to rearrange, use mouse wheel to zoom
      </div>
    </div>
  );
};

