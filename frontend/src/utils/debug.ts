/** Debug utilities for the LR(1) Parser Visualizer frontend. */

interface DebugData {
  [key: string]: any;
}

// Debug flag from environment variable
const DEBUG = import.meta.env.VITE_DEBUG === 'true' || import.meta.env.DEV;

// Color codes for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
};

function getTimestamp(): string {
  const now = new Date();
  return now.toTimeString().split(' ')[0] + '.' + now.getMilliseconds().toString().padStart(3, '0');
}

function formatMessage(emoji: string, message: string, color: string = colors.white): string {
  const timestamp = getTimestamp();
  return `${colors.dim}[${timestamp}]${colors.reset} ${emoji} ${color}${message}${colors.reset}`;
}

export const debug = {
  log: (message: string, data?: DebugData): void => {
    if (DEBUG) {
      console.log(formatMessage('🐛', message, colors.cyan));
      if (data) {
        console.log(`   📊 Data:`, data);
      }
    }
  },

  info: (message: string, data?: DebugData): void => {
    console.log(formatMessage('ℹ️', message, colors.blue));
    if (data) {
      console.log(`   📊 Data:`, data);
    }
  },

  success: (message: string, data?: DebugData): void => {
    console.log(formatMessage('✅', message, colors.green));
    if (data) {
      console.log(`   📊 Data:`, data);
    }
  },

  error: (message: string, error?: Error, data?: DebugData): void => {
    console.error(formatMessage('❌', message, colors.red));
    if (error) {
      console.error(`   🔥 Error:`, error);
    }
    if (data) {
      console.error(`   📊 Data:`, data);
    }
  },

  warn: (message: string, data?: DebugData): void => {
    console.warn(formatMessage('⚠️', message, colors.yellow));
    if (data) {
      console.warn(`   📊 Data:`, data);
    }
  },

  api: {
    request: (method: string, url: string, data?: DebugData): void => {
      debug.info(`🌐 ${method} ${url}`, data);
    },

    response: (url: string, status: number, data?: DebugData): void => {
      if (status >= 200 && status < 300) {
        debug.success(`🌐 Response ${status} for ${url}`, data);
      } else {
        debug.error(`🌐 Response ${status} for ${url}`, undefined, data);
      }
    },
  },

  component: {
    mount: (componentName: string, props?: DebugData): void => {
      debug.log(`🎨 Mounting ${componentName}`, props);
    },

    update: (componentName: string, props?: DebugData): void => {
      debug.log(`🎨 Updating ${componentName}`, props);
    },

    unmount: (componentName: string): void => {
      debug.log(`🎨 Unmounting ${componentName}`);
    },
  },

  store: {
    action: (actionName: string, payload?: DebugData): void => {
      debug.log(`🏪 Store action: ${actionName}`, payload);
    },

    state: (stateName: string, state: DebugData): void => {
      debug.log(`🏪 Store state: ${stateName}`, state);
    },
  },

  animation: {
    start: (animationName: string, element?: string): void => {
      debug.log(`🎬 Starting animation: ${animationName}`, { element });
    },

    end: (animationName: string, element?: string): void => {
      debug.log(`🎬 Ended animation: ${animationName}`, { element });
    },
  },

  performance: {
    start: (operation: string): number => {
      const startTime = performance.now();
      debug.log(`⏱️ Starting: ${operation}`, { startTime });
      return startTime;
    },

    end: (operation: string, startTime: number): void => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      debug.log(`⏱️ Completed: ${operation}`, { duration: `${duration.toFixed(2)}ms` });
    },
  },
};

// Timer decorator for functions
export function debugTimer<T extends (...args: any[]) => any>(
  fn: T,
  name?: string
): T {
  return ((...args: any[]) => {
    const operationName = name || fn.name || 'anonymous';
    const startTime = debug.performance.start(operationName);
    
    try {
      const result = fn(...args);
      debug.performance.end(operationName, startTime);
      return result;
    } catch (error) {
      debug.performance.end(operationName, startTime);
      debug.error(`Function ${operationName} failed`, error as Error);
      throw error;
    }
  }) as T;
}

// Hook for React components
export function useDebugLog(componentName: string) {
  return {
    log: (message: string, data?: DebugData) => debug.log(`[${componentName}] ${message}`, data),
    info: (message: string, data?: DebugData) => debug.info(`[${componentName}] ${message}`, data),
    error: (message: string, error?: Error, data?: DebugData) => debug.error(`[${componentName}] ${message}`, error, data),
    success: (message: string, data?: DebugData) => debug.success(`[${componentName}] ${message}`, data),
  };
}

export default debug;
