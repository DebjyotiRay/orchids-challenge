'use client';

import { useState, useEffect } from 'react';
import GenerationPreview from './GenerationPreview';

interface OutputGalleryProps {
  taskId: string | null;
  showLiveGeneration: boolean;
}

export default function OutputGallery({ taskId, showLiveGeneration }: OutputGalleryProps) {
  const [selectedOutput, setSelectedOutput] = useState<string>('direct');
  const [availableOutputs, setAvailableOutputs] = useState<string[]>([]);

  // In a real implementation, this would check which outputs are actually available
  // Here we're simulating that all outputs are available
  useEffect(() => {
    // Simulating an API call to check available outputs
    const checkAvailableOutputs = async () => {
      // In a real implementation, we would fetch this data from the backend
      setAvailableOutputs(['direct', 'enhanced', 'project', 'project2']);
    };

    checkAvailableOutputs();
  }, [taskId]);

  return (
    <div className="mt-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">Generated Outputs</h2>
      
      {/* Output Type Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {availableOutputs.map((outputType) => {
            const isSelected = selectedOutput === outputType;
            const labels = {
              'direct': 'Basic HTML/CSS',
              'enhanced': 'Enhanced Version',
              'project': 'React Project',
              'project2': 'Interactive App'
            };
            
            return (
              <button
                key={outputType}
                onClick={() => setSelectedOutput(outputType)}
                className={`
                  whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                  ${isSelected 
                    ? 'border-indigo-500 text-indigo-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                `}
              >
                {labels[outputType as keyof typeof labels]}
              </button>
            );
          })}
        </nav>
      </div>
      
      {/* Live Mode Toggle */}
      <div className="flex items-center mt-4 mb-2">
        <span className="text-sm text-gray-500 mr-3">Preview Mode:</span>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${showLiveGeneration 
          ? 'bg-green-100 text-green-800' 
          : 'bg-blue-100 text-blue-800'}`}
        >
          {showLiveGeneration ? 'Live Generation Simulation' : 'Instant Preview'}
        </span>
      </div>
      
      {/* Selected Output Preview */}
      <GenerationPreview 
        taskId={taskId} 
        generationType={selectedOutput as 'direct' | 'enhanced' | 'project' | 'project2'} 
        showLive={showLiveGeneration}
      />
      
      {/* Info Section */}
      <div className="mt-4 p-4 bg-gray-50 rounded-md text-sm text-gray-600">
        <p className="font-medium mb-2">About this output:</p>
        {selectedOutput === 'direct' && (
          <p>Basic HTML/CSS version directly generated from the website structure.</p>
        )}
        {selectedOutput === 'enhanced' && (
          <p>Enhanced HTML/CSS with improved styling and responsive design.</p>
        )}
        {selectedOutput === 'project' && (
          <p>Full React project with components matching the original website structure.</p>
        )}
        {selectedOutput === 'project2' && (
          <p>Interactive application with additional features beyond the original website.</p>
        )}
      </div>
    </div>
  );
}
