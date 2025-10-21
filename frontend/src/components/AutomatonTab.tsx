import React from 'react';
import { useParserStore } from '../store/parserStore';
import { AutomatonView } from './AutomatonView';
import { LoadingSpinner } from './LoadingSpinner';

export const AutomatonTab: React.FC = () => {
    const { grammarValid, grammarInfo, isValidatingGrammar } = useParserStore();

    if (isValidatingGrammar) {
        return (
            <div className="flex items-center justify-center py-12">
                <LoadingSpinner />
            </div>
        );
    }

    if (!grammarValid || !grammarInfo) {
        return (
            <div className="text-center py-12">
                <div className="text-gray-500 text-lg mb-4">
                    Please configure a valid grammar first
                </div>
                <div className="text-gray-400 text-sm">
                    Go to the Grammar Configuration tab to set up your grammar
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-900">
                        LR(1) Automaton Visualization
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">
                        Interactive visualization of the LR(1) parsing automaton with {grammarInfo.num_states} states
                    </p>
                </div>
                <div className="p-6">
                    <div className="h-[70vh] min-h-[600px]">
                        <AutomatonView />
                    </div>
                </div>
            </div>
        </div>
    );
};
