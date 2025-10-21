import React, { useEffect, useCallback } from 'react';
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
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useParserStore } from '../store/parserStore';

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

  useEffect(() => {
    if (isGeneratingTable || !grammarInfo?.lr1_states) {
      setNodes([]);
      setEdges([]);
      return;
    }

    // Get current state from parsing stack
    const currentState = getCurrentState();
    const currentStepData = getCurrentStepData();

    // Create nodes from LR(1) states data
    const automatonNodes: Node<AutomatonNodeData>[] = grammarInfo.lr1_states.map((state, index) => {
      // Calculate position using a simple grid layout
      const cols = Math.ceil(Math.sqrt(grammarInfo.lr1_states.length));
      const row = Math.floor(index / cols);
      const col = index % cols;
      const x = col * 250 + 50; // Smaller spacing
      const y = row * 180 + 50; // Smaller spacing

      return {
        id: state.state_number.toString(),
        type: 'default',
        position: { x, y },
        data: {
          state: state.state_number,
          items: state.items,
          isCurrent: currentState === state.state_number, // FIXED: Use currentState from stack
          isHighlighted: false,
        },
      };
    });

    // Create edges from transitions data
    const automatonEdges: Edge<AutomatonEdgeData>[] = [];

    console.log('Creating edges from transitions:', grammarInfo.lr1_states);

    grammarInfo.lr1_states.forEach((state) => {
      console.log(`State ${state.state_number} has ${state.transitions?.length || 0} transitions:`, state.transitions);

      // Check if transitions exist, otherwise create basic edges from shift symbols
      if (state.transitions && state.transitions.length > 0) {
        state.transitions.forEach((transition) => {
          // Check if this edge is part of the current parsing path
          const isActive = Boolean(currentStepData &&
            state.state_number === currentState &&
            currentStepData.action?.type === 'shift' &&
            currentStepData.current_token === transition.symbol);

          automatonEdges.push({
            id: `e${state.state_number}-${transition.to_state}-${transition.symbol}`,
            source: state.state_number.toString(),
            target: transition.to_state.toString(),
            label: transition.symbol,
            data: {
              symbol: transition.symbol,
              isActive,
              isHighlighted: false,
            },
          });
        });
      } else {
        // Fallback: create basic transitions based on shift symbols
        console.log(`No transitions for state ${state.state_number}, using shift symbols:`, state.shift_symbols);
        state.shift_symbols.forEach((symbol) => {
          const targetState = (state.state_number + 1) % grammarInfo.lr1_states.length;
          if (targetState !== state.state_number) {
            automatonEdges.push({
              id: `e${state.state_number}-${targetState}-${symbol}`,
              source: state.state_number.toString(),
              target: targetState.toString(),
              label: symbol,
              data: {
                symbol,
                isActive: false,
                isHighlighted: false,
              },
            });
          }
        });
      }
    });

    console.log('Created edges:', automatonEdges);

    setNodes(automatonNodes);
    setEdges(automatonEdges);
  }, [currentStep, isGeneratingTable, grammarInfo, getCurrentState, getCurrentStepData]);

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge(params, eds));
  }, [setEdges]);

  const nodeTypes = {
    default: ({ data }: { data: AutomatonNodeData }) => (
      <div className={`px-2 py-1 bg-white border-2 rounded shadow-sm min-w-[120px] max-w-[150px] transition-all duration-300 ${data.isCurrent
        ? 'border-blue-500 bg-blue-50 shadow-lg transform scale-105'
        : 'border-gray-200 hover:border-gray-300 hover:shadow-md hover:transform hover:scale-102'
        }`}>
        <div className="text-center mb-1">
          <div className={`text-sm font-bold ${data.isCurrent ? 'text-blue-900' : 'text-gray-900'}`}>
            {data.state}
          </div>
        </div>

        <div className="space-y-0.5">
          {data.items.slice(0, 3).map((item, index) => (
            <div
              key={index}
              className={`text-xs font-mono px-1 py-0.5 rounded text-gray-700 truncate transition-colors duration-200 ${data.isCurrent ? 'bg-blue-100' : 'bg-gray-100 hover:bg-gray-200'
                }`}
              title={item}
            >
              {item.length > 20 ? item.substring(0, 20) + '...' : item}
            </div>
          ))}
          {data.items.length > 3 && (
            <div className="text-xs text-gray-500 text-center">
              +{data.items.length - 3} more
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

  const getEdgeStyle = (edge: any) => {
    const isActive = edge.data?.isActive;
    return {
      strokeWidth: isActive ? 4 : 2,
      stroke: isActive ? '#f59e0b' : '#3b82f6',
      strokeDasharray: isActive ? '5,5' : 'none',
      opacity: isActive ? 1 : 0.7,
    };
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
                nodes.find(n => n.data.isCurrent)?.data.state || 'Unknown'
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
            attributionPosition="bottom-left"
          >
            <Controls />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        )}
      </div>

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
              <strong>Stack:</strong> {currentStepData.stack.map(([state, symbol]) => `${state}${symbol ? `,${symbol}` : ''}`).join(' | ')}
            </div>
            <div className="text-xs text-gray-600">
              <strong>Input Remaining:</strong> {currentStepData.input_remaining?.join(' ') || 'None'}
            </div>
            {currentStepData.action && (
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

