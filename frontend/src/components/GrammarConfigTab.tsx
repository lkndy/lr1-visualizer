import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, FileText, Upload, Terminal, Hash, List, Eye, EyeOff } from 'lucide-react';
import { useParserStore } from '../store/parserStore';
import { GrammarEditor } from './GrammarEditor';
import { ParsingTable } from './ParsingTable';
import { LoadingSpinner, SkeletonCard, SkeletonText } from './LoadingSpinner';

export const GrammarConfigTab: React.FC = () => {
    const {
        grammarText,
        grammarValid,
        grammarInfo,
        grammarErrors,
        isValidatingGrammar,
        actionTable,
        gotoTable,
        showConflicts,
        setShowConflicts,
    } = useParserStore();

    // Pagination state for LR(1) States
    const [currentPage, setCurrentPage] = useState(1);

    // Reset pagination when grammar changes
    useEffect(() => {
        setCurrentPage(1);
    }, [grammarInfo]);

    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
        terminals: true,
        nonTerminals: true,
        productions: true,
        firstSets: false,
        followSets: false,
        lr1States: false,
        parsingTable: false,
        automaton: false,
    });

    const toggleSection = (section: string) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const SectionHeader: React.FC<{
        id: string;
        title: string;
        icon: React.ReactNode;
        badge?: string;
        badgeColor?: string;
    }> = ({ id, title, icon, badge, badgeColor = "bg-blue-100 text-blue-800" }) => (
        <button
            onClick={() => toggleSection(id)}
            className="w-full flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
            <div className="flex items-center space-x-3">
                {expandedSections[id] ? (
                    <ChevronDown className="w-5 h-5 text-gray-500" />
                ) : (
                    <ChevronRight className="w-5 h-5 text-gray-500" />
                )}
                {icon}
                <span className="font-medium text-gray-900">{title}</span>
                {badge && (
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${badgeColor}`}>
                        {badge}
                    </span>
                )}
            </div>
        </button>
    );

    const SectionContent: React.FC<{ id: string; children: React.ReactNode }> = ({ id, children }) => (
        expandedSections[id] && (
            <div className="mt-2 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                {children}
            </div>
        )
    );

    const renderSymbols = (symbols: Array<{ name: string; type: string }>, symbolType: 'terminal' | 'non_terminal') => (
        <div className="flex flex-wrap gap-2">
            {symbols.map((symbol, index) => (
                <span
                    key={index}
                    className={`px-3 py-1 rounded-full text-sm font-medium ${symbolType === 'terminal'
                        ? 'bg-green-100 text-green-800 border border-green-200'
                        : 'bg-purple-100 text-purple-800 border border-purple-200'
                        }`}
                >
                    {symbol.name}
                </span>
            ))}
        </div>
    );

    const renderFirstFollowSets = (sets: Record<string, string[]>, title: string) => (
        <div className="space-y-3">
            {Object.entries(sets).map(([symbol, setItems]) => (
                <div key={symbol} className="flex items-center space-x-3">
                    <span className="font-medium text-gray-700 w-20">{symbol}:</span>
                    <div className="flex flex-wrap gap-1">
                        <span className="text-gray-600">{"{"}</span>
                        {setItems.map((item, index) => (
                            <span key={index} className="text-gray-800">
                                {item}
                                {index < setItems.length - 1 && <span className="text-gray-500">, </span>}
                            </span>
                        ))}
                        <span className="text-gray-600">{"}"}</span>
                    </div>
                </div>
            ))}
        </div>
    );

    const renderProductions = (productions: Array<{ lhs: string; rhs: string[]; index: number }>) => (
        <div className="space-y-2">
            {productions.map((prod, index) => (
                <div key={index} className="flex items-center space-x-2 font-mono text-sm">
                    <span className="text-blue-600 font-medium">#{prod.index}</span>
                    <span className="text-purple-600 font-medium">{prod.lhs}</span>
                    <span className="text-gray-500">→</span>
                    <span className="text-gray-800">
                        {prod.rhs.length === 0 ? (
                            <span className="text-gray-500 italic">ε</span>
                        ) : (
                            prod.rhs.join(' ')
                        )}
                    </span>
                </div>
            ))}
        </div>
    );

    const renderLR1States = (states: Array<{
        state_number: number;
        items: string[];
        shift_symbols: string[];
        reduce_items: string[];
    }>) => {
        const itemsPerPage = 9; // 3x3 grid

        const totalPages = Math.ceil(states.length / itemsPerPage);
        const startIdx = (currentPage - 1) * itemsPerPage;
        const paginatedStates = states.slice(startIdx, startIdx + itemsPerPage);

        const goToPage = (page: number) => {
            setCurrentPage(Math.max(1, Math.min(page, totalPages)));
        };

        return (
            <div className="space-y-4">
                {/* Pagination Controls */}
                <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-600">
                        Showing {startIdx + 1}-{Math.min(startIdx + itemsPerPage, states.length)} of {states.length} states
                    </div>
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={() => goToPage(currentPage - 1)}
                            disabled={currentPage === 1}
                            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>
                        <span className="text-sm text-gray-600">
                            Page {currentPage} of {totalPages}
                        </span>
                        <button
                            onClick={() => goToPage(currentPage + 1)}
                            disabled={currentPage === totalPages}
                            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Next
                        </button>
                    </div>
                </div>

                {/* States Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {paginatedStates.map((state, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-3">
                                <h4 className="font-semibold text-gray-900">State {state.state_number}</h4>
                                <div className="flex flex-col space-y-1">
                                    {state.shift_symbols.length > 0 && (
                                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                            Shift: {state.shift_symbols.slice(0, 2).join(', ')}{state.shift_symbols.length > 2 ? '...' : ''}
                                        </span>
                                    )}
                                    {state.reduce_items.length > 0 && (
                                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                                            Reduce: {state.reduce_items.length} items
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div className="space-y-1 max-h-32 overflow-y-auto">
                                {state.items.slice(0, 4).map((item, itemIndex) => (
                                    <div key={itemIndex} className="font-mono text-xs text-gray-700 bg-gray-50 px-2 py-1 rounded break-words">
                                        {item.length > 40 ? item.substring(0, 40) + '...' : item}
                                    </div>
                                ))}
                                {state.items.length > 4 && (
                                    <div className="text-xs text-gray-500 text-center py-1">
                                        +{state.items.length - 4} more items
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Left Column - Grammar Editor */}
            <div className="xl:col-span-1 space-y-6">
                <div className="card p-6">
                    <div className="flex items-center space-x-2 mb-4">
                        <FileText className="w-5 h-5 text-blue-600" />
                        <h2 className="text-lg font-semibold">Grammar Definition</h2>
                    </div>
                    <GrammarEditor />

                    {/* File Upload Section */}
                    <div className="mt-4 pt-4 border-t border-gray-200">
                        <label className="flex items-center space-x-2 text-sm text-gray-600 cursor-pointer">
                            <Upload className="w-4 h-4" />
                            <span>Upload .lark file</span>
                            <input
                                type="file"
                                accept=".lark"
                                className="hidden"
                                onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) {
                                        const reader = new FileReader();
                                        reader.onload = (event) => {
                                            const content = event.target?.result as string;
                                            useParserStore.getState().setGrammarText(content);
                                        };
                                        reader.readAsText(file);
                                    }
                                }}
                            />
                        </label>
                    </div>
                </div>

                {/* Grammar Stats */}
                <div className="card p-6">
                    <h3 className="text-lg font-semibold mb-4">Grammar Statistics</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-blue-50 p-4 rounded-lg">
                            <div className="text-2xl font-bold text-blue-600">
                                {grammarInfo?.num_productions || 0}
                            </div>
                            <div className="text-sm text-blue-600">Productions</div>
                        </div>
                        <div className="bg-green-50 p-4 rounded-lg">
                            <div className="text-2xl font-bold text-green-600">
                                {grammarInfo?.num_terminals || 0}
                            </div>
                            <div className="text-sm text-green-600">Terminals</div>
                        </div>
                        <div className="bg-purple-50 p-4 rounded-lg">
                            <div className="text-2xl font-bold text-purple-600">
                                {grammarInfo?.num_non_terminals || 0}
                            </div>
                            <div className="text-sm text-purple-600">Non-terminals</div>
                        </div>
                        <div className="bg-orange-50 p-4 rounded-lg">
                            <div className="text-2xl font-bold text-orange-600">
                                {grammarInfo?.num_states || 0}
                            </div>
                            <div className="text-sm text-orange-600">States</div>
                        </div>
                    </div>

                    <div className="mt-4 pt-4 border-t border-gray-200">
                        <div className="text-sm text-gray-600 mb-2">Grammar Type:</div>
                        <div className="text-lg font-medium">
                            {grammarInfo?.grammar_type || 'Unknown'}
                        </div>
                    </div>
                </div>
            </div>

            {/* Right Column - Grammar Analysis */}
            <div className="xl:col-span-2 space-y-6">
                {isValidatingGrammar && (
                    <div className="space-y-4">
                        <div className="card p-6 text-center">
                            <LoadingSpinner size="lg" text="Analyzing grammar..." />
                        </div>
                        <SkeletonCard />
                        <SkeletonCard />
                        <SkeletonCard />
                    </div>
                )}

                {!grammarValid && grammarErrors.length > 0 && (
                    <div className="card p-6">
                        <h3 className="text-lg font-semibold text-red-600 mb-4">Grammar Errors</h3>
                        <div className="space-y-2">
                            {grammarErrors.map((error, index) => (
                                <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                                    <div className="font-medium text-red-800">{error.type}</div>
                                    <div className="text-red-700">{error.message}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {grammarValid && grammarInfo && (
                    <>
                        {/* Terminals */}
                        <div className="space-y-2">
                            <SectionHeader
                                id="terminals"
                                title="Terminals"
                                icon={<Terminal className="w-5 h-5 text-green-600" />}
                                badge={`${grammarInfo.terminals_list.length}`}
                                badgeColor="bg-green-100 text-green-800"
                            />
                            <SectionContent id="terminals">
                                {renderSymbols(grammarInfo.terminals_list, 'terminal')}
                            </SectionContent>
                        </div>

                        {/* Non-terminals */}
                        <div className="space-y-2">
                            <SectionHeader
                                id="nonTerminals"
                                title="Non-terminals"
                                icon={<Hash className="w-5 h-5 text-purple-600" />}
                                badge={`${grammarInfo.non_terminals_list.length}`}
                                badgeColor="bg-purple-100 text-purple-800"
                            />
                            <SectionContent id="nonTerminals">
                                {renderSymbols(grammarInfo.non_terminals_list, 'non_terminal')}
                            </SectionContent>
                        </div>

                        {/* Productions */}
                        <div className="space-y-2">
                            <SectionHeader
                                id="productions"
                                title="Productions"
                                icon={<List className="w-5 h-5 text-blue-600" />}
                                badge={`${grammarInfo.productions_detailed.length}`}
                            />
                            <SectionContent id="productions">
                                {renderProductions(grammarInfo.productions_detailed)}
                            </SectionContent>
                        </div>

                        {/* FIRST Sets */}
                        <div className="space-y-2">
                            <SectionHeader
                                id="firstSets"
                                title="FIRST Sets"
                                icon={<Eye className="w-5 h-5 text-indigo-600" />}
                                badge={`${Object.keys(grammarInfo.first_sets || {}).length}`}
                                badgeColor="bg-indigo-100 text-indigo-800"
                            />
                            <SectionContent id="firstSets">
                                {renderFirstFollowSets(grammarInfo.first_sets || {}, 'FIRST')}
                            </SectionContent>
                        </div>

                        {/* FOLLOW Sets */}
                        <div className="space-y-2">
                            <SectionHeader
                                id="followSets"
                                title="FOLLOW Sets"
                                icon={<EyeOff className="w-5 h-5 text-pink-600" />}
                                badge={`${Object.keys(grammarInfo.follow_sets || {}).length}`}
                                badgeColor="bg-pink-100 text-pink-800"
                            />
                            <SectionContent id="followSets">
                                {renderFirstFollowSets(grammarInfo.follow_sets || {}, 'FOLLOW')}
                            </SectionContent>
                        </div>

                        {/* LR(1) States */}
                        <div className="space-y-2">
                            <SectionHeader
                                id="lr1States"
                                title="LR(1) States"
                                icon={<Hash className="w-5 h-5 text-gray-600" />}
                                badge={`${grammarInfo.lr1_states.length}`}
                                badgeColor="bg-gray-100 text-gray-800"
                            />
                            <SectionContent id="lr1States">
                                {renderLR1States(grammarInfo.lr1_states)}
                            </SectionContent>
                        </div>

                        {/* Parsing Tables */}
                        <div className="space-y-2">
                            <SectionHeader
                                id="parsingTable"
                                title="Parsing Tables"
                                icon={<List className="w-5 h-5 text-amber-600" />}
                                badge="ACTION & GOTO"
                                badgeColor="bg-amber-100 text-amber-800"
                            />
                            <SectionContent id="parsingTable">
                                <ParsingTable />
                            </SectionContent>
                        </div>

                    </>
                )}
            </div>

        </div>
    );
};
