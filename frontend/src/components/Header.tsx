import React, { useState } from 'react';
import { BookOpen, Github, Settings, FolderOpen } from 'lucide-react';
import { ExamplesModal } from './ExamplesModal';

export const Header: React.FC = () => {
  const [isExamplesModalOpen, setIsExamplesModalOpen] = useState(false);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-primary-600 rounded-lg">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                LR(1) Parser Visualizer
              </h1>
              <p className="text-sm text-gray-600">
                Interactive step-by-step LR(1) parsing
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsExamplesModalOpen(true)}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors"
            >
              <FolderOpen className="w-4 h-4" />
              <span className="text-sm">Load Example Grammar</span>
            </button>

            <button
              className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
              onClick={() => window.open('https://github.com', '_blank')}
            >
              <Github className="w-4 h-4" />
              <span className="text-sm">GitHub</span>
            </button>

            <button className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors">
              <Settings className="w-4 h-4" />
              <span className="text-sm">Settings</span>
            </button>
          </div>
        </div>
      </div>

      {/* Examples Modal */}
      <ExamplesModal
        isOpen={isExamplesModalOpen}
        onClose={() => setIsExamplesModalOpen(false)}
      />
    </header>
  );
};
