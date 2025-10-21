import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Target, Zap } from 'lucide-react';
import { useParserStore } from '../store/parserStore';

interface DerivationStep {
    stepNumber: number;
    derivation: string;
    action: string;
    isCurrent: boolean;
}

export const DerivationVisualizer: React.FC = () => {
    const { parsingSteps, currentStep, getCurrentStepData } = useParserStore();
    const [derivationSteps, setDerivationSteps] = useState<DerivationStep[]>([]);
    const [showAllSteps, setShowAllSteps] = useState(false);

    useEffect(() => {
        if (parsingSteps.length === 0) {
            setDerivationSteps([]);
            return;
        }

        const steps = parsingSteps.map((step, index) => ({
            stepNumber: step.step_number,
            derivation: step.derivation_so_far,
            action: step.action?.description || 'No action description',
            isCurrent: index === currentStep,
        }));

        setDerivationSteps(steps);
    }, [parsingSteps, currentStep]);

    const currentDerivation = derivationSteps[currentStep]?.derivation || '';
    const previousDerivation = currentStep > 0 ? derivationSteps[currentStep - 1]?.derivation : '';
    const currentStepData = getCurrentStepData();

    // Calculate differences between current and previous derivation
    const changes = useMemo(() => {
        if (!previousDerivation || !currentDerivation) {
            return { added: currentDerivation, removed: '' };
        }

        // Simple diff algorithm for derivation strings
        const prevParts = previousDerivation.split(' ');
        const currParts = currentDerivation.split(' ');

        let added = '';
        let removed = '';

        // Find what was added
        for (let i = 0; i < currParts.length; i++) {
            if (i >= prevParts.length || currParts[i] !== prevParts[i]) {
                added = currParts.slice(i).join(' ');
                break;
            }
        }

        // Find what was removed
        for (let i = 0; i < prevParts.length; i++) {
            if (i >= currParts.length || prevParts[i] !== currParts[i]) {
                removed = prevParts.slice(i).join(' ');
                break;
            }
        }

        return { added, removed };
    }, [previousDerivation, currentDerivation]);

    return (
        <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center space-x-2">
                    <Target className="w-5 h-5 text-purple-600" />
                    <span>Derivation Progress</span>
                </h3>
                <button
                    onClick={() => setShowAllSteps(!showAllSteps)}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                    {showAllSteps ? 'Show Current Only' : 'Show All Steps'}
                </button>
            </div>

            {/* Current Derivation - Prominent Display */}
            <div className="mb-6">
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                        <Zap className="w-4 h-4 text-purple-600" />
                        <span className="text-sm font-medium text-purple-800">Current Derivation</span>
                    </div>

                    <div className="font-mono text-xl text-purple-900 bg-white p-3 rounded border min-h-[3rem] flex items-center">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={currentDerivation}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.3 }}
                                className="flex items-center space-x-1"
                            >
                                {currentDerivation.split(' ').map((part, index) => {
                                    const isNew = changes.added.includes(part) && index >= currentDerivation.split(' ').length - changes.added.split(' ').length;
                                    return (
                                        <motion.span
                                            key={`${part}-${index}`}
                                            initial={isNew ? { scale: 1.2, backgroundColor: '#fef3c7' } : {}}
                                            animate={{ scale: 1, backgroundColor: 'transparent' }}
                                            transition={{ duration: 0.5 }}
                                            className={`px-2 py-1 rounded ${isNew ? 'bg-yellow-200 text-yellow-900 font-bold' : 'text-purple-900'
                                                }`}
                                        >
                                            {part}
                                        </motion.span>
                                    );
                                })}
                            </motion.div>
                        </AnimatePresence>
                    </div>

                    {/* Action Description */}
                    {currentStepData?.action && (
                        <div className="mt-3 text-sm text-purple-700">
                            <strong>Action:</strong> {currentStepData.action.description || 'No description available'}
                        </div>
                    )}
                </div>
            </div>

            {/* All Steps (Collapsible) */}
            <AnimatePresence>
                {showAllSteps && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                        className="space-y-2"
                    >
                        <h4 className="text-md font-medium text-gray-700 mb-3">All Derivation Steps</h4>
                        <div className="max-h-64 overflow-y-auto space-y-2">
                            {derivationSteps.map((step, index) => (
                                <motion.div
                                    key={step.stepNumber}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                    className={`p-3 rounded-lg border transition-all duration-200 ${step.isCurrent
                                        ? 'bg-yellow-50 border-yellow-300 shadow-md'
                                        : 'bg-gray-50 border-gray-200'
                                        }`}
                                >
                                    <div className="flex items-center space-x-3">
                                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step.isCurrent
                                            ? 'bg-yellow-500 text-white'
                                            : 'bg-gray-400 text-white'
                                            }`}>
                                            {step.stepNumber}
                                        </div>

                                        <div className="flex-1">
                                            <div className="font-mono text-sm text-gray-800 mb-1">
                                                {step.derivation}
                                            </div>
                                            <div className="text-xs text-gray-600">
                                                {step.action}
                                            </div>
                                        </div>

                                        {step.isCurrent && (
                                            <motion.div
                                                animate={{ scale: [1, 1.2, 1] }}
                                                transition={{ duration: 1, repeat: Infinity }}
                                                className="text-yellow-600"
                                            >
                                                <ArrowRight className="w-4 h-4" />
                                            </motion.div>
                                        )}
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Legend */}
            <div className="mt-4 flex items-center space-x-4 text-xs text-gray-600">
                <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-yellow-200 rounded"></div>
                    <span>New/Changed</span>
                </div>
                <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-purple-200 rounded"></div>
                    <span>Current Step</span>
                </div>
                <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-gray-200 rounded"></div>
                    <span>Previous Steps</span>
                </div>
            </div>
        </div>
    );
};
