"use client";

import React, { useState, useEffect } from "react";

interface ApiKeyConfigProps {
  onClose: () => void;
}

export default function ApiKeyConfig({ onClose }: ApiKeyConfigProps) {
  const [anthropicKey, setAnthropicKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [awsAccessKey, setAwsAccessKey] = useState("");
  const [awsSecretKey, setAwsSecretKey] = useState("");
  const [awsRegion, setAwsRegion] = useState("us-east-1");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [keyStatus, setKeyStatus] = useState({
    anthropic: false,
    openai: false,
    google: false,
    aws: false,
  });

  // Fetch current key status on mount
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch("http://localhost:8002/api/config/keys/status");
        const data = await response.json();
        setKeyStatus(data);
      } catch (err) {
        console.error("Failed to fetch API key status:", err);
      }
    };

    fetchStatus();
  }, []);

  const handleSaveAnthropicKey = async () => {
    if (!anthropicKey.trim()) return;
    
    setLoading(true);
    setError("");
    setSuccess("");
    
    try {
      const response = await fetch("http://localhost:8002/api/config/keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          provider: "anthropic",
          api_key: anthropicKey,
        }),
      });
      
      if (response.ok) {
        setSuccess("Anthropic API key saved successfully");
        setKeyStatus(prev => ({ ...prev, anthropic: true }));
        setAnthropicKey(""); // Clear the input for security
      } else {
        const error = await response.json();
        setError(error.detail || "Failed to save API key");
      }
    } catch (err) {
      setError("An error occurred while saving the API key");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveOpenAIKey = async () => {
    if (!openaiKey.trim()) return;
    
    setLoading(true);
    setError("");
    setSuccess("");
    
    try {
      const response = await fetch("http://localhost:8002/api/config/keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          provider: "openai",
          api_key: openaiKey,
        }),
      });
      
      if (response.ok) {
        setSuccess("OpenAI API key saved successfully");
        setKeyStatus(prev => ({ ...prev, openai: true }));
        setOpenaiKey(""); // Clear the input for security
      } else {
        const error = await response.json();
        setError(error.detail || "Failed to save API key");
      }
    } catch (err) {
      setError("An error occurred while saving the API key");
    } finally {
      setLoading(false);
    }
  };
  
  const handleSaveAwsCredentials = async () => {
    if (!awsAccessKey.trim() || !awsSecretKey.trim()) return;
    
    setLoading(true);
    setError("");
    setSuccess("");
    
    try {
      const response = await fetch("http://localhost:8002/api/config/keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          provider: "aws",
          api_key: awsAccessKey,
          aws_secret_key: awsSecretKey,
          aws_region: awsRegion
        }),
      });
      
      if (response.ok) {
        setSuccess("AWS credentials saved successfully");
        setKeyStatus(prev => ({ ...prev, aws: true }));
        setAwsAccessKey(""); // Clear the input for security
        setAwsSecretKey(""); // Clear the input for security
      } else {
        const error = await response.json();
        setError(error.detail || "Failed to save AWS credentials");
      }
    } catch (err) {
      setError("An error occurred while saving AWS credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">API Key Configuration</h2>
          <button 
            className="text-gray-500 hover:text-gray-800"
            onClick={onClose}
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path 
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
        
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
            <p>{error}</p>
          </div>
        )}
        
        {success && (
          <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4">
            <p>{success}</p>
          </div>
        )}
        
        <div className="mb-6">
          <p className="text-sm text-gray-600 mb-2">
            API keys are required for the LLM integration. Your keys are stored locally in memory and are never persisted.
          </p>
        </div>
        
        {/* Anthropic API Key */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <label htmlFor="anthropic-key" className="block text-sm font-medium text-gray-700">
              Anthropic API Key (Claude)
            </label>
            {keyStatus.anthropic && (
              <span className="inline-flex items-center text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800">
                <svg className="mr-1.5 h-2 w-2 text-green-400" fill="currentColor" viewBox="0 0 8 8">
                  <circle cx="4" cy="4" r="3" />
                </svg>
                Configured
              </span>
            )}
          </div>
          <div className="mt-1 flex rounded-md shadow-sm">
            <input
              type="password"
              name="anthropic-key"
              id="anthropic-key"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-2 border"
              placeholder="sk-ant-..."
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
            />
            <button
              type="button"
              onClick={handleSaveAnthropicKey}
              disabled={loading || !anthropicKey}
              className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-300"
            >
              Save
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            Get your Claude API key from <a href="https://console.anthropic.com/keys" className="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">Anthropic Console</a>
          </p>
        </div>
        
        {/* OpenAI API Key */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <label htmlFor="openai-key" className="block text-sm font-medium text-gray-700">
              OpenAI API Key
            </label>
            {keyStatus.openai && (
              <span className="inline-flex items-center text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800">
                <svg className="mr-1.5 h-2 w-2 text-green-400" fill="currentColor" viewBox="0 0 8 8">
                  <circle cx="4" cy="4" r="3" />
                </svg>
                Configured
              </span>
            )}
          </div>
          <div className="mt-1 flex rounded-md shadow-sm">
            <input
              type="password"
              name="openai-key"
              id="openai-key"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-2 border"
              placeholder="sk-..."
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
            />
            <button
              type="button"
              onClick={handleSaveOpenAIKey}
              disabled={loading || !openaiKey}
              className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-300"
            >
              Save
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            Get your OpenAI API key from <a href="https://platform.openai.com/api-keys" className="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">OpenAI Dashboard</a>
          </p>
        </div>
        
        {/* AWS Bedrock Credentials */}
        <div className="mb-4 border-t pt-4 mt-6">
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-gray-700">
              AWS Credentials (for Bedrock)
            </label>
            {keyStatus.aws && (
              <span className="inline-flex items-center text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800">
                <svg className="mr-1.5 h-2 w-2 text-green-400" fill="currentColor" viewBox="0 0 8 8">
                  <circle cx="4" cy="4" r="3" />
                </svg>
                Configured
              </span>
            )}
          </div>
          
          {/* AWS Access Key */}
          <div className="mt-3">
            <label htmlFor="aws-access-key" className="block text-xs font-medium text-gray-700 mb-1">
              Access Key ID
            </label>
            <input
              type="password"
              name="aws-access-key"
              id="aws-access-key"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-2 border"
              placeholder="AKIA..."
              value={awsAccessKey}
              onChange={(e) => setAwsAccessKey(e.target.value)}
            />
          </div>
          
          {/* AWS Secret Key */}
          <div className="mt-3">
            <label htmlFor="aws-secret-key" className="block text-xs font-medium text-gray-700 mb-1">
              Secret Access Key
            </label>
            <input
              type="password"
              name="aws-secret-key"
              id="aws-secret-key"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-2 border"
              placeholder="Enter your AWS Secret Access Key"
              value={awsSecretKey}
              onChange={(e) => setAwsSecretKey(e.target.value)}
            />
          </div>
          
          {/* AWS Region */}
          <div className="mt-3">
            <label htmlFor="aws-region" className="block text-xs font-medium text-gray-700 mb-1">
              Region
            </label>
            <select
              id="aws-region"
              name="aws-region"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-2 border"
              value={awsRegion}
              onChange={(e) => setAwsRegion(e.target.value)}
            >
              <option value="us-east-1">US East (N. Virginia) - us-east-1</option>
              <option value="us-east-2">US East (Ohio) - us-east-2</option>
              <option value="us-west-1">US West (N. California) - us-west-1</option>
              <option value="us-west-2">US West (Oregon) - us-west-2</option>
              <option value="eu-west-1">EU (Ireland) - eu-west-1</option>
              <option value="eu-central-1">EU (Frankfurt) - eu-central-1</option>
              <option value="ap-northeast-1">Asia Pacific (Tokyo) - ap-northeast-1</option>
              <option value="ap-southeast-1">Asia Pacific (Singapore) - ap-southeast-1</option>
              <option value="ap-southeast-2">Asia Pacific (Sydney) - ap-southeast-2</option>
            </select>
          </div>
          
          <div className="mt-3">
            <button
              type="button"
              onClick={handleSaveAwsCredentials}
              disabled={loading || !awsAccessKey || !awsSecretKey}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-300"
            >
              Save AWS Credentials
            </button>
          </div>
          
          <p className="mt-2 text-xs text-gray-500">
            AWS credentials are used to access Bedrock models. These credentials should have permission to use Bedrock services.
          </p>
        </div>
        
        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
