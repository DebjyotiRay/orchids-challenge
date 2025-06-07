import os
import asyncio
import time
import json
import uuid
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from fastapi import WebSocket

from .workflow.agent_factory import AgentFactory
from .workflow.orchestrator import WorkflowOrchestrator
from .workflow.models import (
    WorkflowState, 
    GenerationRequest, 
    GenerationResponse, 
    AgentConfig,
    WorkflowConfig
)


class WebsiteGenerationService:
    """
    Main service for multi-agent website generation.
    
    This class provides the main API for interacting with the multi-agent
    website generation system. It handles initialization of agents and the
    workflow orchestrator, and provides methods for generating websites from URLs.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the website generation service.
        
        Args:
            config: Service configuration parameters
        """
        self.config = config or {}
        self.debug = self.config.get("debug", False)
        self.output_dir = self.config.get("output_dir", "generated")
        self.screenshots_dir = self.config.get("screenshots_dir", "screenshots")
        
        # Create directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Initialize agents and orchestrator
        self.agent_configs = self._create_agent_configs()
        self.agent_instances = None
        self.orchestrator = None
        
        # Store active tasks and connections
        self.active_tasks = {}
        self.websocket_connections = {}
        
        if self.debug:
            print("[Service] Initialized website generation service")
        
    async def initialize(self):
        """
        Initialize agent instances and the workflow orchestrator.
        
        This method should be called before using the service to ensure
        that all components are properly initialized.
        """
        if self.agent_instances is None:
            # Create agent instances
            self.agent_instances = await AgentFactory.create_agents_from_config(self.agent_configs)
            
            if self.debug:
                print(f"[Service] Created {len(self.agent_instances)} agent instances")
                
            # Create workflow orchestrator
            self.orchestrator = WorkflowOrchestrator(
                agents=self.agent_instances,
                debug=self.debug,
                output_dir=self.output_dir,
                status_callback=self._handle_agent_status_update  # Add callback for status updates
            )
            
            if self.debug:
                print("[Service] Created workflow orchestrator")
    
    def _create_agent_configs(self) -> List[AgentConfig]:
        """
        Create agent configurations using the factory.
        
        Returns:
            List of agent configurations
        """
        # Extract relevant configuration for agent initialization
        agent_kwargs = {
            "output_dir": self.output_dir,
            "screenshots_dir": self.screenshots_dir,
            "firecrawl_api_key": self.config.get("firecrawl_api_key", os.getenv("FIRECRAWL_API_KEY", "")),
            "openai_api_key": self.config.get("openai_api_key", os.getenv("OPENAI_API_KEY", ""))
        }
        
        # Create default agent configurations
        return AgentFactory.create_default_workflow_agents(
            debug=self.debug,
            **agent_kwargs
        )
    
    async def clone_website(self, url: str) -> str:
        """
        Start a new website cloning task.
        
        Args:
            url: URL of the website to clone
            
        Returns:
            The task ID
        """
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Store the task
        self.active_tasks[task_id] = {
            "url": url,
            "status": "pending",
            "created_at": time.time(),
            "result": None
        }
        
        # Start the generation task in the background
        asyncio.create_task(self._run_generation_task(task_id, url))
        
        return task_id
    
    async def _run_generation_task(self, task_id: str, url: str):
        """
        Run the website generation task.
        
        Args:
            task_id: The task ID
            url: URL of the website to clone
        """
        try:
            # Update task status
            self.active_tasks[task_id]["status"] = "running"
            
            # Send status update to connected clients
            await self._notify_clients(task_id, {
                "event": "task_started",
                "task_id": task_id,
                "url": url
            })
            
            # Generate the website
            result = await self.generate_website_from_url(url)
            
            # Update task with result
            self.active_tasks[task_id]["status"] = "completed" if result.status == "success" else "failed"
            self.active_tasks[task_id]["result"] = result.dict()
            
            # Send status update to connected clients
            await self._notify_clients(task_id, {
                "event": "task_completed" if result.status == "success" else "task_failed",
                "task_id": task_id,
                "result": result.dict()
            })
            
        except Exception as e:
            # Update task status
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["error"] = str(e)
            
            # Send status update to connected clients
            await self._notify_clients(task_id, {
                "event": "task_failed",
                "task_id": task_id,
                "error": str(e)
            })
            
            if self.debug:
                print(f"[Service] Error generating website: {str(e)}")
    
    async def _handle_agent_status_update(self, state: WorkflowState, event: str, agent_id: Optional[str] = None):
        """
        Handle agent status updates from the orchestrator.
        
        Args:
            state: Current workflow state
            event: Event type
            agent_id: ID of the agent that triggered the event
        """
        # Extract task ID from output path
        output_path = state.get("output_path", "")
        if not output_path:
            return
            
        task_id = os.path.basename(output_path)
        
        # Prepare the message based on the event
        message = {
            "event": event,
            "task_id": task_id
        }
        
        if event == "agent_started" and agent_id:
            agent_data = state["agents"].get(agent_id, {})
            agent_name = agent_data.get("name", agent_id)
            
            message.update({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "start_time": agent_data.get("start_time")
            })
            
        elif event == "agent_completed" and agent_id:
            agent_data = state["agents"].get(agent_id, {})
            agent_name = agent_data.get("name", agent_id)
            
            message.update({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "start_time": agent_data.get("start_time"),
                "end_time": agent_data.get("end_time"),
                "duration": agent_data.get("end_time", 0) - agent_data.get("start_time", 0)
            })
            
        elif event == "agent_failed" and agent_id:
            agent_data = state["agents"].get(agent_id, {})
            agent_name = agent_data.get("name", agent_id)
            
            message.update({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "error": agent_data.get("error", "Unknown error")
            })
            
        # Send the message to connected clients
        await self._notify_clients(task_id, message)
    
    async def register_websocket(self, task_id: str, websocket: WebSocket):
        """
        Register a WebSocket connection for a task.
        
        Args:
            task_id: The task ID
            websocket: WebSocket connection
        """
        if task_id not in self.websocket_connections:
            self.websocket_connections[task_id] = []
            
        self.websocket_connections[task_id].append(websocket)
        
        if self.debug:
            print(f"[Service] Registered WebSocket for task {task_id}")
    
    async def unregister_websocket(self, task_id: str, websocket: WebSocket):
        """
        Unregister a WebSocket connection for a task.
        
        Args:
            task_id: The task ID
            websocket: WebSocket connection
        """
        if task_id in self.websocket_connections:
            if websocket in self.websocket_connections[task_id]:
                self.websocket_connections[task_id].remove(websocket)
                
                if self.debug:
                    print(f"[Service] Unregistered WebSocket for task {task_id}")
    
    async def _notify_clients(self, task_id: str, message: Dict[str, Any]):
        """
        Send a message to all connected clients for a task.
        
        Args:
            task_id: The task ID
            message: Message to send
        """
        if task_id not in self.websocket_connections:
            return
            
        for websocket in self.websocket_connections[task_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                if self.debug:
                    print(f"[Service] Error sending message to client: {str(e)}")
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task.
        
        Args:
            task_id: The task ID
            
        Returns:
            Task status data
        """
        if task_id not in self.active_tasks:
            return {"status": "not_found"}
            
        task_data = self.active_tasks[task_id]
        
        # Return basic status information
        status_data = {
            "task_id": task_id,
            "url": task_data["url"],
            "status": task_data["status"],
            "created_at": task_data["created_at"]
        }
        
        # If the task completed or failed, include more information
        if task_data["status"] in ["completed", "failed"]:
            if "result" in task_data and task_data["result"]:
                status_data["result"] = task_data["result"]
                
            if "error" in task_data:
                status_data["error"] = task_data["error"]
                
        return status_data
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the result of a completed task.
        
        Args:
            task_id: The task ID
            
        Returns:
            Task result data, or None if the task is not found or not completed
        """
        if task_id not in self.active_tasks:
            return None
            
        task_data = self.active_tasks[task_id]
        
        if task_data["status"] != "completed" or not task_data.get("result"):
            return None
            
        return task_data["result"]
    
    async def generate_website_from_url(self, url: str) -> GenerationResponse:
        """
        Generate a website from a URL.
        
        Args:
            url: URL of the website to clone
            
        Returns:
            Generation response containing the results of the generation
        """
        if self.debug:
            print(f"[Service] Generating website from URL: {url}")
        
        # Ensure the service is initialized
        if self.orchestrator is None:
            await self.initialize()
            
        start_time = time.time()
        
        try:
            # Run the workflow
            workflow_state = await self.orchestrator.run_workflow(url)
            
            # Check if the workflow completed successfully
            if workflow_state["status"] == "completed":
                # Extract HTML and CSS from the component synthesizer results
                component_results = workflow_state["results"].get("component_synthesizer_5", {})
                html = component_results.get("html_output", "")
                css = component_results.get("css_output", "")
                
                # Get validation report
                validation_results = workflow_state["results"].get("validation_6", {})
                validation_report = validation_results.get("validation_report", {})
                
                # Create the output directory if it doesn't exist
                output_path = workflow_state["output_path"]
                if output_path:
                    os.makedirs(output_path, exist_ok=True)
                    
                    # Write HTML and CSS files
                    html_path = os.path.join(output_path, "index.html")
                    css_path = os.path.join(output_path, "styles.css")
                    
                    with open(html_path, "w") as f:
                        f.write(html)
                        
                    with open(css_path, "w") as f:
                        f.write(css)
                
                return GenerationResponse(
                    status="success",
                    quality_score=workflow_state["quality_score"],
                    message="Website generation completed successfully",
                    html=html,
                    css=css,
                    output_path=output_path,
                    html_path=os.path.join(output_path, "index.html"),
                    css_path=os.path.join(output_path, "styles.css"),
                    validation_report=validation_report
                )
            else:
                # Extract error information
                error_message = "Website generation failed"
                if workflow_state["errors"]:
                    error = workflow_state["errors"][-1]
                    error_message = f"Error in {error.get('agent_name', 'unknown agent')}: {error.get('error', 'unknown error')}"
                
                return GenerationResponse(
                    status="error",
                    quality_score=workflow_state["quality_score"],
                    message=error_message,
                    error=error_message
                )
                
        except Exception as e:
            error_message = f"Website generation failed: {str(e)}"
            if self.debug:
                print(f"[Service] {error_message}")
                
            return GenerationResponse(
                status="error",
                message=error_message,
                error=str(e)
            )
            
        finally:
            if self.debug:
                print(f"[Service] Website generation completed in {time.time() - start_time:.2f} seconds")
    
    def get_registered_agents(self) -> List[Dict[str, Any]]:
        """
        Get information about the registered agents.
        
        Returns:
            List of agent information
        """
        return [
            {
                "type": config.agent_type,
                "name": config.name,
                "config": {k: v for k, v in config.config.items() if k not in ["api_key"]}
            }
            for config in self.agent_configs
        ]


# Create an instance of the service for use in FastAPI routes
multi_agent_service = WebsiteGenerationService(
    config={
        "debug": True,
        "output_dir": "generated",
        "screenshots_dir": "screenshots"
    }
)
