import React, { useState, useEffect } from 'react';
import { X, Play, FileText, Code, Zap } from 'lucide-react';
import { useParserStore, getExampleGrammars } from '../store/parserStore';
import { ExampleGrammar } from '../types/parser';

interface ExamplesModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const ExamplesModal: React.FC<ExamplesModalProps> = ({ isOpen, onClose }) => {
    const { loadExample } = useParserStore();
    const [examples, setExamples] = useState<Record<string, ExampleGrammar>>({});
    const [isLoading, setIsLoading] = useState(true);
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

    useEffect(() => {
        const fetchExamples = async () => {
            try {
                const response = await getExampleGrammars();
                setExamples(response.examples);
                setSelectedCategory(Object.keys(response.examples)[0]);
            } catch (error) {
                console.error('Failed to fetch examples:', error);
            } finally {
                setIsLoading(false);
            }
        };

        if (isOpen) {
            fetchExamples();
        }
    }, [isOpen]);

    const handleLoadExample = (example: ExampleGrammar) => {
        loadExample(example);
        onClose();
    };

    const getCategoryIcon = (category: string) => {
        switch (category) {
            case 'arithmetic':
                return <Code className="w-5 h-5 text-blue-600" />;
            case 'simple_language':
                return <FileText className="w-5 h-5 text-green-600" />;
            case 'json':
                return <Zap className="w-5 h-5 text-purple-600" />;
            default:
                return <FileText className="w-5 h-5 text-gray-600" />;
        }
    };

    const getCategoryDescription = (category: string) => {
        switch (category) {
            case 'arithmetic':
                return 'Mathematical expressions with operators and precedence';
            case 'simple_language':
                return 'Basic programming language constructs';
            case 'json':
                return 'Structured data format with objects and arrays';
            default:
                return 'Example grammar for learning LR(1) parsing';
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                    <h2 className="text-2xl font-bold text-gray-900">Load Example Grammar</h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <X className="w-6 h-6 text-gray-500" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex h-[calc(90vh-120px)]">
                    {/* Categories Sidebar */}
                    <div className="w-64 bg-gray-50 border-r border-gray-200 overflow-y-auto">
                        <div className="p-4">
                            <h3 className="text-sm font-medium text-gray-700 mb-3">Categories</h3>
                            <div className="space-y-1">
                                {Object.entries(examples).map(([key, example]) => (
                                    <button
                                        key={key}
                                        onClick={() => setSelectedCategory(key)}
                                        className={`w-full text-left p-3 rounded-lg transition-colors ${selectedCategory === key
                                                ? 'bg-blue-100 text-blue-900 border border-blue-200'
                                                : 'hover:bg-gray-100 text-gray-700'
                                            }`}
                                    >
                                        <div className="flex items-center space-x-3">
                                            {getCategoryIcon(key)}
                                            <div>
                                                <div className="font-medium">{example.name}</div>
                                                <div className="text-xs text-gray-500">
                                                    {example.sample_inputs.length} samples
                                                </div>
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Example Details */}
                    <div className="flex-1 overflow-y-auto">
                        {isLoading ? (
                            <div className="flex items-center justify-center h-full">
                                <div className="text-center">
                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                                    <p className="text-gray-600">Loading examples...</p>
                                </div>
                            </div>
                        ) : selectedCategory && examples[selectedCategory] ? (
                            <div className="p-6">
                                <ExampleCard
                                    example={examples[selectedCategory]}
                                    onLoad={() => handleLoadExample(examples[selectedCategory])}
                                />
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-full">
                                <p className="text-gray-600">No examples available</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

interface ExampleCardProps {
    example: ExampleGrammar;
    onLoad: () => void;
}

const ExampleCard: React.FC<ExampleCardProps> = ({ example, onLoad }) => {
    const [showGrammar, setShowGrammar] = useState(false);

    return (
        <div className="max-w-4xl mx-auto">
            {/* Example Header */}
            <div className="mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{example.name}</h3>
                <p className="text-gray-600 text-lg">{example.description}</p>
            </div>

            {/* Sample Strings */}
            <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-3">Sample Strings</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {example.sample_inputs.map((sample, index) => (
                        <div
                            key={index}
                            className="p-3 bg-gray-50 border border-gray-200 rounded-lg"
                        >
                            <code className="text-sm font-mono text-gray-800">{sample}</code>
                        </div>
                    ))}
                </div>
            </div>

            {/* Grammar */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                    <h4 className="text-lg font-semibold text-gray-900">Grammar</h4>
                    <button
                        onClick={() => setShowGrammar(!showGrammar)}
                        className="text-sm text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                    >
                        <span>{showGrammar ? 'Hide' : 'Show'} Grammar</span>
                        {showGrammar ? '↑' : '↓'}
                    </button>
                </div>

                {showGrammar && (
                    <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                        <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap">
                            {example.grammar}
                        </pre>
                    </div>
                )}
            </div>

            {/* Load Button */}
            <div className="flex justify-center">
                <button
                    onClick={onLoad}
                    className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 text-lg"
                >
                    <Play className="w-5 h-5" />
                    <span>Load Example</span>
                </button>
            </div>
        </div>
    );
};
