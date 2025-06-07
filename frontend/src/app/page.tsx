'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import ApiKeyConfig from './components/ApiKeyConfig';
import ProcessingStatus from './components/ProcessingStatus';
import OutputGallery from './components/OutputGallery';

interface CloneStatus {
  taskId: string | null;
  status: 'idle' | 'loading' | 'success' | 'error';
  result: any;
  error: string | null;
}

export default function Home() {
  const [url, setUrl] = useState<string>('');
  const [cloneStatus, setCloneStatus] = useState<CloneStatus>({
    taskId: null,
    status: 'idle',
    result: null,
    error: null
  });
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showLiveGeneration, setShowLiveGeneration] = useState<boolean>(true);
  const [showApiConfig, setShowApiConfig] = useState<boolean>(false);
  const [useMultiAgent, setUseMultiAgent] = useState<boolean>(true);
  const [apiKeyStatus, setApiKeyStatus] = useState<{
    anthropic: boolean;
    openai: boolean;
    google: boolean;
    aws: boolean;
  }>({
    anthropic: false,
    openai: false,
    google: false,
    aws: false
  });

  // Check API key status on load
  useEffect(() => {
    fetchApiKeyStatus();
  }, []);
  
  const fetchApiKeyStatus = async () => {
    try {
      const response = await fetch('http://localhost:8002/api/config/keys/status');
      if (response.ok) {
        const status = await response.json();
        setApiKeyStatus(status);
      }
    } catch (error) {
      console.error('Failed to fetch API key status:', error);
    }
  };

  // Poll for task status if we have a taskId and are in loading state
  // Only for legacy mode (multi-agent uses WebSockets)
  useEffect(() => {
    if (!useMultiAgent && cloneStatus.taskId && cloneStatus.status === 'loading') {
      const intervalId = setInterval(checkTaskStatus, 2000);
      return () => clearInterval(intervalId);
    }
  }, [cloneStatus.taskId, cloneStatus.status, useMultiAgent]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url) return;
    
    try {
      setCloneStatus({ ...cloneStatus, status: 'loading', error: null });
      
      // Different API endpoints for legacy vs. multi-agent
      const apiEndpoint = useMultiAgent 
        ? 'http://localhost:8002/multi-agent/clone'
        : 'http://localhost:8002/clone';
      
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to start cloning process');
      }
      
      const data = await response.json();
      setCloneStatus({
        taskId: data.task_id,
        status: data.status === 'complete' ? 'success' : 'loading',
        result: null,
        error: null
      });
      
      // If task is already complete and not using multi-agent, get the result
      if (!useMultiAgent && data.status === 'complete') {
        await getTaskResult(data.task_id);
      }
    } catch (error) {
      console.error('Error submitting URL:', error);
      setCloneStatus({
        ...cloneStatus,
        status: 'error',
        error: error instanceof Error ? error.message : 'An unknown error occurred'
      });
    }
  };
  
  const checkTaskStatus = async () => {
    try {
      if (!cloneStatus.taskId) return;
      
      const statusEndpoint = useMultiAgent
        ? `http://localhost:8002/multi-agent/status/${cloneStatus.taskId}`
        : `http://localhost:8002/status/${cloneStatus.taskId}`;
      
      const response = await fetch(statusEndpoint);
      if (!response.ok) {
        throw new Error('Failed to check task status');
      }
      
      const data = await response.json();
      
      if (data.status === 'complete' || data.status === 'completed') {
        await getTaskResult(cloneStatus.taskId);
      } else if (data.status === 'error' || data.status === 'failed') {
        setCloneStatus({
          ...cloneStatus,
          status: 'error',
          error: data.error || 'Website cloning failed'
        });
      }
    } catch (error) {
      console.error('Error checking task status:', error);
    }
  };
  
  const getTaskResult = async (taskId: string) => {
    try {
      const resultEndpoint = useMultiAgent
        ? `http://localhost:8002/multi-agent/result/${taskId}`
        : `http://localhost:8002/result/${taskId}`;
      
      const response = await fetch(resultEndpoint);
      if (!response.ok) {
        throw new Error('Failed to get task result');
      }
      
      const result = await response.json();
      setCloneStatus({
        ...cloneStatus,
        status: 'success',
        result
      });
      
      // Set the preview URL
      const previewEndpoint = useMultiAgent
        ? `http://localhost:8002/multi-agent/preview/${taskId}`
        : `http://localhost:8002/preview/${taskId}`;
      
      setPreviewUrl(previewEndpoint);
    } catch (error) {
      console.error('Error getting task result:', error);
      setCloneStatus({
        ...cloneStatus,
        status: 'error',
        error: error instanceof Error ? error.message : 'An unknown error occurred'
      });
    }
  };

  const toggleApiConfig = () => {
    setShowApiConfig(!showApiConfig);
  };

  const handleApiConfigClose = () => {
    setShowApiConfig(false);
    fetchApiKeyStatus();  // Refresh API key status after closing config
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Website Clone Generator</h1>
          <button
            onClick={toggleApiConfig}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            API Settings
          </button>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* API Key Status Indicator */}
          <div className="mb-4 p-4 bg-gray-50 rounded-md border border-gray-200">
            <div className="flex flex-wrap gap-3">
              <span className="text-sm font-medium text-gray-500">API Keys:</span>
              <span className={`px-2 py-1 inline-flex text-xs leading-4 font-semibold rounded-full ${apiKeyStatus.openai ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                OpenAI: {apiKeyStatus.openai ? 'Configured' : 'Not Configured'}
              </span>
              <span className={`px-2 py-1 inline-flex text-xs leading-4 font-semibold rounded-full ${apiKeyStatus.anthropic ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                Claude: {apiKeyStatus.anthropic ? 'Configured' : 'Not Configured'}
              </span>
              <span className={`px-2 py-1 inline-flex text-xs leading-4 font-semibold rounded-full ${apiKeyStatus.aws ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                AWS Bedrock: {apiKeyStatus.aws ? 'Configured' : 'Optional'}
              </span>
            </div>
          </div>
          
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              {/* Approach Selection */}
              <div className="mb-6">
                <label className="text-sm font-medium text-gray-700 mb-2 block">Generation Approach</label>
                <div className="flex space-x-4">
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      className="form-radio h-4 w-4 text-indigo-600"
                      checked={!useMultiAgent}
                      onChange={() => setUseMultiAgent(false)}
                      disabled={cloneStatus.status === 'loading'}
                    />
                    <span className="ml-2 text-gray-700">Legacy (Single LLM)</span>
                  </label>
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      className="form-radio h-4 w-4 text-indigo-600"
                      checked={useMultiAgent}
                      onChange={() => setUseMultiAgent(true)}
                      disabled={cloneStatus.status === 'loading'}
                    />
                    <span className="ml-2 text-gray-700">Multi-Agent System</span>
                  </label>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  {useMultiAgent 
                    ? "Using multi-agent system with specialized agents for each step of the process" 
                    : "Using single LLM to generate the entire website at once"}
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="url" className="block text-sm font-medium text-gray-700">
                    Website URL
                  </label>
                  <div className="mt-1 flex rounded-md shadow-sm">
                    <input
                      type="url"
                      name="url"
                      id="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      className="focus:ring-indigo-500 focus:border-indigo-500 flex-1 block w-full rounded-md sm:text-sm border-gray-300 p-2 border"
                      placeholder="https://example.com"
                      required
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={cloneStatus.status === 'loading'}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
                >
                  {cloneStatus.status === 'loading' ? 'Cloning...' : 'Clone Website'}
                </button>
              </form>
              
              {/* Display processing status for multi-agent approach */}
              {useMultiAgent && cloneStatus.status === 'loading' && cloneStatus.taskId && (
                <div className="mt-6">
                  <ProcessingStatus taskId={cloneStatus.taskId} />
                </div>
              )}
              
              {/* Display spinner for legacy approach */}
              {!useMultiAgent && cloneStatus.status === 'loading' && (
                <div className="mt-6 text-center">
                  <div className="loader animate-spin mx-auto h-10 w-10 border-4 border-indigo-600 rounded-full border-t-transparent"></div>
                  <p className="mt-2 text-gray-600">Cloning website... This may take a few minutes.</p>
                </div>
              )}
              
              {cloneStatus.status === 'error' && (
                <div className="mt-6 p-4 bg-red-50 rounded-md">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">Error</h3>
                      <p className="text-sm text-red-700 mt-1">{cloneStatus.error}</p>
                    </div>
                  </div>
                </div>
              )}
              
              {cloneStatus.status === 'success' && (
                <>
                  {/* Preview Mode Toggle */}
                  <div className="mt-6 flex items-center justify-between">
                    <h2 className="text-lg font-medium text-gray-900">Cloned Website</h2>
                    <div className="flex items-center">
                      <span className="text-sm text-gray-500 mr-3">Preview Mode:</span>
                      <button
                        onClick={() => setShowLiveGeneration(!showLiveGeneration)}
                        className={`relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                          showLiveGeneration ? 'bg-indigo-600' : 'bg-gray-200'
                        }`}
                      >
                        <span className="sr-only">Toggle preview mode</span>
                        <span
                          className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200 ${
                            showLiveGeneration ? 'translate-x-5' : 'translate-x-0'
                          }`}
                        />
                      </button>
                      <span className="ml-3 text-sm text-gray-500">
                        {showLiveGeneration ? 'Live Generation Simulation' : 'Instant Preview'}
                      </span>
                    </div>
                  </div>
                  
                  {/* Display source URL */}
                  <div className="mt-2 text-sm text-gray-500">
                    Source URL: <span className="font-medium">{url}</span>
                  </div>
                  
                  {/* Output Gallery */}
                  <OutputGallery 
                    taskId={cloneStatus.taskId} 
                    showLiveGeneration={showLiveGeneration}
                  />
                  
                  {/* Display generation approach used */}
                  <div className="mt-4 text-sm text-gray-500">
                    Generated using: {useMultiAgent ? 'Multi-Agent System' : 'Legacy Single LLM Approach'}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </main>
      
      {showApiConfig && <ApiKeyConfig onClose={handleApiConfigClose} />}
    </div>
  );
}
