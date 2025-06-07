import os
import json
import base64
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, BotoCoreError

class BedrockGenerator:
    """Class to handle interactions with AWS Bedrock Claude for website cloning."""
    
    def __init__(
        self, 
        model_id: str = "anthropic.claude-3-7-sonnet-20250219-v1:0", 
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        inference_profile_arn: Optional[str] = None
    ):
        """
        Initialize the Bedrock generator with Claude.
        
        Args:
            model_id: The specific Bedrock model to use
            region_name: AWS region name
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_session_token: AWS session token (for temporary credentials)
            inference_profile_arn: AWS Bedrock inference profile ARN (required for some models)
        """
        self.model_id = model_id
        self.inference_profile_arn = inference_profile_arn
        
        # Use provided credentials or fall back to environment variables/AWS config
        self.region_name = region_name or os.environ.get("AWS_REGION", "us-east-1")
        self.aws_access_key_id = aws_access_key_id or os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.aws_session_token = aws_session_token or os.environ.get("AWS_SESSION_TOKEN")
        
        # Create boto3 session with explicit credentials if provided
        session_kwargs = {}
        if self.aws_access_key_id and self.aws_secret_access_key:
            session_kwargs.update({
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
            })
            
            # Add session token if it exists
            if self.aws_session_token:
                session_kwargs["aws_session_token"] = self.aws_session_token
        
        session = boto3.Session(region_name=self.region_name, **session_kwargs)
        
        # Create bedrock client
        self.bedrock_runtime = session.client(
            service_name="bedrock-runtime",
            region_name=self.region_name
        )
    
    async def generate_website_clone(self, scraped_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """
        Generate HTML and CSS for a cloned website based on scraped data using AWS Bedrock Claude.
        
        Args:
            scraped_data: Dictionary containing scraped website data
            
        Returns:
            Tuple containing HTML and CSS content
        """
        # Create a system prompt with instructions
        system_prompt = self._create_system_prompt()
        
        # Create a user message with the scraped data
        user_prompt = self._create_user_prompt(scraped_data)
        
        # Call Bedrock Claude with these prompts
        try:
            response = self._invoke_bedrock_model(system_prompt, user_prompt)
            content = response["content"][0]["text"]
            
            # Extract HTML and CSS from the response
            html_content = self._extract_code_block(content, "html")
            css_content = self._extract_code_block(content, "css")
            
            return html_content, css_content
        except (ClientError, BotoCoreError) as e:
            print(f"AWS Bedrock error: {e}")
            raise Exception(f"Failed to generate website clone through AWS Bedrock: {str(e)}")
    
    def _invoke_bedrock_model(self, system_prompt: str, user_prompt: str) -> Dict:
        """Call AWS Bedrock Claude model with the given prompts."""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100000,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        }
        
        kwargs = {
            "body": json.dumps(request_body)
        }
        
        # Use inference profile ARN if provided, otherwise use model ID
        if self.inference_profile_arn:
            kwargs["inferenceProfileArn"] = self.inference_profile_arn
        else:
            kwargs["modelId"] = self.model_id
            
        print(f"Invoking Bedrock with {'inferenceProfileArn' if self.inference_profile_arn else 'modelId'}")
        
        try:
            response = self.bedrock_runtime.invoke_model(**kwargs)
        except Exception as e:
            if "on-demand throughput isn't supported" in str(e):
                print("Model requires an inference profile. Trying alternative approach...")
                # Try to find the default inference profile for this model
                try:
                    # First try using the default inference profile format
                    inference_id = f"{self.model_id.replace(':', '-')}-default"
                    print(f"Trying default inference profile: {inference_id}")
                    kwargs.pop("modelId", None)
                    kwargs["inferenceProfileArn"] = inference_id
                    response = self.bedrock_runtime.invoke_model(**kwargs)
                except Exception as inner_e:
                    print(f"Failed with default inference profile: {inner_e}")
                    raise e
            else:
                raise e
        
        response_body = json.loads(response.get("body").read())
        return response_body
        
    def _create_system_prompt(self) -> str:
        """Create the system prompt for Claude."""
        return """You are an expert web developer specializing in creating pixel-perfect HTML/CSS clones of website designs. Your task is to create an HTML and CSS implementation that visually recreates the website design information you'll be provided.

Instructions:
1. Analyze the provided website information thoroughly, including layout structure, colors, fonts, and the screenshot.
2. Create a single HTML file with embedded CSS that recreates the visual appearance of the original site.
3. Focus on visual fidelity and responsive design.
4. Use modern HTML5 and CSS3 techniques.
5. For images, use placeholder services like https://placehold.co/ with similar dimensions and aspect ratios.
6. The HTML should be valid, accessible, and follow best practices.
7. Use CSS variables for colors and theming.

Output Format:
You should provide two code blocks:
1. First, output an HTML document with embedded CSS in the head section
2. Second, provide (optional) additional CSS that could be in a separate file

Important:
- Recreate the layout as closely as possible using semantic HTML
- Match colors, fonts, spacing, and proportions
- Make sure text content is preserved
- Use inline SVG or Font Awesome for icons where possible
- Implement responsive design principles
- If needed, add minimal JavaScript for interactive elements
"""

    def _create_user_prompt(self, scraped_data: Dict[str, Any]) -> str:
        """Create the user prompt with scraped website data."""
        
        screenshot_path = scraped_data.get('screenshot_path')
        screenshot_b64 = ""
        
        # Read screenshot if available and convert to base64
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, "rb") as img_file:
                screenshot_b64 = base64.b64encode(img_file.read()).decode("utf-8")
        
        # Build a structured message with all the data
        message = f"""
# Website Clone Request

Please create a pixel-perfect HTML and CSS clone of the following website:

## Website Title
{scraped_data.get('meta_tags', {}).get('title', 'Untitled Website')}

## Layout Structure
```json
{json.dumps(scraped_data.get('layout_structure', {}), indent=2)}
```

## Color Palette
{', '.join(scraped_data.get('color_palette', []))}

## Fonts
{', '.join(scraped_data.get('fonts', []))}

## Text Content Sample
```
{scraped_data.get('text_content', '')[:500]}... (truncated)
```

## Meta Tags
```json
{json.dumps(scraped_data.get('meta_tags', {}), indent=2)}
```

Please analyze the provided information and create an HTML file with embedded CSS that recreates this website's design. Focus on recreating the visual layout, styling, and overall appearance.
"""

        # Minimized HTML and CSS to provide context but not overwhelm the model
        if 'html' in scraped_data and len(scraped_data['html']) > 0:
            # Strip comments and minify HTML to reduce token count
            html_sample = scraped_data['html']
            # Just take a portion to avoid token limits
            html_sample = self._truncate_html(html_sample, max_length=10000)
            message += f"\n\n## HTML Structure Sample\n```html\n{html_sample}\n```"
        
        if 'css' in scraped_data and scraped_data['css']:
            css_sample = scraped_data['css']
            # Just take a portion to avoid token limits
            if len(css_sample) > 5000:
                css_sample = css_sample[:5000] + "... (truncated)"
            message += f"\n\n## CSS Sample\n```css\n{css_sample}\n```"

        # If we have a screenshot, include it
        if screenshot_b64:
            message += f"\n\n## Screenshot\n<img src=\"data:image/png;base64,{screenshot_b64}\" alt=\"Website Screenshot\">"

        return message
    
    def _truncate_html(self, html: str, max_length: int = 10000) -> str:
        """
        Truncate HTML intelligently to stay under token limits while preserving structure.
        """
        if len(html) <= max_length:
            return html
            
        # Simple truncation that tries to maintain valid HTML structure
        truncated = html[:max_length]
        # Make sure we don't cut in the middle of a tag
        last_close_tag = truncated.rfind('>')
        if last_close_tag > 0:
            truncated = truncated[:last_close_tag + 1]
        
        return truncated + "\n<!-- HTML truncated due to length -->"
    
    def _extract_code_block(self, text: str, language: str) -> str:
        """
        Extract a code block of the specified language from text.
        
        Args:
            text: Text containing code blocks
            language: Language of the code block to extract (html, css)
            
        Returns:
            The extracted code block or an empty string if not found
        """
        import re
        
        # Pattern to match code blocks: ```language ... ```
        pattern = f"```{language}\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Try alternative pattern for HTML with doctype
        if language == "html":
            doctype_pattern = r"<!DOCTYPE html>(.*?)(?:```|$)"
            doctype_matches = re.findall(doctype_pattern, text, re.DOTALL)
            if doctype_matches:
                return "<!DOCTYPE html>" + doctype_matches[0].strip()
        
        return ""
