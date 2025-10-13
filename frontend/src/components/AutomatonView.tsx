import React, { useEffect, useState, useCallback } from 'react';
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

interface AutomatonNode extends Node {
  data: {
    state: number;
    items: string[];
    isCurrent: boolean;
    isHighlighted: boolean;
  };
}

interface AutomatonEdge extends Edge {
  data?: {
    symbol: string;
    isActive: boolean;
    isHighlighted: boolean;
  };
}

export const AutomatonView: React.FC = () => {
  const { 
    currentStep, 
    parsingSteps, 
    automaton,
    isGeneratingTable 
  } = useParserStore();
  
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    // This would be populated from the backend automaton data
    // For now, we'll create a simple example
    if (isGeneratingTable) return;

    // Example automaton nodes and edges
    const exampleNodes: AutomatonNode[] = [
      {
        id: '0',
        type: 'default',
        position: { x: 100, y: 100 },
        data: {
          state: 0,
          items: ['[S\' → ·S, $]'],
          isCurrent: currentStep === 0,
          isHighlighted: false,
        },
      },
      {
        id: '1',
        type: 'default',
        position: { x: 300, y: 100 },
        data: {
          state: 1,
          items: ['[S\' → S·, $]'],
          isCurrent: currentStep === 1,
          isHighlighted: false,
        },
      },
      {
        id: '2',
        type: 'default',
        position: { x: 200, y: 250 },
        data: {
          state: 2,
          items: ['[S → ·E, $]', '[E → ·E + T, $]'],
          isCurrent: currentStep === 2,
          isHighlighted: false,
        },
      },
    ];

    const exampleEdges: AutomatonEdge[] = [
      {
        id: 'e0-1',
        source: '0',
        target: '1',
        label: 'S',
        data: {
          symbol: 'S',
          isActive: currentStep >= 1,
          isHighlighted: currentStep === 1,
        },
      },
      {
        id: 'e0-2',
        source: '0',
        target: '2',
        label: 'E',
        data: {
          symbol: 'E',
          isActive: currentStep >= 2,
          isHighlighted: currentStep === 2,
        },
      },
    ];

    setNodes(exampleNodes);
    setEdges(exampleEdges);
  }, [currentStep, isGeneratingTable]);

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge(params, eds));
  }, [setEdges]);

  const nodeTypes = {
    default: ({ data }: { data: AutomatonNode['data'] }) => (
      <div className={`px-4 py-2 bg-white border-2 rounded-lg shadow-sm min-w-[200px] ${
        data.isCurrent 
          ? 'border-primary-500 bg-primary-50 animate-pulse-glow' 
          : 'border-gray-200 hover:border-gray-300'
      }`}>
        <div className="text-center mb-2">
          <div className="text-lg font-bold text-gray-900">
            State {data.state}
          </div>
        </div>
        
        <div className="space-y-1">
          {data.items.map((item, index) => (
            <div 
              key={index}
              className="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-gray-700"
            >
              {item}
            </div>
          ))}
        </div>
        
        {data.isCurrent && (
          <div className="absolute -top-2 -right-2 w-4 h-4 bg-primary-500 rounded-full animate-ping"></div>
        )}
      </div>
    ),
  };

  const edgeOptions = {
    style: {
      strokeWidth: 2,
      stroke: '#6b7280',
    },
    markerEnd: {
      type: 'arrowclosed',
      color: '#6b7280',
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
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-sm text-blue-800">
            <strong>Current State:</strong> {
              nodes.find(n => n.data.isCurrent)?.data.state || 'Unknown'
            }
          </div>
          <div className="text-sm text-blue-700 mt-1">
            {parsingSteps[currentStep]?.explanation}
          </div>
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

      {/* Instructions */}
      <div className="mt-4 text-xs text-gray-500">
        💡 Drag nodes to rearrange, use mouse wheel to zoom
      </div>
    </div>
  );
};

