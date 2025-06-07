from pydantic import BaseModel, HttpUrl, Field, SecretStr
from typing import Optional, List, Dict, Any, Literal

class CloneRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL of the website to clone")
    
class CloneResponse(BaseModel):
    html: str = Field(..., description="Generated HTML content")
    css: Optional[str] = Field(None, description="Generated CSS content")
    status: str = Field("success", description="Status of the cloning process")
    
class ScrapeResult(BaseModel):
    html: str = Field(..., description="HTML content of the website")
    css: Optional[str] = Field(None, description="CSS content of the website")
    screenshot_path: str = Field(..., description="Path to the screenshot of the website")
    text_content: str = Field(..., description="Text content extracted from the website")
    meta_tags: Dict[str, str] = Field(default_factory=dict, description="Meta tags extracted from the website")
    color_palette: List[str] = Field(default_factory=list, description="Dominant colors extracted from the website")
    fonts: List[str] = Field(default_factory=list, description="Fonts used in the website")
    layout_structure: Dict[str, Any] = Field(default_factory=dict, description="Layout structure of the website")

class ApiKeyRequest(BaseModel):
    provider: Literal["anthropic", "openai", "google", "aws"] = Field(..., description="API key provider")
    api_key: SecretStr = Field(..., description="API key value")
    aws_secret_key: Optional[SecretStr] = Field(None, description="AWS Secret Access Key (only for AWS)")
    aws_region: Optional[str] = Field(None, description="AWS Region (only for AWS)")
