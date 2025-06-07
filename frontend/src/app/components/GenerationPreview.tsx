'use coient';

import { useState, useEffect } from 'react';
import Image from 'next/image';

interface GenerationPreviewProps {
  taskId: string | null;
  generationType: 'direct' | 'enhanced' | 'project' | 'project2';
  showLive: boolean;
}

const typeLabels = {
  'direct': 'Basic HTML/CSS',
  'enhanced': 'Enhanced Version',
  'project': 'React Project',
  'project2': 'Interactive Application'
};

export default function GenerationPreview({ taskId, generationType, showLive }: GenerationPreviewProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [generationStep, setGenerationStep] = useState<number>(0);
  const [generationText, setGenerationText] = useState<string>('Initializing generation...');
  const [showPreview, setShowPreview] = useState<boolean>(false);

  // Array of fake generation steps to simulate real-time processing
  const generationSteps = [
    'Analyzing website structure...',
    'Extracting semantic information...',
    'Processing layout components...',
    'Generating HTML structure...',
    'Applying styles and design patterns...',
    'Optimizing responsive design...',
    'Finalizing output...',
    'Generation complete!'
  ];

  // Simulate generation process
  useEffect(() => {
    if (!showLive) {
      // If we're not showing live generation, just load the preview
      loadPreview();
      return;
    }

    setIsLoading(true);
    setShowPreview(false);
    
    // Simulate generation steps with timeouts
    const stepInterval = setInterval(() => {
      setGenerationStep(prev => {
        const nextStep = prev + 1;
        if (nextStep < generationSteps.length) {
          setGenerationText(generationSteps[nextStep]);
          return nextStep;
        } else {
          // Generation "finished"
          clearInterval(stepInterval);
          loadPreview();
          return prev;
        }
      });
    }, 800); // Update every 800ms for a realistic feel

    return () => clearInterval(stepInterval);
  }, [showLive, generationType]);

  // Function to load the actual preview
  const loadPreview = async () => {
    // For a real implementation, this would use the actual task ID
    // Here we're just directly loading from the generated directory
    setPreviewUrl(`/generated/${generationType}/index.html`);
    setIsLoading(false);
    setShowPreview(true);
  };

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg mt-6">
      <div className="bg-gray-100 px-4 py-2 border-b border-gray-300 flex justify-between items-center">
        <div className="text-gray-700 font-medium">{typeLabels[generationType]}</div>
        {previewUrl && !isLoading && (
          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
          >
            Open in new tab
          </a>
        )}
      </div>

      {/* Generation process simulation */}
      {isLoading && showLive && (
        <div className="p-6 text-center">
          <div className="loader animate-spin mx-auto h-10 w-10 border-4 border-indigo-600 rounded-full border-t-transparent"></div>
          <p className="mt-3 text-gray-600">{generationText}</p>
          <div className="mt-4 w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className="h-2.5 rounded-full bg-indigo-600" 
              style={{width: `${(generationStep / (generationSteps.length - 1)) * 100}%`}}
            ></div>
          </div>
        </div>
      )}

      {/* Preview of the generated content */}
      {showPreview && previewUrl && (
        <div className="h-96 overflow-auto">
          <iframe src={previewUrl} className="w-full h-full border-0" title="Generated output preview"></iframe>
        </div>
      )}
    </div>
  );
}
