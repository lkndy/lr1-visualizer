import React, { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParserStore } from '../store/parserStore';

interface StackItem {
  id: string;
  state: number;
  symbol: string;
  isNew: boolean;
  isRemoved: boolean;
}

export const StackVisualizer: React.FC = () => {
  const {
    currentStep,
    parsingSteps,
    tokens,
    currentToken,
    derivationProgress,
    getCurrentStepData
  } = useParserStore();
  const [stackItems, setStackItems] = useState<StackItem[]>([]);
  const [animationKey, setAnimationKey] = useState(0);

  useEffect(() => {
    if (parsingSteps.length === 0 || currentStep >= parsingSteps.length) {
      setStackItems([]);
      return;
    }

    const currentStepData = parsingSteps[currentStep];
    const newStackItems: StackItem[] = currentStepData.stack.map(([state, symbol], index) => ({
      id: `${state}-${symbol}-${index}`,
      state,
      symbol,
      isNew: false,
      isRemoved: false,
    }));

    // Determine which items are new or removed
    const previousStepData = currentStep > 0 ? parsingSteps[currentStep - 1] : null;
    const previousStackItems = previousStepData?.stack.map(([state, symbol], index) => ({
      id: `${state}-${symbol}-${index}`,
      state,
      symbol,
      isNew: false,
      isRemoved: false,
    })) || [];

    // Mark new items
    newStackItems.forEach((item, index) => {
      const wasPresent = previousStackItems.some(
        (prevItem) => prevItem.state === item.state && prevItem.symbol === item.symbol
      );
      if (!wasPresent && index === newStackItems.length - 1) {
        item.isNew = true;
      }
    });

    // Mark removed items (for animation)
    const removedItems: StackItem[] = [];
    previousStackItems.forEach((prevItem) => {
      const isStillPresent = newStackItems.some(
        (item) => item.state === prevItem.state && item.symbol === prevItem.symbol
      );
      if (!isStillPresent) {
        removedItems.push({ ...prevItem, isRemoved: true });
      }
    });

    setStackItems(newStackItems);
    setAnimationKey(prev => prev + 1);
  }, [currentStep, parsingSteps]);

  const currentStepData = getCurrentStepData();

  const actionType = useMemo(() => {
    return currentStepData?.action?.type || null;
  }, [currentStepData]);

  const inputRemaining = useMemo(() => {
    return currentStepData?.input_remaining || [];
  }, [currentStepData]);

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Parser Stack</h2>
        <div className="text-sm text-gray-600">
          {stackItems.length} item{stackItems.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Action Indicator */}
      {actionType && (
        <div className="mb-4">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${actionType === 'shift' ? 'bg-blue-100 text-blue-800' :
            actionType === 'reduce' ? 'bg-green-100 text-green-800' :
              actionType === 'accept' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
            }`}>
            {actionType.toUpperCase()}
          </div>
        </div>
      )}

      {/* Stack Visualization */}
      <div className="bg-gray-50 rounded-lg p-4 min-h-[200px]">
        <div className="flex flex-col-reverse space-y-reverse space-y-2">
          <AnimatePresence mode="popLayout">
            {stackItems.map((item, index) => (
              <motion.div
                key={`${item.id}-${animationKey}`}
                initial={{
                  opacity: item.isNew ? 0 : 1,
                  y: item.isNew ? -20 : 0,
                  scale: item.isNew ? 0.9 : 1
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                  scale: 1
                }}
                exit={{
                  opacity: 0,
                  y: -20,
                  scale: 0.9
                }}
                transition={{
                  duration: 0.3,
                  ease: "easeOut"
                }}
                className={`flex items-center justify-between p-3 bg-white rounded-lg border-2 transition-all duration-200 ${item.isNew
                  ? 'border-primary-300 bg-primary-50 animate-pulse-glow'
                  : 'border-gray-200 hover:border-gray-300'
                  }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-full text-sm font-medium text-gray-600">
                    {index}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      State {item.state}
                    </div>
                    <div className="text-xs text-gray-600">
                      Symbol: {item.symbol}
                    </div>
                  </div>
                </div>

                {item.isNew && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.1, duration: 0.2 }}
                    className="text-primary-600 text-xs font-medium"
                  >
                    NEW
                  </motion.div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Empty State */}
        {stackItems.length === 0 && (
          <div className="flex items-center justify-center h-32 text-gray-500">
            <div className="text-center">
              <div className="text-lg mb-2">📚</div>
              <div className="text-sm">Stack is empty</div>
            </div>
          </div>
        )}
      </div>

      {/* Input Tokens Display */}
      {tokens.length > 0 && (
        <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="text-sm text-gray-600 mb-2">Input Tokens:</div>
          <div className="flex flex-wrap gap-1">
            {tokens.map((token, index) => {
              const isProcessed = index < tokens.length - (inputRemaining?.length || 0);
              const isCurrent = token === currentToken;
              return (
                <span
                  key={index}
                  className={`px-2 py-1 rounded text-sm font-mono ${isCurrent
                    ? 'bg-yellow-200 border-2 border-yellow-500 font-bold'
                    : isProcessed
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-200 text-gray-600'
                    }`}
                >
                  {token}
                </span>
              );
            })}
          </div>
          {currentToken && (
            <div className="text-sm text-yellow-700 mt-2">
              <strong>Current Token:</strong> {currentToken}
            </div>
          )}
        </div>
      )}

      {/* Derivation Progress */}
      {derivationProgress && (
        <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
          <div className="text-sm text-purple-600 mb-1">Derivation Progress:</div>
          <div className="font-mono text-lg text-purple-900">{derivationProgress}</div>
        </div>
      )}

      {/* Stack Info */}
      {stackItems.length > 0 && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-sm text-blue-800">
            <strong>Top of Stack:</strong> State {stackItems[stackItems.length - 1].state}, Symbol '{stackItems[stackItems.length - 1].symbol}'
          </div>
          <div className="text-sm text-blue-700 mt-1">
            {actionType === 'shift' && 'Pushing new state and symbol onto stack'}
            {actionType === 'reduce' && 'Popping symbols and pushing new non-terminal'}
            {actionType === 'accept' && 'Parsing completed successfully'}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 flex items-center space-x-4 text-xs text-gray-600">
        <div className="flex items-center space-x-1">
          <div className="w-3 h-3 bg-primary-100 border border-primary-300 rounded"></div>
          <span>New item</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-3 h-3 bg-gray-100 border border-gray-300 rounded"></div>
          <span>Existing item</span>
        </div>
      </div>
    </div>
  );
};
