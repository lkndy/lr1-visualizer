import React from 'react';
import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward, 
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Settings
} from 'lucide-react';
import { useParserStore } from '../store/parserStore';

export const StepControls: React.FC = () => {
  const {
    currentStep,
    totalSteps,
    isPlaying,
    playSpeed,
    setPlaySpeed,
    nextStep,
    previousStep,
    play,
    pause,
    reset,
    parsingSteps,
  } = useParserStore();

  const handlePlayPause = () => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  };

  const handleStepForward = () => {
    nextStep();
  };

  const handleStepBackward = () => {
    previousStep();
  };

  const handleReset = () => {
    reset();
  };

  const handleSpeedChange = (speed: number) => {
    setPlaySpeed(speed);
  };

  const progress = totalSteps > 0 ? ((currentStep + 1) / totalSteps) * 100 : 0;

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Step Controls</h2>
        <div className="text-sm text-gray-600">
          {totalSteps > 0 ? `${currentStep + 1} / ${totalSteps}` : 'No steps'}
        </div>
      </div>

      {/* Progress Bar */}
      {totalSteps > 0 && (
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Step {currentStep + 1}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Control Buttons */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <button
          onClick={handleStepBackward}
          disabled={currentStep === 0 || totalSteps === 0}
          className="btn-secondary flex items-center justify-center space-x-2"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Previous</span>
        </button>
        
        <button
          onClick={handleStepForward}
          disabled={currentStep >= totalSteps - 1 || totalSteps === 0}
          className="btn-secondary flex items-center justify-center space-x-2"
        >
          <span>Next</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Play/Pause and Reset */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <button
          onClick={handlePlayPause}
          disabled={totalSteps === 0}
          className="btn-primary flex items-center justify-center space-x-2"
        >
          {isPlaying ? (
            <>
              <Pause className="w-4 h-4" />
              <span>Pause</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Play</span>
            </>
          )}
        </button>
        
        <button
          onClick={handleReset}
          disabled={totalSteps === 0}
          className="btn-secondary flex items-center justify-center space-x-2"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reset</span>
        </button>
      </div>

      {/* Speed Control */}
      {totalSteps > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">
              <Settings className="w-4 h-4 inline mr-1" />
              Speed
            </label>
            <span className="text-sm text-gray-600">{playSpeed}x</span>
          </div>
          
          <input
            type="range"
            min="0.1"
            max="3"
            step="0.1"
            value={playSpeed}
            onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
          />
          
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0.1x</span>
            <span>3.0x</span>
          </div>
        </div>
      )}

      {/* Current Step Info */}
      {parsingSteps.length > 0 && currentStep < parsingSteps.length && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="text-sm text-gray-600 mb-2">Current Action:</div>
          <div className="font-medium text-gray-900">
            {parsingSteps[currentStep]?.action.action_type.toUpperCase()}
            {parsingSteps[currentStep]?.action.target !== undefined && 
              ` ${parsingSteps[currentStep].action.target}`
            }
          </div>
          
          {parsingSteps[currentStep]?.current_token && (
            <div className="mt-2">
              <div className="text-sm text-gray-600 mb-1">Token:</div>
              <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                {parsingSteps[currentStep].current_token}
              </code>
            </div>
          )}
        </div>
      )}

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
        }
        
        .slider::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: none;
        }
      `}</style>
    </div>
  );
};
