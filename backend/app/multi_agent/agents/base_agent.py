import os
import asyncio
import concurrent.futures
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent system.
    
    This abstract class defines the common interface and functionality
    that all specialized agents should implement.
    """
    
    def __init__(self, **kwargs):
        """Initialize the base agent with common configuration."""
        # Debug mode for verbose logging
        self.debug = kwargs.get("debug", False)
        
        # Timeout for operations in seconds
        self.timeout = kwargs.get("timeout", 60)
        
        # Maximum retries for operations
        self.max_retries = kwargs.get("max_retries", 3)
        
        # Agent identifier
        self.id = kwargs.get("id", self.__class__.__name__)
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and return the output.
        
        This method must be implemented by all subclasses.
        
        Args:
            input_data: Dictionary containing input data for the agent
            
        Returns:
            Dictionary containing the output data from the agent
        """
        pass
    
    def process_sync(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for the async process method.
        
        This method uses a thread pool executor to run the async process method
        in a separate thread to avoid event loop conflicts.
        
        Args:
            input_data: Dictionary containing input data for the agent
            
        Returns:
            Dictionary containing the output data from the agent
        """
        # Create a ThreadPoolExecutor to run the async function in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as pool:
            # Define a function that creates a new event loop and runs the async function
            def run_async_in_thread():
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Run the async process method
                    return loop.run_until_complete(self.process(input_data))
                finally:
                    # Close the event loop
                    loop.close()
            
            # Submit the function to the thread pool and wait for the result
            future = pool.submit(run_async_in_thread)
            # Return the result or raise any exception
            return future.result()
