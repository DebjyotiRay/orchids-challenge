import os
from typing import Dict, Any, List, Optional, Type

from ..agents.base_agent import BaseAgent
from ..agents.scraper_agent import ScraperAgent
from ..agents.semantic_parser_agent import SemanticParserAgent
from ..agents.style_transfer_agent import StyleTransferAgent
from ..agents.layout_generator_agent import LayoutGeneratorAgent
from ..agents.component_synthesizer_agent import ComponentSynthesizerAgent
from ..agents.validation_agent import ValidationAgent
from .models import AgentConfig


class AgentFactory:
    """
    Factory class for creating agent instances.
    
    This class provides methods for creating instances of different agent types
    with the specified configuration parameters.
    """
    
    # Map agent types to agent classes
    _agent_classes: Dict[str, Type[BaseAgent]] = {
        "scraper": ScraperAgent,
        "semantic_parser": SemanticParserAgent,
        "style_transfer": StyleTransferAgent,
        "layout_generator": LayoutGeneratorAgent,
        "component_synthesizer": ComponentSynthesizerAgent,
        "validation": ValidationAgent
    }
    
    @classmethod
    async def create_agent(cls, config: AgentConfig) -> BaseAgent:
        """
        Create a new agent instance with the specified configuration.
        
        Args:
            config: Agent configuration
            
        Returns:
            New agent instance
            
        Raises:
            ValueError: If the agent type is invalid
        """
        agent_class = cls._agent_classes.get(config.agent_type)
        if not agent_class:
            raise ValueError(f"Invalid agent type: {config.agent_type}")
        
        # Create an instance of the agent class with the specified configuration
        agent = agent_class(
            name=config.name,
            debug=config.debug,
            timeout=config.timeout,
            retry_limit=config.max_retries,
            **config.config
        )
        
        return agent
    
    @classmethod
    async def create_agents_from_config(
        cls, agent_configs: List[AgentConfig]
    ) -> Dict[str, BaseAgent]:
        """
        Create multiple agent instances from a list of configurations.
        
        Args:
            agent_configs: List of agent configurations
            
        Returns:
            Dictionary mapping agent IDs to agent instances
        """
        agents = {}
        
        for i, config in enumerate(agent_configs):
            # Generate a unique ID for the agent if not specified
            agent_id = f"{config.agent_type}_{i+1}"
            
            # Create the agent instance
            agent = await cls.create_agent(config)
            
            # Add the agent to the dictionary
            agents[agent_id] = agent
            
        return agents
    
    @classmethod
    def create_default_workflow_agents(
        cls, debug: bool = False, **kwargs
    ) -> List[AgentConfig]:
        """
        Create a default set of agent configurations for a complete workflow.
        
        Args:
            debug: Whether to enable debug mode for all agents
            **kwargs: Additional configuration parameters
            
        Returns:
            List of agent configurations
        """
        # Get configuration values from kwargs or environment variables
        output_dir = kwargs.get("output_dir", os.getenv("OUTPUT_DIR", "generated"))
        screenshots_dir = kwargs.get("screenshots_dir", os.getenv("SCREENSHOTS_DIR", "screenshots"))
        firecrawl_api_key = kwargs.get("firecrawl_api_key", os.getenv("FIRECRAWL_API_KEY", ""))
        openai_api_key = kwargs.get("openai_api_key", os.getenv("OPENAI_API_KEY", ""))
        
        # Create agent configurations
        agent_configs = [
            # Scraper Agent
            AgentConfig(
                agent_type="scraper",
                name="ScrapeWebsite",
                debug=debug,
                config={
                    "api_key": firecrawl_api_key,
                    "stealth_mode": True,
                    "proxy_rotation": True,
                    "screenshots_dir": screenshots_dir
                }
            ),
            
            # Semantic Parser Agent
            AgentConfig(
                agent_type="semantic_parser",
                name="ParseStructure",
                debug=debug,
                config={
                    "analyze_text_semantics": True,
                    "analyze_component_patterns": True,
                    "analyze_heading_structure": True
                }
            ),
            
            # Style Transfer Agent
            AgentConfig(
                agent_type="style_transfer",
                name="GenerateDesignSystem",
                debug=debug,
                config={
                    "api_key": openai_api_key,
                    "color_extraction_mode": "pixel",
                    "min_colors": 5,
                    "max_colors": 10
                }
            ),
            
            # Layout Generator Agent
            AgentConfig(
                agent_type="layout_generator",
                name="GenerateLayout",
                debug=debug,
                config={
                    "column_counts": {
                        "mobile": 4,
                        "tablet": 8,
                        "desktop": 12
                    },
                    "breakpoints": {
                        "mobile": "0px",
                        "tablet": "768px",
                        "desktop": "1200px"
                    }
                }
            ),
            
            # Component Synthesizer Agent
            AgentConfig(
                agent_type="component_synthesizer",
                name="GenerateComponents",
                debug=debug,
                config={
                    "component_dir": "components",
                    "output_dir": output_dir,
                    "typescript": True,
                    "react_version": "18"
                }
            ),
            
            # Validation Agent
            AgentConfig(
                agent_type="validation",
                name="ValidateWebsite",
                debug=debug,
                config={
                    "performance_threshold": int(os.getenv("PERFORMANCE_THRESHOLD", "90")),
                    "accessibility_threshold": int(os.getenv("ACCESSIBILITY_THRESHOLD", "95")),
                    "seo_threshold": int(os.getenv("SEO_THRESHOLD", "90")),
                    "best_practices_threshold": int(os.getenv("BEST_PRACTICES_THRESHOLD", "85"))
                }
            )
        ]
        
        return agent_configs
