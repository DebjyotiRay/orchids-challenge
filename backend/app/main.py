import os
from pathlib import Path
import shutil
import asyncio
import base64
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security, status, WebSocket, WebSocketDisconnect
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .models import CloneRequest, CloneResponse, ApiKeyRequest
from .scraper import WebsiteScraper
from .llm import LLMGenerator
from .bedrock_generator import BedrockGenerator
from .multi_agent.service import multi_agent_service

# Create directories for storing generated content and screenshots
OUTPUT_DIR = Path("generated")
OUTPUT_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR = Path("screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# AWS credentials are already loaded from .env file
# No need to set default values as they're read from environment variables

# Initialize FastAPI application
app = FastAPI(title="Website Clone Generator API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tasks in progress (URL -> task_id)
active_tasks: Dict[str, str] = {}
# Results cache (URL -> result)
results_cache: Dict[str, Dict[str, Any]] = {}
# Store API keys in memory (in a production app, these would be stored securely)
api_keys: Dict[str, Dict[str, str]] = {}

# Mount the generated and screenshots directories with CORS headers
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path

# Create custom static files handler with CORS headers
class CORSStaticFiles(StaticFiles):
    async def __call__(self, scope, receive, send):
        response = await super().__call__(scope, receive, send)
        if response and hasattr(response, "headers"):
            response.headers["Access-Control-Allow-Origin"] = "*"
        return response

# Mount directories with CORS support
app.mount("/generated", CORSStaticFiles(directory="generated"), name="generated")
app.mount("/screenshots", CORSStaticFiles(directory="screenshots"), name="screenshots")

# Add a route to list available generated outputs
@app.get("/api/outputs", response_model=Dict[str, List[str]])
async def list_available_outputs():
    """
    List all available generated outputs for browsing
    """
    output_dir = Path("generated")
    available_outputs = {}
    
    if output_dir.exists():
        for item in output_dir.iterdir():
            if item.is_dir() and (item / "index.html").exists():
                category = item.name
                available_outputs[category] = ["index.html"]
                
                # Add other files in this directory
                for file in item.glob("*.css"):
                    available_outputs[category].append(file.name)
                
    return {"outputs": available_outputs}

# API Router for the legacy single-LLM cloning system
@app.get("/")
async def read_root():
    return {"message": "Website Clone Generator API"}

@app.post("/clone", response_model=Dict[str, str])
async def clone_website(request: CloneRequest, background_tasks: BackgroundTasks):
    """
    Start a website cloning process in the background using the legacy system.
    """
    url = str(request.url)
    
    # Check if we already have a task for this URL
    if url in active_tasks:
        return {"task_id": active_tasks[url], "status": "in_progress"}
    
    # Check if we already have results for this URL
    if url in results_cache:
        return {"task_id": "cached", "status": "complete"}
    
    # Generate a task ID
    task_id = str(hash(url))
    active_tasks[url] = task_id
    
    # Start the cloning process in the background
    background_tasks.add_task(process_clone_request, url, task_id)
    
    return {"task_id": task_id, "status": "started"}

@app.get("/status/{task_id}", response_model=Dict[str, str])
async def get_task_status(task_id: str):
    """
    Check the status of a legacy cloning task.
    """
    # Find the URL for this task ID
    url = None
    for u, tid in active_tasks.items():
        if tid == task_id:
            url = u
            break
    
    if not url:
        return {"status": "not_found"}
    
    if url in results_cache:
        return {"status": "complete", "url": url}
    
    return {"status": "in_progress", "url": url}

@app.get("/result/{task_id}", response_model=CloneResponse)
async def get_task_result(task_id: str):
    """
    Get the results of a completed legacy cloning task.
    """
    # Find the URL for this task ID
    url = None
    for u, tid in active_tasks.items():
        if tid == task_id:
            url = u
            break
    
    if not url or url not in results_cache:
        raise HTTPException(status_code=404, detail="Task not found or not completed yet")
    
    return results_cache[url]

@app.get("/preview/{task_id}", response_class=HTMLResponse)
async def preview_clone(task_id: str):
    """
    Preview the cloned website.
    """
    # Find the URL for this task ID
    url = None
    for u, tid in active_tasks.items():
        if tid == task_id:
            url = u
            break
    
    if not url or url not in results_cache:
        raise HTTPException(status_code=404, detail="Task not found or not completed yet")
    
    html_path = results_cache[url].get("html_path")
    if not html_path or not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="HTML file not found")
    
    with open(html_path) as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)

@app.post("/api/config/keys")
async def configure_api_key(request: ApiKeyRequest):
    """
    Configure an API key for a specific provider
    """
    provider = request.provider
    api_key = request.api_key.get_secret_value()
    
    # Store the API key
    if provider == "aws":
        # For AWS, we need to store additional credentials
        aws_credentials = {
            "access_key": api_key
        }
        
        if request.aws_secret_key:
            aws_credentials["secret_key"] = request.aws_secret_key.get_secret_value()
            
        if request.aws_region:
            aws_credentials["region"] = request.aws_region
        else:
            aws_credentials["region"] = "us-east-1"  # Default region
            
        api_keys[provider] = aws_credentials
        
        # Set AWS environment variables
        os.environ["AWS_ACCESS_KEY_ID"] = api_key
        if request.aws_secret_key:
            os.environ["AWS_SECRET_ACCESS_KEY"] = request.aws_secret_key.get_secret_value()
        if request.aws_region:
            os.environ["AWS_REGION"] = request.aws_region
    else:
        # For other providers, just store the API key
        api_keys[provider] = {"api_key": api_key}
        
        # Set environment variable for the provider
        if provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "google":
            os.environ["GOOGLE_API_KEY"] = api_key
    
    return {"status": "success", "message": f"API key for {provider} configured successfully"}

@app.get("/api/config/keys/status")
async def get_api_key_status():
    """
    Check which API keys are configured
    """
    return {
        "anthropic": "anthropic" in api_keys,
        "openai": "openai" in api_keys,
        "google": "google" in api_keys,
        "aws": "aws" in api_keys
    }

@app.get("/screenshot/{task_id}")
async def get_screenshot(task_id: str):
    """
    Get the screenshot for a cloning task.
    """
    # Find the URL for this task ID
    url = None
    for u, tid in active_tasks.items():
        if tid == task_id:
            url = u
            break
    
    if not url or url not in results_cache:
        raise HTTPException(status_code=404, detail="Task not found or not completed yet")
    
    screenshot_path = results_cache[url].get("screenshot_path")
    if not screenshot_path or not os.path.exists(screenshot_path):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    return FileResponse(screenshot_path)

# API Router for the multi-agent cloning system
@app.post("/multi-agent/clone", response_model=Dict[str, str])
async def multi_agent_clone_website(request: CloneRequest):
    """
    Start a website cloning process using the multi-agent system.
    """
    url = str(request.url)
    
    # Start the cloning process
    task_id = await multi_agent_service.clone_website(url)
    
    return {"task_id": task_id, "status": "started"}

@app.get("/multi-agent/status/{task_id}", response_model=Dict[str, Any])
async def multi_agent_get_task_status(task_id: str):
    """
    Check the status of a multi-agent cloning task.
    """
    status = await multi_agent_service.get_task_status(task_id)
    return status

@app.get("/multi-agent/result/{task_id}")
async def multi_agent_get_task_result(task_id: str):
    """
    Get the results of a completed multi-agent cloning task.
    """
    result = await multi_agent_service.get_task_result(task_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found or not completed yet")
    
    return result

@app.get("/multi-agent/preview/{task_id}", response_class=HTMLResponse)
async def multi_agent_preview_clone(task_id: str):
    """
    Preview the cloned website from the multi-agent system.
    """
    result = await multi_agent_service.get_task_result(task_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found or not completed yet")
    
    html_path = result.get("html_path")
    if not html_path or not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="HTML file not found")
    
    with open(html_path) as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)

@app.websocket("/multi-agent/ws/{task_id}")
async def multi_agent_websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time updates on multi-agent cloning tasks.
    """
    await websocket.accept()
    
    try:
        # Register the WebSocket connection
        await multi_agent_service.register_websocket(task_id, websocket)
        
        # Send initial status
        status = await multi_agent_service.get_task_status(task_id)
        await websocket.send_json({
            "task_id": task_id,
            "event": "connected",
            "status": status
        })
        
        # Keep the connection open until the client disconnects
        while True:
            # Wait for messages from the client (like cancellation)
            data = await websocket.receive_text()
            # For now, just echo the message back
            await websocket.send_text(f"Echo: {data}")
            
    except WebSocketDisconnect:
        # Client disconnected
        print(f"WebSocket client disconnected from task {task_id}")
    finally:
        # Unregister the WebSocket connection
        await multi_agent_service.unregister_websocket(task_id, websocket)

# Legacy background task function
async def process_clone_request(url: str, task_id: str):
    """
    Process a website cloning request in the background using the legacy system.
    """
    try:
        # Scrape the website
        scraper = WebsiteScraper()
        scraped_data = await scraper.scrape(url)
        
        # First try OpenAI
        try:
            print("Trying OpenAI GPT-4o for website cloning...")
            
            # If we have OpenAI API key in memory, use that
            if "openai" in api_keys:
                api_key = api_keys["openai"]["api_key"]
                print("Using OpenAI API key from memory configuration")
            else:
                # Otherwise use the one from environment variables
                api_key = os.environ.get("OPENAI_API_KEY")
                print(f"Using OpenAI API key from environment: {'*' * len(api_key) if api_key else 'Not set'}")
            
            # Initialize the OpenAI generator
            from .openai_generator import OpenAIGenerator
            llm_generator = OpenAIGenerator(model_name="gpt-4o", api_key=api_key)
        except Exception as e:
            print(f"Failed to initialize OpenAI: {e}")
            
            # Try Claude next
            try:
                print("Falling back to Claude for website cloning...")
                model_name = "claude-3-sonnet-20240229"  # Default model
                
                if "anthropic" in api_keys:
                    # Use Claude directly from memory
                    api_key = api_keys["anthropic"]["api_key"]
                    llm_generator = LLMGenerator(model_name=model_name, api_key=api_key)
                else:
                    # Use Claude from environment
                    llm_generator = LLMGenerator(model_name=model_name)  # Will use ANTHROPIC_API_KEY from env if available
            except Exception as e:
                print(f"Failed to initialize Claude: {e}")
                raise Exception("Could not initialize any LLM model for website cloning. Please check your API keys.")
            
        html_content, css_content = await llm_generator.generate_website_clone(scraped_data.dict())
        
        # Create output directory for this result
        result_dir = OUTPUT_DIR / task_id
        result_dir.mkdir(exist_ok=True)
        
        # Save the html and css files
        html_path = result_dir / "index.html"
        with open(html_path, "w") as f:
            f.write(html_content)
        
        css_path = None
        if css_content:
            css_path = result_dir / "styles.css"
            with open(css_path, "w") as f:
                f.write(css_content)
        
        # Store the results in our cache
        results_cache[url] = {
            "html": html_content,
            "css": css_content,
            "html_path": str(html_path),
            "css_path": str(css_path) if css_path else None,
            "screenshot_path": scraped_data.screenshot_path,
            "status": "success"
        }
        
    except Exception as e:
        print(f"Error processing clone request for {url}: {str(e)}")
        # Store the error in our cache
        results_cache[url] = {
            "status": "error",
            "error": str(e)
        }
    finally:
        # Clean up the task from active_tasks if it's still there
        if url in active_tasks and active_tasks[url] == task_id:
            del active_tasks[url]

# Run the FastAPI app using Uvicorn when script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
