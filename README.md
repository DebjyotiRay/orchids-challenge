# Multi-Agent Website Generation System

An advanced website generation system that uses a coordinated team of specialized AI agents to clone and reimagine websites. Unlike traditional single-LLM approaches, our multi-agent architecture delivers superior results through specialized expertise, coordinated workflow, and real-time feedback loops.
## LIVE AT https://v0-orchids.vercel.app/

## Workflow Diagram: 
https://www.mermaidchart.com/app/projects/f999f6ae-25f7-47b4-9ad0-dbfd2e523457/diagrams/c6414640-8be6-4106-aade-154b6d7693d3/share/invite/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkb2N1bWVudElEIjoiYzY0MTQ2NDAtOGJlNi00MTA2LWFhZGUtMTU0YjZkNzY5M2QzIiwiYWNjZXNzIjoiVmlldyIsImlhdCI6MTc0OTI4OTYwMX0.yEqiG0B77iIavAvJrXpsaFfIrAhrhfoCoexTG-V9hVc

## Table of Contents

1. [System Overview](#system-overview)
2. [Multi-Agent Architecture](#multi-agent-architecture)
3. [Agent Descriptions](#agent-descriptions)
4. [Workflow Orchestration](#workflow-orchestration)
5. [Backend Implementation](#backend-implementation)
6. [Frontend Interface](#frontend-interface)
7. [Getting Started](#getting-started)
8. [Usage Examples](#usage-examples)
9. [Performance & Scalability](#performance--scalability)
10. [Future Improvements](#future-improvements)

## System Overview

Orchids transforms the process of website generation through a distributed cognitive approach where specialized agents work in concert, each contributing unique expertise to the final product.

Key advantages over traditional approaches:

- **Specialized Expertise**: Each agent focuses on one aspect of website generation
- **Coordinated Workflow**: LangGraph orchestration ensures smooth agent collaboration
- **Quality Assurance**: Built-in validation and feedback loops improve output quality
- **Real-time Visibility**: Live progress visualization of agent activities
- **Resource Efficiency**: Agents operate independently, enabling parallel processing and scaling

## Multi-Agent Architecture

The system employs six specialized agents that work together in a coordinated workflow:

### Agent Descriptions

1. **Scraper Agent**
   - **Responsibility**: Extracts website content, structure, and assets
   - **Technologies**: Firecrawl for stealth browsing and anti-bot avoidance
   - **Outputs**: HTML, CSS, screenshots, metadata, DOM structure

2. **Semantic Parser Agent**
   - **Responsibility**: Analyzes document structure and component relationships
   - **Technologies**: DOM analysis, component pattern recognition
   - **Outputs**: Component hierarchy, semantic structure, content classification

3. **Style Transfer Agent**
   - **Responsibility**: Extracts design system elements and visual patterns
   - **Technologies**: Color extraction, typography analysis, spacing calculations
   - **Outputs**: Design system (colors, typography, spacing, shadows, etc.)

4. **Layout Generator Agent**
   - **Responsibility**: Creates responsive CSS Grid layouts for various screen sizes
   - **Technologies**: CSS Grid, responsive breakpoints, layout pattern analysis
   - **Outputs**: Grid templates, responsive layout specifications

5. **Component Synthesizer Agent**
   - **Responsibility**: Generates functional React/TypeScript components
   - **Technologies**: React, TypeScript, CSS, HTML
   - **Outputs**: React components, TypeScript interfaces, CSS modules

6. **Validation Agent**
   - **Responsibility**: Quality assurance, accessibility checks, performance testing
   - **Technologies**: Web standards, accessibility guidelines, performance metrics
   - **Outputs**: Validation report, quality score, improvement suggestions

## Workflow Orchestration

The multi-agent workflow is orchestrated using LangGraph's StateGraph pattern:

```
Scraper → Semantic Parser → Style Transfer → Layout Generator → Component Synthesizer → Validation
                                                                      ↑                    |
                                                                      └────────────────────┘
                                                              (Feedback loop on validation failure)
```

### State Management

The `WorkflowOrchestrator` manages the entire process:

1. **Initial State Creation**: When a URL is submitted, a workflow state is created with a unique ID
2. **Agent Execution Sequence**: Agents execute in a predefined sequence, with each agent receiving input from previous agents
3. **State Transitions**: The state graph controls transitions between agents
4. **Feedback Loops**: The validation agent can send work back to the component synthesizer for improvement
5. **Error Handling**: Built-in retries and graceful degradation when operations fail
6. **Event Broadcasting**: Status updates for real-time monitoring

### Data Flow

Data flows between agents through the workflow state:

1. Scraper extracts raw website data
2. Semantic Parser transforms raw data into structured component hierarchies
3. Style Transfer extracts design system from visual elements
4. Layout Generator creates responsive layouts based on semantic structure
5. Component Synthesizer generates functional components using all previous outputs
6. Validation ensures quality standards are met

## Backend Implementation

The backend is built using FastAPI and implements the multi-agent system:

### Core Components

- **BaseAgent**: Abstract class defining the agent interface
- **WorkflowOrchestrator**: Manages agent execution and workflow state
- **WebsiteGenerationService**: High-level service for website generation
- **LangGraph Integration**: Directed state graph for workflow management

### API Endpoints

- `POST /multi-agent/clone`: Start cloning a website
- `GET /multi-agent/status/{task_id}`: Get status of a cloning task
- `GET /multi-agent/result/{task_id}`: Get results of a completed task
- `WS /multi-agent/ws/{task_id}`: WebSocket for real-time updates

### Advanced Features

- **Async Implementation**: All agent operations are asynchronous for maximum throughput
- **Resource Efficiency**: Operations like color extraction use sampling for efficiency
- **Error Recovery**: Agents can retry operations up to a configured number of times
- **Stateless Design**: Each website generation is independent, enabling scaling

## Frontend Interface

The frontend provides a user-friendly interface for website generation:

### Key Features

- **URL Input**: Simple interface to enter website URLs for cloning
- **Real-Time Progress**: Visual display of each agent's activity and progress
- **Multi-Agent Visualization**: See all agents working together in real-time
- **Live Preview**: Immediate display of the generated website
- **Project Browser**: Explore generated code and assets

### Technologies

- HTML, CSS (Tailwind), and JavaScript for the user interface
- WebSocket connection for real-time progress updates
- Dynamic generation progress visualization

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 20+ (for frontend)
- OpenAI API key

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/orchids-challenge.git
cd orchids-challenge
```

2. Install backend dependencies:

```bash
cd backend
pip install -e .
```

3. Set up environment variables:

```bash
cp .env.example .env
# Edit .env to add your OpenAI API key
```

4. Install frontend dependencies:

```bash
cd ../frontend
npm install
```

### Running the Application

#### Backend API

```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

#### Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:3000

## Usage Examples

### Generate a Website Clone

1. Open the website at http://localhost:3000
2. Enter a website URL (e.g., youtube.com, leetcode.com) in the input field
3. Click "Generate" and watch the multi-agent system in action
4. View the real-time progress of each agent as they work together
5. Explore the generated website when the process completes

### Through API

```python
import asyncio
import aiohttp

async def clone_website(url):
    async with aiohttp.ClientSession() as session:
        # Start cloning process
        async with session.post("http://localhost:8000/multi-agent/clone", json={"url": url}) as response:
            data = await response.json()
            task_id = data["task_id"]
            
        # Connect to WebSocket for real-time updates
        async with session.ws_connect(f"http://localhost:8000/multi-agent/ws/{task_id}") as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print(f"Update: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
                    
        # Get final result
        async with session.get(f"http://localhost:8000/multi-agent/result/{task_id}") as response:
            result = await response.json()
            return result

# Run the function
asyncio.run(clone_website("https://example.com"))
```

## Performance & Scalability

The system is designed for production performance:

- **Async Implementation**: All agent operations use asyncio for maximum throughput
- **Resource Efficiency**: Operations like color extraction use sampling to minimize resource usage
- **Stateless Design**: Each website generation is independent, enabling horizontal scaling
- **Parallel Processing**: Agents can work concurrently where the workflow allows

## Future Improvements

Potential areas for enhancement:

1. **Advanced Pattern Recognition**
   - Integration with vector databases for component pattern recognition
   - Machine learning models for identifying common UI patterns

2. **Behavior Extraction**
   - Addition of a JavaScript behavior extraction agent
   - Automated recreation of interactive elements

3. **Distributed Processing**
   - Implementation of a distributed worker pool for parallel scraping
   - Kubernetes deployment for horizontal scaling

4. **Asset Generation**
   - Integration with image generation AI for asset recreation
   - SVG optimization and generation

5. **User Experience**
   - Interactive customization of generated websites
   - Visual editor for modifying generated components

---

## License

[MIT](LICENSE)
