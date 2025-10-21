import { useEffect, useCallback } from 'react';
import { useParserStore } from '../store/parserStore';

export const useKeyboardShortcuts = () => {
    const {
        currentStep,
        totalSteps,
        isPlaying,
        play,
        pause,
        nextStep,
        previousStep,
        reset,
        setCurrentStep,
    } = useParserStore();

    const handleKeyDown = useCallback((event: KeyboardEvent) => {
        // Don't trigger shortcuts when typing in input fields
        if (
            event.target instanceof HTMLInputElement ||
            event.target instanceof HTMLTextAreaElement ||
            (event.target as HTMLElement)?.contentEditable === 'true'
        ) {
            return;
        }

        // Prevent default behavior for our shortcuts
        const shortcuts = [
            'Space',
            'ArrowLeft',
            'ArrowRight',
            'Home',
            'End',
            'KeyR',
            'KeyP',
            'Escape',
        ];

        if (shortcuts.includes(event.code)) {
            event.preventDefault();
        }

        switch (event.code) {
            case 'Space':
                // Play/Pause
                if (isPlaying) {
                    pause();
                } else {
                    play();
                }
                break;

            case 'ArrowLeft':
                // Previous step
                if (currentStep > 0) {
                    previousStep();
                }
                break;

            case 'ArrowRight':
                // Next step
                if (currentStep < totalSteps - 1) {
                    nextStep();
                }
                break;

            case 'Home':
                // First step
                setCurrentStep(0);
                break;

            case 'End':
                // Last step
                setCurrentStep(totalSteps - 1);
                break;

            case 'KeyR':
                // Reset
                reset();
                break;

            case 'KeyP':
                // Toggle play/pause (alternative to space)
                if (isPlaying) {
                    pause();
                } else {
                    play();
                }
                break;

            case 'Escape':
                // Stop playing and reset
                pause();
                reset();
                break;

            default:
                break;
        }
    }, [
        currentStep,
        totalSteps,
        isPlaying,
        play,
        pause,
        nextStep,
        previousStep,
        reset,
        setCurrentStep,
    ]);

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleKeyDown]);

    // Return shortcut information for display
    return {
        shortcuts: [
            { key: 'Space', description: 'Play/Pause' },
            { key: '←', description: 'Previous step' },
            { key: '→', description: 'Next step' },
            { key: 'Home', description: 'First step' },
            { key: 'End', description: 'Last step' },
            { key: 'R', description: 'Reset' },
            { key: 'P', description: 'Play/Pause' },
            { key: 'Esc', description: 'Stop & Reset' },
        ],
    };
};
