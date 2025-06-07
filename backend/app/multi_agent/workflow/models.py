from typing import Dict, Any, List, Optional, Union, TypedDict
from pydantic import BaseModel, Field


class AgentState(TypedDict, total=False):
    """
    Represents the state of an agent in the workflow.
    
    This model tracks the execution status and results of an individual agent.
    """
    agent_id: str
    name: str
    status: str  # pending, running, completed, failed
    start_time: Optional[float]
    end_time: Optional[float]
    result: Dict[str, Any]
    error: Optional[str]
    retry_count: int


class WorkflowState(TypedDict, total=False):
    """
    Represents the overall state of the multi-agent workflow.
    
    This model tracks the execution status and results of the entire workflow,
    including the state of each individual agent and the data being passed
    between them.
    """
    url: str
    current_agent_id: Optional[str]
    agents: Dict[str, AgentState]
    results: Dict[str, Any]
    errors: List[Dict[str, Any]]
    quality_score: float
    status: str  # pending, running, completed, failed
    output_path: Optional[str]


class GenerationRequest(BaseModel):
    """
    Request model for website generation.
    
    This model defines the input parameters for a website generation request.
    """
    url: str
    output_dir: Optional[str] = None
    debug: bool = False
    max_retries: int = 3
    timeout: int = 60


class GenerationResponse(BaseModel):
    """
    Response model for website generation.
    
    This model defines the output structure for a website generation response.
    """
    status: str  # success, error
    quality_score: float = 0.0
    message: str
    html: Optional[str] = None
    css: Optional[str] = None
    output_path: Optional[str] = None
    html_path: Optional[str] = None
    css_path: Optional[str] = None
    error: Optional[str] = None
    validation_report: Optional[Dict[str, Any]] = None


class AgentConfig(BaseModel):
    """
    Configuration model for an agent.
    
    This model defines the configuration parameters for an agent instance.
    """
    agent_type: str
    name: str
    debug: bool = False
    max_retries: int = 3
    timeout: int = 60
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowConfig(BaseModel):
    """
    Configuration model for the workflow.
    
    This model defines the configuration parameters for the entire workflow,
    including the configuration of each agent and the workflow settings.
    """
    agents: List[AgentConfig]
    debug: bool = False
    output_dir: str = "generated"
    screenshots_dir: str = "screenshots"
