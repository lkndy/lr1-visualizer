import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { motion } from 'framer-motion';
import { useParserStore } from '../store/parserStore';
import { ASTNode } from '../types/parser';

interface ASTVisualizationNode {
  id: string;
  symbol: string;
  x: number;
  y: number;
  isNew: boolean;
  isHighlighted: boolean;
  nodeType: 'terminal' | 'non_terminal' | 'epsilon';
}

interface ASTVisualizationEdge {
  id: string;
  source: string;
  target: string;
  isNew: boolean;
  isHighlighted: boolean;
}

export const ASTVisualizer: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);
  const { currentStep, parsingSteps, ast } = useParserStore();
  const [nodes, setNodes] = useState<ASTVisualizationNode[]>([]);
  const [edges, setEdges] = useState<ASTVisualizationEdge[]>([]);
  const [dimensions, setDimensions] = useState({ width: 400, height: 300 });

  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef.current) {
        const rect = svgRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width || 400, height: rect.height || 300 });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (!ast || !ast.nodes) {
      setNodes([]);
      setEdges([]);
      return;
    }

    // Build tree structure from AST nodes
    const astNodes = Object.values(ast.nodes) as ASTNode[];
    const nodeMap = new Map(astNodes.map(node => [node.id, node]));
    
    // Find root node
    const rootNode = astNodes.find(node => !node.parent) || astNodes[0];
    if (!rootNode) return;

    // Create hierarchical layout
    const treeData = buildTreeStructure(rootNode, nodeMap);
    const layout = d3.tree<{ id: string; symbol: string; nodeType: string }>()
      .size([dimensions.width - 40, dimensions.height - 40]);

    const root = d3.hierarchy(treeData);
    layout(root);

    // Convert to visualization nodes and edges
    const newNodes: ASTVisualizationNode[] = [];
    const newEdges: ASTVisualizationEdge[] = [];

    root.descendants().forEach((d, index) => {
      const node = nodeMap.get(d.data.id);
      if (node) {
        newNodes.push({
          id: node.id,
          symbol: node.symbol,
          x: d.x || 0,
          y: d.y || 0,
          isNew: currentStep > 0 && parsingSteps[currentStep]?.ast_nodes?.some(
            astNode => astNode.id === node.id
          ),
          isHighlighted: false,
          nodeType: node.symbol_type as 'terminal' | 'non_terminal' | 'epsilon',
        });

        if (d.parent) {
          newEdges.push({
            id: `${d.parent.data.id}-${d.data.id}`,
            source: d.parent.data.id,
            target: d.data.id,
            isNew: currentStep > 0 && parsingSteps[currentStep]?.ast_nodes?.some(
              astNode => astNode.id === node.id
            ),
            isHighlighted: false,
          });
        }
      }
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [ast, currentStep, parsingSteps, dimensions]);

  const buildTreeStructure = (node: ASTNode, nodeMap: Map<string, ASTNode>): any => {
    const children = node.children
      .map(childId => nodeMap.get(childId))
      .filter(Boolean)
      .map(child => buildTreeStructure(child!, nodeMap));

    return {
      id: node.id,
      symbol: node.symbol,
      nodeType: node.symbol_type,
      children,
    };
  };

  const getNodeColor = (nodeType: string, isHighlighted: boolean) => {
    if (isHighlighted) return '#3b82f6';
    
    switch (nodeType) {
      case 'terminal':
        return '#dc2626';
      case 'non_terminal':
        return '#7c3aed';
      case 'epsilon':
        return '#6b7280';
      default:
        return '#374151';
    }
  };

  const getNodeSize = (nodeType: string) => {
    switch (nodeType) {
      case 'terminal':
        return 25;
      case 'non_terminal':
        return 35;
      default:
        return 20;
    }
  };

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Create container for zooming and panning
    const container = svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 3])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Draw edges
    const link = container.selectAll('.link')
      .data(edges)
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('d', (d) => {
        const sourceNode = nodes.find(n => n.id === d.source);
        const targetNode = nodes.find(n => n.id === d.target);
        
        if (!sourceNode || !targetNode) return '';
        
        return `M ${sourceNode.x} ${sourceNode.y} L ${targetNode.x} ${targetNode.y}`;
      })
      .attr('stroke', (d) => d.isNew ? '#3b82f6' : '#6b7280')
      .attr('stroke-width', (d) => d.isNew ? 3 : 2)
      .attr('stroke-dasharray', (d) => d.isNew ? '5,5' : 'none')
      .attr('opacity', (d) => d.isNew ? 0.8 : 0.6);

    // Draw nodes
    const node = container.selectAll('.node')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', (d) => `translate(${d.x},${d.y})`);

    // Add circles for nodes
    node.append('circle')
      .attr('r', (d) => getNodeSize(d.nodeType))
      .attr('fill', (d) => getNodeColor(d.nodeType, d.isHighlighted))
      .attr('stroke', (d) => d.isNew ? '#3b82f6' : '#ffffff')
      .attr('stroke-width', (d) => d.isNew ? 3 : 2)
      .attr('opacity', (d) => d.isNew ? 0.9 : 1);

    // Add text labels
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '.35em')
      .attr('fill', '#ffffff')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .text((d) => d.symbol);

    // Add animations for new nodes
    if (nodes.some(n => n.isNew)) {
      node.filter(d => d.isNew)
        .style('opacity', 0)
        .transition()
        .duration(500)
        .style('opacity', 1);

      link.filter(d => d.isNew)
        .style('opacity', 0)
        .transition()
        .duration(500)
        .style('opacity', 0.8);
    }

  }, [nodes, edges, dimensions]);

  const nodeTypeCounts = nodes.reduce((acc, node) => {
    acc[node.nodeType] = (acc[node.nodeType] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Abstract Syntax Tree</h2>
        <div className="text-sm text-gray-600">
          {nodes.length} node{nodes.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* AST Statistics */}
      {Object.keys(nodeTypeCounts).length > 0 && (
        <div className="mb-4 grid grid-cols-3 gap-2">
          {Object.entries(nodeTypeCounts).map(([type, count]) => (
            <div key={type} className="text-center p-2 bg-gray-50 rounded">
              <div className="text-lg font-bold" style={{ color: getNodeColor(type, false) }}>
                {count}
              </div>
              <div className="text-xs text-gray-600 capitalize">
                {type.replace('_', ' ')}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* SVG Container */}
      <div className="border border-gray-200 rounded-lg bg-gray-50" style={{ height: '400px' }}>
        {nodes.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-lg mb-2">🌳</div>
              <div className="text-sm">No AST nodes yet</div>
              <div className="text-xs text-gray-400 mt-1">
                Start parsing to see the tree construction
              </div>
            </div>
          </div>
        ) : (
          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            style={{ cursor: 'grab' }}
          >
            {/* This will be populated by D3 */}
          </svg>
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="flex items-center space-x-2">
          <div 
            className="w-4 h-4 rounded-full border-2 border-white"
            style={{ backgroundColor: getNodeColor('non_terminal', false) }}
          ></div>
          <span className="text-sm text-gray-600">Non-terminal</span>
        </div>
        <div className="flex items-center space-x-2">
          <div 
            className="w-4 h-4 rounded-full border-2 border-white"
            style={{ backgroundColor: getNodeColor('terminal', false) }}
          ></div>
          <span className="text-sm text-gray-600">Terminal</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-primary-100 border-2 border-primary-300 rounded-full"></div>
          <span className="text-sm text-gray-600">New node</span>
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-4 text-xs text-gray-500">
        💡 Use mouse wheel to zoom, drag to pan
      </div>
    </div>
  );
};
