import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  color?: 'blue' | 'gray' | 'white';
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className = '',
  color = 'blue',
  text
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const colorClasses = {
    blue: 'border-blue-600',
    gray: 'border-gray-600',
    white: 'border-white',
  };

  return (
    <div className={`flex flex-col justify-center items-center ${className}`}>
      <div className={`spinner ${sizeClasses[size]} ${colorClasses[color]}`}></div>
      {text && (
        <div className={`text-sm mt-2 ${color === 'white' ? 'text-white' : 'text-gray-600'}`}>
          {text}
        </div>
      )}
    </div>
  );
};

// Skeleton components for loading states
export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
    <div className="animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
      <div className="space-y-2">
        <div className="h-3 bg-gray-200 rounded w-full"></div>
        <div className="h-3 bg-gray-200 rounded w-5/6"></div>
        <div className="h-3 bg-gray-200 rounded w-4/6"></div>
      </div>
    </div>
  </div>
);

export const SkeletonTable: React.FC<{ rows?: number; cols?: number }> = ({ rows = 5, cols = 4 }) => (
  <div className="animate-pulse">
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr>
              {Array.from({ length: cols }).map((_, i) => (
                <th key={i} className="px-3 py-2 border border-gray-200">
                  <div className="h-3 bg-gray-200 rounded w-16"></div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rows }).map((_, i) => (
              <tr key={i}>
                {Array.from({ length: cols }).map((_, j) => (
                  <td key={j} className="px-3 py-2 border border-gray-200">
                    <div className="h-3 bg-gray-200 rounded w-12"></div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

export const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({ lines = 3, className = '' }) => (
  <div className={`animate-pulse ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <div key={i} className="h-3 bg-gray-200 rounded mb-2" style={{ width: `${Math.random() * 40 + 60}%` }}></div>
    ))}
  </div>
);
