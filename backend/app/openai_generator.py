import os
import json
from typing import Dict, Any, List, Optional, Tuple

from openai import OpenAI

class OpenAIGenerator:
    """
    Generator that uses OpenAI's GPT models to generate website clones.
    """
    
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        """
        Initialize the OpenAI generator.
        
        Args:
            model_name: The OpenAI model to use
            api_key: The OpenAI API key, or None to use the environment variable
        """
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Either pass it explicitly or "
                "set the OPENAI_API_KEY environment variable."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        
    async def generate_website_clone(self, scraped_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate an HTML and CSS clone of a website based on scraped data.
        
        Args:
            scraped_data: Dictionary containing the scraped website data
            
        Returns:
            Tuple of (html_content, css_content)
        """
        html = scraped_data.get("html", "")
        url = scraped_data.get("url", "")
        title = scraped_data.get("title", "")
        screenshot_path = scraped_data.get("screenshot_path", "")
        
        # Our optimized color palette
        colors = {
            "primary": "#3c87c6",   # Blue
            "secondary": "#a4121c", # Red
            "accent": "#e84610",    # Orange
            "background": "#f8f8f8", # Light gray
            "text": "#232120"       # Dark gray
        }
        
        # Create the prompt for OpenAI
        prompt = f"""You are an expert web developer specializing in creating pixel-perfect HTML/CSS clones.
        
Create a complete and detailed HTML and CSS implementation for the website {title or url} based on the provided data.
Use the following color palette:
- Primary color (blue): {colors["primary"]}
- Secondary color (red): {colors["secondary"]}
- Accent color (orange): {colors["accent"]}
- Background color: {colors["background"]}
- Text color: {colors["text"]}

Guidelines:
1. Create semantic, accessible HTML5 that matches the structure and layout
2. Use CSS variables for the color palette
3. Implement proper responsive design
4. Structure the code cleanly with appropriate comments
5. Include realistic sample content that matches the website's theme
6. Use modern CSS techniques including flexbox or grid
7. Don't include any JavaScript

Return two code blocks:
1. A complete HTML file (index.html)
2. A complete CSS file (styles.css)

The HTML should reference the CSS file with a relative path: <link rel="stylesheet" href="styles.css">
"""

        # Make request to OpenAI API
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert web developer specializing in HTML and CSS."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096
        )
        
        content = response.choices[0].message.content
        
        # Extract HTML and CSS from the response
        html_content = self._extract_code_block(content, "html")
        css_content = self._extract_code_block(content, "css")
        
        # If no HTML content was found using ```html``` markers, look for <!DOCTYPE html>
        if not html_content and "<!DOCTYPE html>" in content:
            start_idx = content.find("<!DOCTYPE html>")
            end_idx = content.find("```", start_idx)
            if end_idx == -1:
                end_idx = len(content)
            html_content = content[start_idx:end_idx].strip()
        
        # If no CSS content was found, look for a CSS block that may not be properly formatted
        if not css_content:
            css_markers = ["/* CSS */", "body {", ":root {", "* {"]
            for marker in css_markers:
                if marker in content:
                    start_idx = content.find(marker)
                    end_idx = len(content)
                    css_block = content[start_idx:end_idx].strip()
                    if css_block and len(css_block) > 50:
                        css_content = css_block
                        break
        
        return html_content, css_content
    
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
        pattern = f"```{language}\\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        return ""
