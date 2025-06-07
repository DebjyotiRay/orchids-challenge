# Multi-Agent Website Cloning System

This package implements a sophisticated multi-agent system for website cloning using LangGraph for agent orchestration and Firecrawl for website scraping. The system is designed as a production-ready backend component that automatically generates responsive websites by analyzing and recreating existing web designs.

## Architecture

The system follows a six-agent architecture, where each agent specializes in a particular aspect of website cloning:

1. **Scraper Agent**: Extracts website content using Firecrawl, handling anti-bot protection
2. **Semantic Parser Agent**: Analyzes website structure to identify components and layout patterns
3. **Style Transfer Agent**: Extracts design system elements like colors, typography, and spacing
4. **Layout Generator Agent**: Creates responsive CSS Grid specifications
5. **Component Synthesizer Agent**: Generates HTML, CSS, and React/TypeScript components
6. **Validation Agent**: Performs quality assurance on generated code

The workflow is orchestrated using LangGraph's StateGraph pattern, providing robust error handling, retries, and conditional execution paths.

## Features

- **Advanced Scraping**: Utilizes Firecrawl for stealth browsing and bot-protection avoidance
- **Semantic Analysis**: Employs sophisticated DOM structure analysis to identify UI patterns
- **Design System Extraction**: Creates a complete design system including colors, typography, spacing
- **Responsive Layouts**: Generates mobile-first CSS Grid layouts with appropriate breakpoints
- **Component Generation**: Creates modern React components with TypeScript interfaces
- **Quality Validation**: Performs accessibility, performance, and SEO checks on output

## Workflow

The workflow follows a sequential process with feedback loops:

```
Scraper → Semantic Parser → Style Transfer → Layout Generator → Component Synthesizer → Validation
                                                                       ↑                    |
                                                                       └────────────────────┘
                                                                      (Feedback loop on validation failure)
```

## Usage

To use the system, create an instance of `WebsiteGenerationService` and call the `generate_website_from_url` method:

```python
import asyncio
from app.multi_agent.service import WebsiteGenerationService

async def main():
    # Create service
    service = WebsiteGenerationService({
        "debug": True,
        "output_dir": "generated"
    })
    
    # Initialize service
    await service.initialize()
    
    # Generate website from URL
    result = await service.generate_website_from_url("https://example.com")
    
    print(f"Generated website: {result.output_path}")
    print(f"Quality score: {result.quality_score}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The system can be configured with various parameters:

- **Debug Mode**: Enable detailed logging for each agent
- **Output Directory**: Specify where generated websites are saved
- **API Keys**: Provide API keys for external services like Firecrawl
- **Agent-Specific Config**: Each agent has specific configurations

## Directory Structure

```
app/multi_agent/
├── __init__.py                # Package initialization
├── service.py                 # Main service interface
├── agents/                    # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py          # Base agent class
│   ├── scraper_agent.py       # Website scraper
│   ├── semantic_parser_agent.py # DOM structure analyzer
│   ├── style_transfer_agent.py  # Design system extractor
│   ├── layout_generator_agent.py # Layout creator
│   ├── component_synthesizer_agent.py # Component generator
│   └── validation_agent.py    # Quality assurance
└── workflow/                  # Orchestration components
    ├── __init__.py
    ├── models.py              # State models
    ├── agent_factory.py       # Agent creation
    └── orchestrator.py        # LangGraph workflow
```

## Required Dependencies

The system requires the following dependencies:

- LangGraph: For agent orchestration and state management
- Firecrawl: For website scraping
- BeautifulSoup4: For HTML parsing
- Pillow & NumPy: For image processing
- scikit-learn: For color extraction

## Error Handling

The system implements comprehensive error handling:

- **Agent retries**: Each agent can retry operations up to a configured number of times
- **Graceful degradation**: The system falls back to simpler approaches when advanced operations fail
- **Validation feedback**: The validation agent provides feedback to improve component synthesis

## Performance and Scalability

The system is designed for production performance:

- **Async implementation**: All agent operations are async for maximum throughput
- **Resource efficiency**: Operations like color extraction use sampling to minimize resource usage
- **Stateless design**: Each website generation is independent, enabling horizontal scaling

## Future Improvements

Potential areas for enhancement:

- Integration with vector databases for component pattern recognition
- Addition of a JavaScript behavior extraction agent
- Implementation of a distributed worker pool for parallel scraping
- Integration with image generation AI for asset recreation
