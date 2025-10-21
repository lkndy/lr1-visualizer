import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Play,
    Pause,
    RotateCcw,
    ChevronLeft,
    ChevronRight,
    SkipBack,
    SkipForward,
    Zap,
    CheckCircle,
    AlertCircle,
    ArrowRight,
    ArrowDown
} from 'lucide-react';
import { useParserStore } from '../store/parserStore';

interface ActionTraceItem {
    stepNumber: number;
    action: string;
    description: string;
    isCurrent: boolean;
    isCompleted: boolean;
    actionType: 'shift' | 'reduce' | 'accept' | 'error';
}

export const ActionTracePanel: React.FC = () => {
    const {
        parsingSteps,
        currentStep,
        totalSteps,
        isPlaying,
        setCurrentStep,
        nextStep,
        previousStep,
        play,
        pause,
        reset
    } = useParserStore();

    const [actionTraces, setActionTraces] = useState<ActionTraceItem[]>([]);
    const [autoScroll, setAutoScroll] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (parsingSteps.length === 0) {
            setActionTraces([]);
            return;
        }

        const traces = parsingSteps.map((step, index) => ({
            stepNumber: step.step_number,
            action: step.action?.type?.toUpperCase() || 'UNKNOWN',
            description: step.action?.description || 'No description available',
            isCurrent: index === currentStep,
            isCompleted: index < currentStep,
            actionType: step.action?.type || 'unknown',
        }));

        setActionTraces(traces);
    }, [parsingSteps, currentStep]);

    // Auto-scroll to current step
    useEffect(() => {
        if (autoScroll && scrollRef.current) {
            const currentElement = scrollRef.current.querySelector(`[data-step="${currentStep}"]`);
            if (currentElement) {
                currentElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }
    }, [currentStep, autoScroll]);

    const getActionIcon = (actionType: string) => {
        switch (actionType) {
            case 'shift':
                return <ArrowRight className="w-4 h-4 text-blue-600" />;
            case 'reduce':
                return <ArrowDown className="w-4 h-4 text-green-600" />;
            case 'accept':
                return <CheckCircle className="w-4 h-4 text-purple-600" />;
            case 'error':
                return <AlertCircle className="w-4 h-4 text-red-600" />;
            default:
                return <Zap className="w-4 h-4 text-gray-600" />;
        }
    };

    const getActionColor = (actionType: string, isCurrent: boolean, isCompleted: boolean) => {
        if (isCurrent) return 'bg-yellow-100 border-yellow-300 text-yellow-900';
        if (isCompleted) return 'bg-green-50 border-green-200 text-green-800';

        switch (actionType) {
            case 'shift':
                return 'bg-blue-50 border-blue-200 text-blue-800';
            case 'reduce':
                return 'bg-green-50 border-green-200 text-green-800';
            case 'accept':
                return 'bg-purple-50 border-purple-200 text-purple-800';
            case 'error':
                return 'bg-red-50 border-red-200 text-red-800';
            default:
                return 'bg-gray-50 border-gray-200 text-gray-800';
        }
    };

    const handleStepClick = (stepNumber: number) => {
        setCurrentStep(stepNumber);
    };

    const handlePlayPause = () => {
        if (isPlaying) {
            pause();
        } else {
            play();
        }
    };

    return (
        <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center space-x-2">
                    <Zap className="w-5 h-5 text-blue-600" />
                    <span>Action Trace</span>
                </h3>
                <div className="flex items-center space-x-2">
                    <label className="flex items-center space-x-1 text-sm text-gray-600">
                        <input
                            type="checkbox"
                            checked={autoScroll}
                            onChange={(e) => setAutoScroll(e.target.checked)}
                            className="rounded"
                        />
                        <span>Auto-scroll</span>
                    </label>
                </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2">
                    <button
                        onClick={reset}
                        className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded transition-colors"
                        title="Reset to beginning"
                    >
                        <RotateCcw className="w-4 h-4" />
                    </button>

                    <button
                        onClick={previousStep}
                        disabled={currentStep === 0}
                        className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Previous step"
                    >
                        <ChevronLeft className="w-4 h-4" />
                    </button>

                    <button
                        onClick={handlePlayPause}
                        className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded transition-colors"
                        title={isPlaying ? 'Pause' : 'Play'}
                    >
                        {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>

                    <button
                        onClick={nextStep}
                        disabled={currentStep >= totalSteps - 1}
                        className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Next step"
                    >
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>

                <div className="text-sm text-gray-600">
                    Step {currentStep + 1} of {totalSteps}
                </div>
            </div>

            {/* Action List */}
            <div
                ref={scrollRef}
                className="max-h-96 overflow-y-auto space-y-2"
            >
                <AnimatePresence>
                    {actionTraces.map((trace, index) => (
                        <motion.div
                            key={trace.stepNumber}
                            data-step={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ delay: index * 0.05 }}
                            onClick={() => handleStepClick(index)}
                            className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 hover:shadow-md ${getActionColor(trace.actionType, trace.isCurrent, trace.isCompleted)
                                }`}
                        >
                            <div className="flex items-center space-x-3">
                                {/* Step Number */}
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${trace.isCurrent
                                    ? 'bg-yellow-500 text-white'
                                    : trace.isCompleted
                                        ? 'bg-green-500 text-white'
                                        : 'bg-gray-400 text-white'
                                    }`}>
                                    {trace.stepNumber}
                                </div>

                                {/* Action Icon */}
                                <div className="flex-shrink-0">
                                    {getActionIcon(trace.actionType)}
                                </div>

                                {/* Action Details */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center space-x-2 mb-1">
                                        <span className="font-medium text-sm">
                                            {trace.action}
                                        </span>
                                        {trace.isCurrent && (
                                            <motion.div
                                                animate={{ scale: [1, 1.2, 1] }}
                                                transition={{ duration: 1, repeat: Infinity }}
                                                className="text-yellow-600"
                                            >
                                                <Zap className="w-3 h-3" />
                                            </motion.div>
                                        )}
                                    </div>
                                    <div className="text-xs opacity-75 truncate">
                                        {trace.description}
                                    </div>
                                </div>

                                {/* Status Indicator */}
                                {trace.isCurrent && (
                                    <motion.div
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        className="w-2 h-2 bg-yellow-500 rounded-full"
                                    />
                                )}
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            {/* Legend */}
            <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-gray-600">
                <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <span>Current</span>
                </div>
                <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span>Completed</span>
                </div>
                <div className="flex items-center space-x-1">
                    <ArrowRight className="w-3 h-3 text-blue-600" />
                    <span>Shift</span>
                </div>
                <div className="flex items-center space-x-1">
                    <ArrowDown className="w-3 h-3 text-green-600" />
                    <span>Reduce</span>
                </div>
                <div className="flex items-center space-x-1">
                    <CheckCircle className="w-3 h-3 text-purple-600" />
                    <span>Accept</span>
                </div>
                <div className="flex items-center space-x-1">
                    <AlertCircle className="w-3 h-3 text-red-600" />
                    <span>Error</span>
                </div>
            </div>
        </div>
    );
};
