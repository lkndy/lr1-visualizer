import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Play } from 'lucide-react';
import { useParserStore } from '../store/parserStore';
import { getExampleGrammars } from '../api/client';
import { ExampleGrammar } from '../types/parser';

export const ExamplesPanel: React.FC = () => {
  const { selectedExample, loadExample } = useParserStore();
  const [isExpanded, setIsExpanded] = useState(false);
  const [examples, setExamples] = useState<Record<string, ExampleGrammar>>({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchExamples = async () => {
      try {
        const response = await getExampleGrammars();
        setExamples(response.examples);
      } catch (error) {
        console.error('Failed to fetch examples:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchExamples();
  }, []);

  const handleLoadExample = (example: ExampleGrammar) => {
    loadExample(example);
    setIsExpanded(false);
  };

  if (isLoading) {
    return (
      <div className="mb-6">
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-4">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <div className="bg-white rounded-lg shadow-md border border-gray-200">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
        >
          <div>
            <h3 className="font-medium text-gray-900">Example Grammars</h3>
            <p className="text-sm text-gray-600">
              {selectedExample ? `Selected: ${selectedExample}` : 'Click to load example grammars'}
            </p>
          </div>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </button>

        {isExpanded && (
          <div className="border-t border-gray-200 p-4 space-y-3">
            {Object.entries(examples).map(([key, example]) => (
              <div
                key={key}
                className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 mb-1">{example.name}</h4>
                    <p className="text-sm text-gray-600 mb-3">{example.description}</p>

                    <div className="bg-gray-50 rounded p-3 mb-3">
                      <div className="text-xs text-gray-500 mb-1">Sample Inputs:</div>
                      <div className="space-y-1">
                        {example.sample_inputs.slice(0, 2).map((input, idx) => (
                          <code key={idx} className="text-sm font-mono text-gray-800 block">{input}</code>
                        ))}
                        {example.sample_inputs.length > 2 && (
                          <div className="text-xs text-gray-500">+{example.sample_inputs.length - 2} more...</div>
                        )}
                      </div>
                    </div>

                    <div className="bg-gray-900 rounded p-3">
                      <div className="text-xs text-gray-400 mb-1">Grammar:</div>
                      <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">
                        {example.grammar}
                      </pre>
                    </div>
                  </div>

                  <button
                    onClick={() => handleLoadExample(example)}
                    className="ml-4 btn-primary flex items-center space-x-1 text-sm"
                  >
                    <Play className="w-3 h-3" />
                    <span>Load</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
