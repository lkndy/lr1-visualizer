import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Bug } from 'lucide-react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null,
        };
    }

    static getDerivedStateFromError(error: Error): State {
        return {
            hasError: true,
            error,
            errorInfo: null,
        };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        this.setState({
            error,
            errorInfo,
        });

        // Call the onError callback if provided
        if (this.props.onError) {
            this.props.onError(error, errorInfo);
        }

        // Log error to console in development
        if (process.env.NODE_ENV === 'development') {
            console.error('ErrorBoundary caught an error:', error, errorInfo);
        }
    }

    handleReset = () => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null,
        });
    };

    handleReload = () => {
        window.location.reload();
    };

    render() {
        if (this.state.hasError) {
            // Custom fallback UI
            if (this.props.fallback) {
                return this.props.fallback;
            }

            // Default error UI
            return (
                <div className="min-h-screen flex items-center justify-center bg-gray-50">
                    <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
                        <div className="flex items-center space-x-3 mb-4">
                            <AlertTriangle className="w-8 h-8 text-red-500" />
                            <h1 className="text-xl font-semibold text-gray-900">
                                Something went wrong
                            </h1>
                        </div>

                        <p className="text-gray-600 mb-4">
                            The application encountered an unexpected error. This might be due to a bug in the code or an issue with the data.
                        </p>

                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <details className="mb-4">
                                <summary className="cursor-pointer text-sm font-medium text-gray-700 mb-2">
                                    Error Details (Development)
                                </summary>
                                <div className="bg-gray-100 p-3 rounded text-xs font-mono text-gray-800 overflow-auto max-h-32">
                                    <div className="mb-2">
                                        <strong>Error:</strong> {this.state.error.message}
                                    </div>
                                    <div className="mb-2">
                                        <strong>Stack:</strong>
                                        <pre className="whitespace-pre-wrap mt-1">
                                            {this.state.error.stack}
                                        </pre>
                                    </div>
                                    {this.state.errorInfo && (
                                        <div>
                                            <strong>Component Stack:</strong>
                                            <pre className="whitespace-pre-wrap mt-1">
                                                {this.state.errorInfo.componentStack}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            </details>
                        )}

                        <div className="flex space-x-3">
                            <button
                                onClick={this.handleReset}
                                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                            >
                                <RefreshCw className="w-4 h-4" />
                                <span>Try Again</span>
                            </button>

                            <button
                                onClick={this.handleReload}
                                className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
                            >
                                <RefreshCw className="w-4 h-4" />
                                <span>Reload Page</span>
                            </button>
                        </div>

                        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                            <div className="flex items-start space-x-2">
                                <Bug className="w-4 h-4 text-yellow-600 mt-0.5" />
                                <div className="text-sm text-yellow-800">
                                    <strong>Report Issue:</strong> If this error persists, please report it with the error details above.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

// Higher-order component for easier usage
export const withErrorBoundary = <P extends object>(
    Component: React.ComponentType<P>,
    errorBoundaryProps?: Omit<Props, 'children'>
) => {
    const WrappedComponent = (props: P) => (
        <ErrorBoundary {...errorBoundaryProps}>
            <Component {...props} />
        </ErrorBoundary>
    );

    WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
    return WrappedComponent;
};
