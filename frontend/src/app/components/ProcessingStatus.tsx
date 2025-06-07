'use client';

import { useState, useEffect } from 'react';

interface Agent {
  name: string;
  description: string;
  icon: string;
}

interface AgentStep {
  agent_id: string;
  agent_name: string;
  status: 'waiting' | 'running' | 'completed' | 'failed';
  start_time?: number;
  end_time?: number;
  duration?: number;
  error?: string;
}

interface ProcessingStatusProps {
  taskId: string;
}

// Agent information with descriptions and icons
const agentInfo: Record<string, Agent> = {
  'scraper_1': {
    name: 'Website Scraper',
    description: 'Scrapes the target website to capture its content and structure',
    icon: '🔍'
  },
  'semantic_parser_2': {
    name: 'Semantic Parser',
    description: 'Analyzes the content to understand its semantic structure',
    icon: '📊'
  },
  'style_transfer_3': {
    name: 'Style Extractor',
    description: 'Extracts and interprets the style information from the website',
    icon: '🎨'
  },
  'layout_generator_4': {
    name: 'Layout Generator',
    description: 'Creates a responsive layout based on the original website',
    icon: '📐'
  },
  'component_synthesizer_5': {
    name: 'Component Synthesizer',
    description: 'Generates the actual HTML and CSS components',
    icon: '⚙️'
  },
  'validation_6': {
    name: 'Code Validator',
    description: 'Validates and ensures the generated code is correct',
    icon: '✅'
  }
};

// Default workflow steps
const defaultWorkflow: AgentStep[] = [
  { agent_id: 'scraper_1', agent_name: 'Website Scraper', status: 'waiting' },
  { agent_id: 'semantic_parser_2', agent_name: 'Semantic Parser', status: 'waiting' },
  { agent_id: 'style_transfer_3', agent_name: 'Style Extractor', status: 'waiting' },
  { agent_id: 'layout_generator_4', agent_name: 'Layout Generator', status: 'waiting' },
  { agent_id: 'component_synthesizer_5', agent_name: 'Component Synthesizer', status: 'waiting' },
  { agent_id: 'validation_6', agent_name: 'Code Validator', status: 'waiting' }
];

export default function ProcessingStatus({ taskId }: ProcessingStatusProps) {
  const [connected, setConnected] = useState(false);
  const [steps, setSteps] = useState<AgentStep[]>(defaultWorkflow);
  const [currentAgentId, setCurrentAgentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);
  
  useEffect(() => {
    let ws: WebSocket;
    
    // Function to initialize WebSocket connection
    const connectWebSocket = () => {
      ws = new WebSocket(`ws://localhost:8002/multi-agent/ws/${taskId}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        
        // Only try to reconnect if we haven't completed yet
        if (!completed) {
          setTimeout(connectWebSocket, 2000);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnected(false);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message:', data);
          
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
    };
    
    // Connect WebSocket
    connectWebSocket();
    
    // Cleanup WebSocket connection on unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [taskId, completed]);
  
  // Handle WebSocket messages
  const handleWebSocketMessage = (data: any) => {
    switch (data.event) {
      case 'task_started':
        // Reset steps when task starts
        setSteps(defaultWorkflow);
        setError(null);
        break;
        
      case 'agent_started':
        setCurrentAgentId(data.agent_id);
        
        // Update the step status
        setSteps(prevSteps => prevSteps.map(step => 
          step.agent_id === data.agent_id 
            ? { ...step, status: 'running', start_time: data.start_time }
            : step
        ));
        break;
        
      case 'agent_completed':
        // Update the step status
        setSteps(prevSteps => prevSteps.map(step => 
          step.agent_id === data.agent_id 
            ? { 
                ...step, 
                status: 'completed', 
                start_time: data.start_time,
                end_time: data.end_time,
                duration: data.duration
              }
            : step
        ));
        break;
        
      case 'agent_failed':
        // Update the step status
        setSteps(prevSteps => prevSteps.map(step => 
          step.agent_id === data.agent_id 
            ? { ...step, status: 'failed', error: data.error }
            : step
        ));
        
        setError(data.error);
        break;
        
      case 'task_completed':
        setCompleted(true);
        break;
        
      case 'task_failed':
        setCompleted(true);
        setError(data.error);
        break;
        
      case 'workflow_completed':
        setCompleted(true);
        break;
        
      case 'workflow_failed':
        setCompleted(true);
        setError('Workflow failed to complete');
        break;
    }
  };
  
  // Calculate overall progress
  const calculateProgress = () => {
    const completedSteps = steps.filter(step => step.status === 'completed').length;
    const totalSteps = steps.length;
    return Math.round((completedSteps / totalSteps) * 100);
  };
  
  // Get the current agent information
  const getCurrentAgentInfo = () => {
    if (!currentAgentId) return null;
    return agentInfo[currentAgentId];
  };
  
  // Format duration in seconds
  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    return `${seconds.toFixed(1)}s`;
  };
  
  const currentAgent = getCurrentAgentInfo();
  const progress = calculateProgress();

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-4 py-5 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Website Generation Progress</h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">
          {connected ? 'Real-time updates via WebSocket connection' : 'Connecting...'}
        </p>
      </div>
      
      {/* Progress bar */}
      <div className="px-4 sm:px-6">
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className={`h-2.5 rounded-full ${error ? 'bg-red-600' : 'bg-blue-600'}`} 
            style={{width: `${progress}%`}}
          ></div>
        </div>
        <p className="mt-1 text-sm text-gray-500 text-right">{progress}% complete</p>
      </div>
      
      {/* Current agent */}
      {currentAgent && (
        <div className="px-4 py-3 sm:px-6 bg-blue-50 border-t border-b border-blue-100">
          <div className="flex items-center">
            <span className="text-2xl mr-3">{currentAgent.icon}</span>
            <div>
              <h4 className="text-md font-medium text-blue-800">
                Currently Running: {currentAgent.name}
              </h4>
              <p className="text-sm text-blue-600">{currentAgent.description}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Error message */}
      {error && (
        <div className="px-4 py-3 sm:px-6 bg-red-50 border-t border-red-100">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Steps list */}
      <div className="border-t border-gray-200">
        <dl>
          {steps.map((step, index) => {
            // Get the agent info for this step
            const agent = agentInfo[step.agent_id] || {
              name: step.agent_name,
              description: 'Processing step',
              icon: '📋'
            };
            
            return (
              <div key={step.agent_id} className={`${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'} px-4 py-3 sm:grid sm:grid-cols-6 sm:gap-4 sm:px-6`}>
                <dt className="text-sm font-medium text-gray-500 flex items-center">
                  <span className="mr-2">{agent.icon}</span>
                  <span>{agent.name}</span>
                </dt>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                  {agent.description}
                </dd>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0">
                  {formatDuration(step.duration)}
                </dd>
                <dd className="mt-1 text-sm sm:mt-0 sm:col-span-2">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                    ${step.status === 'waiting' ? 'bg-gray-100 text-gray-800' : 
                      step.status === 'running' ? 'bg-blue-100 text-blue-800 animate-pulse' : 
                      step.status === 'completed' ? 'bg-green-100 text-green-800' : 
                      'bg-red-100 text-red-800'}`}>
                    {step.status === 'waiting' ? 'Pending' : 
                     step.status === 'running' ? 'In Progress' : 
                     step.status === 'completed' ? 'Completed' : 'Failed'}
                  </span>
                  
                  {step.status === 'failed' && step.error && (
                    <p className="mt-1 text-xs text-red-600">{step.error}</p>
                  )}
                </dd>
              </div>
            );
          })}
        </dl>
      </div>
    </div>
  );
}
