#!/usr/bin/env python
import os
import json
import base64
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from app.multi_agent.agents.scraper_agent import ScraperAgent


class EnhancedWebsiteGenerator:
    """A sophisticated website generator using chain-of-thought with multiple specialized prompts."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the generator with OpenAI API key.
        
        Args:
            api_key: The OpenAI API key, or None to use environment variable
        """
        load_dotenv()
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Either pass it explicitly or "
                "set the OPENAI_API_KEY environment variable."
            )
        
        # Initialize the OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Initialize our scraper
        self.scraper = ScraperAgent(
            debug=True,
            api_key=os.environ.get("FIRECRAWL_API_KEY", ""),
            extract_html=True,
            take_screenshot=True,
            screenshots_dir="screenshots"
        )
        
        # Define our enhanced color palette
        self.colors = {
            "primary": "#3c87c6",      # Blue (primary brand color)
            "secondary": "#a4121c",    # Red (for secondary elements)
            "accent": "#e84610",       # Orange (for calls to action, highlights)
            "background": "#f8f8f8",   # Light gray (background)
            "text": "#232120",         # Dark gray (text color)
            "light-text": "#666666",   # Medium gray (for secondary text)
            "border": "#e8e8e8",       # Very light gray (for borders)
            "success": "#5cb85c",      # Green (for success states)
            "warning": "#f0ad4e",      # Yellow (for warning states)
            "error": "#d9534f"         # Red (for error states)
        }
    
    async def scrape_website(self, url: str) -> Dict[str, Any]:
        """
        Scrape a website using the ScraperAgent.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary with scraped website data
        """
        # Prepare input for the scraper
        scraper_input = {"url": url}
        
        # Process using the scraper agent
        result = await self.scraper.process(scraper_input)
        
        print(f"Scraped website: {url}")
        print(f"Title: {result.get('title', 'Unknown')}")
        print(f"Screenshot: {result.get('screenshot_path', 'No screenshot')}")
        
        return result
    
    def analyze_screenshot(self, screenshot_path: str) -> Dict[str, Any]:
        """
        Analyze the screenshot to extract visual information.
        
        Args:
            screenshot_path: Path to the screenshot
            
        Returns:
            Dictionary with visual analysis results
        """
        print("Step 1: Analyzing website screenshot...")
        
        # Convert screenshot to base64
        with open(screenshot_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Create a detailed prompt for visual analysis
        prompt = f"""You are an expert UI/UX designer specializing in analyzing website screenshots. 
        Perform a DETAILED VISUAL ANALYSIS of this website screenshot.
        
        Focus on:
        1. Overall layout structure (type of layout, major sections)
        2. Color scheme (identify ALL colors used and their purposes)
        3. Typography (font families, sizes, weights for different text elements)
        4. UI components (identify all UI components and their visual characteristics)
        5. Visual hierarchy (how information is prioritized visually)
        6. Spacing patterns (identify spacing between elements)
        7. Responsive design cues (if visible)
        8. Interactive elements (buttons, links, forms, etc.)
        
        Be EXTREMELY SPECIFIC AND DETAILED in your analysis. Include exact dimensions, color codes (estimate if needed),
        spacing values, and precise descriptions of every visual element.
        
        Format your response as structured JSON with the following sections:
        - layout: Overall layout structure
        - colorScheme: All colors used with estimated color codes and their purposes
        - typography: Font details for all text elements
        - uiComponents: Detailed list of all UI components
        - spacing: Spacing patterns
        - responsive: Responsive design cues
        - interactiveElements: Details on all interactive elements
        """
        
        # Send request to OpenAI API for visual analysis
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=3000
        )
        
        visual_analysis = json.loads(response.choices[0].message.content)
        print("Visual analysis completed")
        
        return visual_analysis
    
    def analyze_html_structure(self, html_content: str) -> Dict[str, Any]:
        """
        Analyze the HTML structure to extract semantic information.
        
        Args:
            html_content: HTML content of the website
            
        Returns:
            Dictionary with HTML structure analysis
        """
        print("Step 2: Analyzing HTML structure...")
        
        # Create a detailed prompt for HTML structure analysis
        prompt = f"""You are an expert web developer specializing in HTML semantics and structure analysis.
        Perform a DETAILED STRUCTURAL ANALYSIS of this HTML code.
        
        HTML CODE:
        ```html
        {html_content[:15000]}  # Limit to first 15k chars to avoid token limits
        ```
        
        Focus on:
        1. Document structure (DOCTYPE, head elements, body organization)
        2. Semantic HTML elements used (header, nav, main, section, article, aside, footer, etc.)
        3. Class naming patterns (identify naming conventions, CSS framework clues)
        4. DOM hierarchy (nesting levels, parent-child relationships)
        5. Content organization (how content is structured and grouped)
        6. Navigation structure (menu organization, breadcrumbs)
        7. Form elements and their attributes
        8. Image and media elements
        9. Accessibility features (if present)
        
        Be EXTREMELY SPECIFIC AND DETAILED in your analysis. Don't just list elements but explain their purpose, 
        relationships, and how they contribute to the overall structure.
        
        Format your response as structured JSON with the following sections:
        - documentStructure: Document structure details
        - semanticElements: Analysis of semantic HTML elements
        - classPatterns: Class naming patterns and conventions
        - domHierarchy: DOM hierarchy analysis
        - contentOrganization: How content is structured
        - navigation: Navigation structure details
        - forms: Form elements analysis (if present)
        - media: Image and media elements analysis
        - accessibility: Accessibility features (if present)
        """
        
        # Send request to OpenAI API for HTML structure analysis
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=3000
        )
        
        html_analysis = json.loads(response.choices[0].message.content)
        print("HTML structure analysis completed")
        
        return html_analysis
    
    def extract_components(self, visual_analysis: Dict[str, Any], html_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key components and their relationships.
        
        Args:
            visual_analysis: Visual analysis results
            html_analysis: HTML structure analysis results
            
        Returns:
            Dictionary with component extraction results
        """
        print("Step 3: Extracting key components...")
        
        # Create a detailed prompt for component extraction
        prompt = f"""You are an expert front-end developer specializing in component-based architecture.
        Extract the KEY COMPONENTS from this website based on both visual and HTML analyses.
        
        VISUAL ANALYSIS: {json.dumps(visual_analysis, indent=2)}
        
        HTML ANALYSIS: {json.dumps(html_analysis, indent=2)}
        
        Focus on:
        1. Primary components (header, navigation, product grid, sidebar, footer, etc.)
        2. Reusable UI components (cards, buttons, form elements, alerts, etc.)
        3. Layout patterns (grid systems, flexbox patterns)
        4. Component hierarchy and relationships
        5. Component states and variations (if identifiable)
        6. Data structures that would be needed for each component
        
        For each component, provide:
        - Name (descriptive identifier)
        - Type (structural, UI element, layout, etc.)
        - Purpose (what it does)
        - Visual characteristics (appearance, styling)
        - HTML structure (semantic elements, classes)
        - CSS properties (key styles needed)
        - Variants (different states or versions)
        - Responsive behavior (how it changes at different screen sizes)
        
        Format your response as structured JSON with components organized by category.
        """
        
        # Send request to OpenAI API for component extraction
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=3000
        )
        
        components = json.loads(response.choices[0].message.content)
        print("Component extraction completed")
        
        return components
    
    def create_design_system(self, visual_analysis: Dict[str, Any], components: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a detailed design system.
        
        Args:
            visual_analysis: Visual analysis results
            components: Component extraction results
            
        Returns:
            Dictionary with design system
        """
        print("Step 4: Creating design system...")
        
        # Create a detailed prompt for design system creation
        prompt = f"""You are an expert design systems architect.
        Create a COMPREHENSIVE DESIGN SYSTEM based on the visual analysis and component extraction.
        
        VISUAL ANALYSIS: {json.dumps(visual_analysis, indent=2)}
        
        COMPONENT EXTRACTION: {json.dumps(components, indent=2)}
        
        Use this custom color palette:
        - Primary color (blue): {self.colors["primary"]}
        - Secondary color (red): {self.colors["secondary"]}
        - Accent color (orange): {self.colors["accent"]}
        - Background color: {self.colors["background"]}
        - Text color: {self.colors["text"]}
        - Light text color: {self.colors["light-text"]}
        - Border color: {self.colors["border"]}
        - Success color: {self.colors["success"]}
        - Warning color: {self.colors["warning"]}
        - Error color: {self.colors["error"]}
        
        Your design system should include:
        1. Color system (primary, secondary, accent, neutral colors, utility colors)
        2. Typography (font families, sizes, weights, line heights, letter spacing)
        3. Spacing system (consistent spacing values)
        4. Grid system (columns, gutters, margins)
        5. Border system (widths, radii, styles)
        6. Shadow system (elevation levels)
        7. Component styles (buttons, cards, forms, navigation, etc.)
        8. Utility classes (if applicable)
        9. CSS variables for all values
        
        Format your response as structured JSON with all values specified precisely.
        Make sure all CSS properties use valid CSS values.
        """
        
        # Send request to OpenAI API for design system creation
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=3000
        )
        
        design_system = json.loads(response.choices[0].message.content)
        print("Design system created")
        
        return design_system
    
    def generate_html(self, html_analysis: Dict[str, Any], components: Dict[str, Any], design_system: Dict[str, Any], title: str) -> str:
        """
        Generate pixel-perfect HTML.
        
        Args:
            html_analysis: HTML structure analysis results
            components: Component extraction results
            design_system: Design system
            title: Page title
            
        Returns:
            HTML string
        """
        print("Step 5: Generating HTML...")
        
        # Create a detailed prompt for HTML generation
        prompt = f"""You are an expert HTML developer specializing in semantic, accessible, and pixel-perfect markup.
        Generate COMPLETE, PRODUCTION-READY HTML based on the analyses provided.
        
        HTML ANALYSIS: {json.dumps(html_analysis, indent=2)}
        
        COMPONENTS: {json.dumps(components, indent=2)}
        
        DESIGN SYSTEM: {json.dumps(design_system, indent=2)}
        
        PAGE TITLE: {title}
        
        Requirements:
        1. Use semantic HTML5 elements appropriately (header, nav, main, section, article, etc.)
        2. Ensure excellent accessibility (ARIA attributes, alt texts, proper heading structure)
        3. Use class names that match the design system and component structure
        4. Include a proper doctype, meta tags, and link to an external CSS file named "styles.css"
        5. Recreate the EXACT structure of the original website
        6. Include realistic content that matches the original website's structure
        7. Ensure all interactive elements (buttons, links) are properly marked up
        8. Add appropriate comments to separate major sections
        
        Format your response as clean, properly indented HTML with no explanation text - ONLY the HTML code.
        """
        
        # Send request to OpenAI API for HTML generation
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096
        )
        
        html_content = response.choices[0].message.content
        
        # Clean up the HTML if it's wrapped in markdown code blocks
        if html_content.startswith("```html"):
            html_content = html_content.split("```html")[1]
            
        if html_content.endswith("```"):
            html_content = html_content.rsplit("```", 1)[0]
        
        html_content = html_content.strip()
        
        print("HTML generation completed")
        
        return html_content
    
    def generate_css(self, html_content: str, design_system: Dict[str, Any], components: Dict[str, Any]) -> str:
        """
        Generate precisely matching CSS.
        
        Args:
            html_content: Generated HTML content
            design_system: Design system
            components: Component extraction results
            
        Returns:
            CSS string
        """
        print("Step 6: Generating CSS...")
        
        # Create a detailed prompt for CSS generation
        prompt = f"""You are an expert CSS developer specializing in efficient, maintainable, and precise styling.
        Generate COMPLETE, PRODUCTION-READY CSS based on the HTML and design system provided.
        
        HTML:
        ```html
        {html_content[:10000]}  # Limit to first 10k chars to avoid token limits
        ```
        
        DESIGN SYSTEM: {json.dumps(design_system, indent=2)}
        
        COMPONENTS: {json.dumps(components, indent=2)}
        
        Requirements:
        1. Use CSS variables for all design system values (colors, typography, spacing, etc.)
        2. Implement the exact visual styling described in the design system
        3. Ensure all components match their visual specifications
        4. Include responsive styles with appropriate media queries
        5. Use modern CSS techniques (flexbox, grid, etc.)
        6. Optimize for performance and maintainability
        7. Include appropriate comments to separate sections
        8. Ensure the CSS matches the class names used in the HTML
        9. Include reset/normalize styles at the beginning
        
        Format your response as clean, properly organized CSS with no explanation text - ONLY the CSS code.
        """
        
        # Send request to OpenAI API for CSS generation
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096
        )
        
        css_content = response.choices[0].message.content
        
        # Clean up the CSS if it's wrapped in markdown code blocks
        if css_content.startswith("```css"):
            css_content = css_content.split("```css")[1]
            
        if css_content.endswith("```"):
            css_content = css_content.rsplit("```", 1)[0]
        
        css_content = css_content.strip()
        
        print("CSS generation completed")
        
        return css_content
    
    def validate_html_css(self, html_content: str, css_content: str) -> Tuple[str, str]:
        """
        Validate and fix HTML/CSS issues to ensure they work together correctly.
        
        Args:
            html_content: Generated HTML content
            css_content: Generated CSS content
            
        Returns:
            Tuple of validated HTML and CSS strings
        """
        print("Step 7: Validating HTML and CSS...")
        
        # Create a detailed prompt for validation and fixing issues
        prompt = f"""You are an expert front-end developer specializing in debugging and fixing HTML/CSS issues.
        Review the HTML and CSS below to ensure they work together correctly.
        
        HTML:
        ```html
        {html_content[:10000]}  # Limit to first 10k chars
        ```
        
        CSS:
        ```css
        {css_content[:10000]}  # Limit to first 10k chars
        ```
        
        Tasks:
        1. Identify any mismatches between HTML class names and CSS selectors
        2. Ensure all CSS selectors target elements that exist in the HTML
        3. Fix any syntax errors in HTML or CSS
        4. Ensure CSS variables are properly defined before they're used
        5. Check for unclosed tags, invalid attributes, or improper nesting in HTML
        6. Verify media queries are properly formatted
        7. Ensure responsive designs will work correctly
        
        Return both the updated HTML and CSS as separate code blocks.
        Format your response as two separate code blocks clearly labeled "HTML" and "CSS".
        """
        
        # Send request to OpenAI API for validation
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096
        )
        
        validation_result = response.choices[0].message.content
        
        # Extract HTML and CSS from the validation result
        validated_html = html_content
        validated_css = css_content
        
        if "```html" in validation_result and "```css" in validation_result:
            # Extract HTML
            html_start = validation_result.find("```html") + 7
            html_end = validation_result.find("```", html_start)
            validated_html = validation_result[html_start:html_end].strip()
            
            # Extract CSS
            css_start = validation_result.find("```css") + 6
            css_end = validation_result.find("```", css_start)
            validated_css = validation_result[css_start:css_end].strip()
        
        print("Validation completed")
        
        return validated_html, validated_css
    
    async def generate_website(self, url: str, output_dir: str) -> Tuple[str, str]:
        """
        Generate a website from a URL using a chain-of-thought process.
        
        Args:
            url: The URL to scrape
            output_dir: Directory to save generated files
            
        Returns:
            Tuple of paths to the generated HTML and CSS files
        """
        print(f"Starting enhanced website generation for {url}...")
        
        # Step 1: Scrape the website
        scraped_data = await self.scrape_website(url)
        
        # Step 2: Analyze the screenshot
        visual_analysis = self.analyze_screenshot(scraped_data["screenshot_path"])
        
        # Step 3: Analyze the HTML structure
        html_analysis = self.analyze_html_structure(scraped_data["html"])
        
        # Step 4: Extract components
        components = self.extract_components(visual_analysis, html_analysis)
        
        # Step 5: Create design system
        design_system = self.create_design_system(visual_analysis, components)
        
        # Step 6: Generate HTML
        html_content = self.generate_html(
            html_analysis, 
            components, 
            design_system, 
            scraped_data.get("title", "Generated Website")
        )
        
        # Step 7: Generate CSS
        css_content = self.generate_css(html_content, design_system, components)
        
        # Step 8: Validate HTML and CSS
        html_content, css_content = self.validate_html_css(html_content, css_content)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save HTML and CSS files
        html_path = os.path.join(output_dir, "index.html")
        css_path = os.path.join(output_dir, "styles.css")
        
        with open(html_path, "w") as f:
            f.write(html_content)
            
        with open(css_path, "w") as f:
            f.write(css_content)
            
        print(f"Files saved to {output_dir}")
        
        return html_path, css_path


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate a website with enhanced chain-of-thought process.")
    parser.add_argument("--url", default="https://books.toscrape.com/",
                        help="URL to scrape (default: https://books.toscrape.com/)")
    parser.add_argument("--output", default="generated/enhanced",
                        help="Directory to save generated files (default: generated/enhanced)")
    
    args = parser.parse_args()
    
    # Resolve paths relative to the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(backend_dir, args.output)
    
    # Create the generator and run it
    generator = EnhancedWebsiteGenerator()
    html_path, css_path = await generator.generate_website(args.url, output_dir)
    
    print("\nDone!")
    print(f"Generated HTML: {html_path}")
    print(f"Generated CSS: {css_path}")
    print(f"Open in browser with: open {html_path}")

if __name__ == "__main__":
    asyncio.run(main())
