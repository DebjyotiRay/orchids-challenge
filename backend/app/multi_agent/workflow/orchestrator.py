import os
import time
from typing import Dict, Any, List, Optional, Union, Callable, Tuple, TypedDict, cast, Coroutine
import asyncio
import uuid
from pathlib import Path

from langgraph.graph import StateGraph

from ..agents.base_agent import BaseAgent
from .models import WorkflowState, AgentState


class WorkflowOrchestrator:
    """
    Orchestrates the multi-agent workflow for website cloning.
    
    This class uses LangGraph to define a directed state graph for the workflow,
    where each node represents an agent execution and edges represent transitions
    between agents.
    """
    
    def __init__(
        self,
        agents: Dict[str, BaseAgent],
        debug: bool = False,
        output_dir: str = "generated",
        status_callback: Optional[Callable[[Dict[str, Any], str, Optional[str]], Coroutine]] = None,
        **kwargs
    ):
        """
        Initialize the workflow orchestrator.
        
        Args:
            agents: Dictionary mapping agent IDs to agent instances
            debug: Whether to enable debug mode
            output_dir: Output directory for generated files
            status_callback: Callback function for status updates
            **kwargs: Additional configuration parameters
        """
        self.agents = agents
        self.debug = debug
        self.output_dir = output_dir
        self.status_callback = status_callback
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Build the workflow graph
        self.workflow_graph = self._build_workflow_graph()
        
    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the workflow graph using LangGraph.
        
        Returns:
            StateGraph object representing the workflow
        """
        # Create a new graph
        graph = StateGraph(WorkflowState)
        
        # Check what agents we have
        agent_ids = list(self.agents.keys())
        if self.debug:
            print(f"[Orchestrator] Available agents: {agent_ids}")
            
        # Define a simplified linear workflow
        workflow_nodes = []
        
        # Add nodes for each agent
        for agent_id, agent in self.agents.items():
            graph.add_node(agent_id, self._create_agent_handler(agent_id, agent))
            workflow_nodes.append(agent_id)
        
        # Create edges between nodes in sequence
        for i in range(len(workflow_nodes) - 1):
            from_node = workflow_nodes[i]
            to_node = workflow_nodes[i + 1]
            graph.add_edge(from_node, to_node)
        
        # Add an "end" node as we can't use None in conditional edges in v0.3.34
        graph.add_node("end", self._create_end_handler())
        
        # Only add conditional edges if we have both validation and component synthesis
        # Using the observed agent IDs from the logs
        if "validation_6" in self.agents and "component_synthesizer_5" in self.agents:
            # Define the conditional edges for error handling
            graph.add_conditional_edges(
                "validation_6",
                self._validation_router,
                {
                    "success": "end",  # End of workflow
                    "retry": "component_synthesizer_5"  # Retry component synthesis
                }
            )
        
        # Set the entry point (first agent in the workflow)
        if workflow_nodes:
            graph.set_entry_point(workflow_nodes[0])
            
        if self.debug:
            print(f"[Orchestrator] Workflow created with nodes: {workflow_nodes}")
        
        return graph
    
    def _create_agent_handler(
        self, agent_id: str, agent: BaseAgent
    ) -> Callable[[WorkflowState], WorkflowState]:
        """
        Create a handler function for an agent node in the workflow graph.
        
        Args:
            agent_id: ID of the agent
            agent: Agent instance
            
        Returns:
            Handler function for the agent node
        """
        # For langgraph v0.3.34, we need a synchronous function
        def handler(state: WorkflowState) -> WorkflowState:
            """Handler function for the agent node."""
            # Update the current agent ID
            state["current_agent_id"] = agent_id
            
            # Create or update the agent state
            if agent_id not in state["agents"]:
                state["agents"][agent_id] = {
                    "agent_id": agent_id,
                    "name": agent.id,
                    "status": "running",
                    "start_time": time.time(),
                    "retry_count": 0
                }
            else:
                state["agents"][agent_id]["status"] = "running"
                state["agents"][agent_id]["start_time"] = time.time()
                if "retry_count" not in state["agents"][agent_id]:
                    state["agents"][agent_id]["retry_count"] = 0
                state["agents"][agent_id]["retry_count"] += 1
            
            # Send agent started event
            if self.status_callback:
                try:
                    asyncio.create_task(self.status_callback(state, "agent_started", agent_id))
                except Exception as e:
                    if self.debug:
                        print(f"[Orchestrator] Error sending agent_started event: {str(e)}")
            
            try:
                # Get input data for the agent
                input_data = self._get_agent_input(agent_id, state)
                
                # Run the agent using the synchronous wrapper
                if self.debug:
                    print(f"[Orchestrator] Running {agent.id} agent (ID: {agent_id})")
                    
                # Use the synchronous process method to run the actual agent logic
                result = agent.process_sync(input_data)
                
                # Update agent state with result
                state["agents"][agent_id]["status"] = "completed"
                state["agents"][agent_id]["end_time"] = time.time()
                state["agents"][agent_id]["result"] = result
                
                # Store results in the workflow state
                if "results" not in state:
                    state["results"] = {}
                state["results"][agent_id] = result
                
                # Handle specific outputs for certain agents
                if agent_id == "validation_6":
                    state["quality_score"] = result.get("quality_score", 1.0)
                    
                if agent_id == "component_synthesizer_5":
                    state["output_path"] = result.get("output_path", state.get("output_path", "generated"))
                
                # Set workflow status to completed if this is the final agent
                if agent_id == "validation_6" and result.get("passed", False):
                    state["status"] = "completed"
                
                # Send agent completed event
                if self.status_callback:
                    try:
                        asyncio.create_task(self.status_callback(state, "agent_completed", agent_id))
                    except Exception as e:
                        if self.debug:
                            print(f"[Orchestrator] Error sending agent_completed event: {str(e)}")
                
                return state
                
            except Exception as e:
                # Update agent state with error
                state["agents"][agent_id]["status"] = "failed"
                state["agents"][agent_id]["end_time"] = time.time()
                state["agents"][agent_id]["error"] = str(e)
                
                # Add error to workflow errors
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append({
                    "agent_id": agent_id,
                    "agent_name": agent.id,
                    "error": str(e),
                    "time": time.time()
                })
                
                # Set workflow status to failed if max retries reached
                if state["agents"][agent_id].get("retry_count", 0) >= 3:
                    state["status"] = "failed"
                
                if self.debug:
                    print(f"[Orchestrator] Error in {agent.id} agent: {str(e)}")
                
                # Send agent failed event
                if self.status_callback:
                    try:
                        asyncio.create_task(self.status_callback(state, "agent_failed", agent_id))
                    except Exception as e2:
                        if self.debug:
                            print(f"[Orchestrator] Error sending agent_failed event: {str(e2)}")
                
                # Re-raise the exception to be handled by the state graph
                raise e
        
        return handler
    
    def _validation_router(self, state: WorkflowState) -> str:
        """
        Router function for the validation node.
        
        Args:
            state: Current workflow state
            
        Returns:
            ID of the next agent node or None to end the workflow
        """
        # Using the correct validation_6 and component_synthesizer_5 agent IDs
        validation_result = state["agents"].get("validation_6")
        
        if not validation_result or validation_result.get("status") == "failed":
            # If validation failed due to an error, retry component synthesis
            if validation_result and validation_result.get("retry_count", 0) < 3:
                return "retry"
            else:
                # End the workflow with failure if max retries reached
                state["status"] = "failed"
                return "success"  # End the workflow
        
        # Check if validation passed
        if validation_result and "result" in validation_result:
            passed = validation_result["result"].get("passed", False)
            if passed:
                # End the workflow with success
                state["status"] = "completed"
                return "success"
            else:
                # Retry component synthesis if validation didn't pass
                if state["agents"]["component_synthesizer_5"].get("retry_count", 0) < 3:
                    return "retry"
                else:
                    # End the workflow if max retries reached
                    state["status"] = "failed"
                    return "success"  # End the workflow
        
        # Default to ending the workflow
        return "success"
    
    def _create_end_handler(self) -> Callable[[WorkflowState], WorkflowState]:
        """
        Create a handler function for the end node.
        
        Returns:
            Handler function for the end node
        """
        def handler(state: WorkflowState) -> WorkflowState:
            """Handler function for the end node."""
            # Just return the state as is - this is the end of the workflow
            if self.debug:
                print(f"[Orchestrator] Workflow completed with status: {state['status']}")
                
            # Send workflow completed event
            if self.status_callback:
                try:
                    asyncio.create_task(self.status_callback(state, 
                                                            "workflow_completed" if state['status'] == "completed" else "workflow_failed", 
                                                            None))
                except Exception as e:
                    if self.debug:
                        print(f"[Orchestrator] Error sending workflow_completed event: {str(e)}")
                        
            return state
        
        return handler
        
    async def run_workflow(self, url: str) -> WorkflowState:
        """
        Run the workflow for a given URL.
        
        Args:
            url: URL of the website to clone
            
        Returns:
            Final workflow state
        """
        # Create a unique output directory for this run
        output_dir = os.path.join(
            self.output_dir, 
            str(uuid.uuid4().int)[:20]
        )
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize the workflow state as a TypedDict
        initial_state: WorkflowState = {
            "url": url,
            "status": "running",
            "output_path": output_dir,
            "current_agent_id": None,
            "agents": {},
            "results": {},
            "errors": [],
            "quality_score": 0.0
        }
        
        try:
            # Run the workflow
            if self.debug:
                print(f"[Orchestrator] Starting workflow for URL: {url}")
            
            # First compile the graph (required in langgraph v0.3.34)
            compiled_graph = self.workflow_graph.compile()
            
            # Then invoke the compiled graph
            final_state = compiled_graph.invoke(initial_state)
            
            # Update status if needed
            if final_state["status"] == "running":
                if any(agent.get("status") == "failed" for agent in final_state["agents"].values()):
                    final_state["status"] = "failed"
                else:
                    final_state["status"] = "completed"
            
            return final_state
            
        except Exception as e:
            if self.debug:
                print(f"[Orchestrator] Workflow failed: {str(e)}")
            
            # Update the state with the error
            initial_state["status"] = "failed"
            initial_state["errors"].append({
                "agent_id": "orchestrator",
                "agent_name": "Orchestrator",
                "error": str(e),
                "time": time.time()
            })
            
            return initial_state
    
    def _get_agent_input(self, agent_id: str, state: WorkflowState) -> Dict[str, Any]:
        """
        Get input data for an agent based on the current workflow state.
        
        Args:
            agent_id: ID of the agent
            state: Current workflow state
            
        Returns:
            Input data for the agent
        """
        # Base input with the URL
        input_data = {"url": state["url"]}
        
        # Add results from previous agents based on the correct agent IDs
        if agent_id == "semantic_parser_2" and "scraper_1" in state["results"]:
            # Semantic parser needs the scraper results
            input_data.update(state["results"]["scraper_1"])
            
        elif agent_id == "style_transfer_3":
            # Style transfer needs the scraper and semantic parser results
            if "scraper_1" in state["results"]:
                input_data.update(state["results"]["scraper_1"])
            if "semantic_parser_2" in state["results"]:
                input_data.update(state["results"]["semantic_parser_2"])
                
        elif agent_id == "layout_generator_4":
            # Layout generator needs the semantic parser and style transfer results
            if "semantic_parser_2" in state["results"]:
                input_data.update(state["results"]["semantic_parser_2"])
            if "style_transfer_3" in state["results"]:
                input_data.update(state["results"]["style_transfer_3"])
                
        elif agent_id == "component_synthesizer_5":
            # Component synthesizer needs results from all previous agents
            for prev_agent_id in ["scraper_1", "semantic_parser_2", "style_transfer_3", "layout_generator_4"]:
                if prev_agent_id in state["results"]:
                    input_data.update(state["results"][prev_agent_id])
                    
        elif agent_id == "validation_6" and "component_synthesizer_5" in state["results"]:
            # Validation needs the component synthesizer results
            input_data.update(state["results"]["component_synthesizer_5"])
            
        # Add output path to component synthesizer and validation input
        if agent_id in ["component_synthesizer_5", "validation_6"] and "output_path" in state:
            input_data["output_path"] = state["output_path"]
            
        return input_data
