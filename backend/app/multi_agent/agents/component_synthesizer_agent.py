import os
import re
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .base_agent import BaseAgent


class ComponentSynthesizerAgent(BaseAgent):
    """
    Agent responsible for synthesizing website components.
    
    This agent generates HTML, CSS, and component definitions based on the
    document structure, design system, and layout specifications.
    """
    
    def __init__(self, **kwargs):
        """Initialize the Component Synthesizer Agent with specific configurations."""
        super().__init__(**kwargs)
        
        # Configure output
        self.component_dir = kwargs.get("component_dir", "components")
        self.output_dir = kwargs.get("output_dir", "generated")
        
        # Configure component generation
        self.typescript = kwargs.get("typescript", True)
        self.react_version = kwargs.get("react_version", "18")
        self.css_framework = kwargs.get("css_framework", "none")  # none, tailwind, bootstrap
        
        # Ensure output directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, self.component_dir), exist_ok=True)
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and generate website components.
        
        Args:
            input_data: Dictionary containing document structure, design system, and layout
            
        Returns:
            Dictionary containing generated HTML, CSS, and component definitions
        """
        document_structure = input_data.get("document_structure", {})
        component_mapping = input_data.get("component_mapping", {})
        design_system = input_data.get("design_system", {})
        grid_specification = input_data.get("grid_specification", {})
        responsive_layouts = input_data.get("responsive_layouts", {})
        
        if self.debug:
            print("[ComponentSynthesizerAgent] Generating components")
        
        # Generate CSS for the design system
        design_system_css = await self._generate_design_system_css(design_system)
        
        # Generate components
        component_definitions = await self._generate_component_definitions(
            document_structure, component_mapping, design_system, grid_specification
        )
        
        # Generate layout component
        layout_component = await self._generate_layout_component(
            grid_specification, responsive_layouts, component_definitions
        )
        
        # Generate HTML output
        html_output = await self._generate_html_output(
            document_structure, component_definitions, layout_component
        )
        
        # Generate CSS output
        css_output = await self._generate_css_output(
            design_system_css, grid_specification.get("layout_css", "")
        )
        
        return {
            "html_output": html_output,
            "css_output": css_output,
            "component_definitions": component_definitions,
            "layout_component": layout_component,
            "design_system_css": design_system_css
        }
    
    async def _generate_design_system_css(self, design_system: Dict[str, Any]) -> str:
        """
        Generate CSS for the design system.
        
        Args:
            design_system: Design system definition
            
        Returns:
            CSS string for the design system
        """
        css = []
        
        # Get CSS variables from design system
        css_variables = design_system.get("css_variables", {})
        
        # Root variables
        css.append("/* Design System CSS Variables */")
        css.append(":root {")
        
        # Add color variables
        css.append("  /* Colors */")
        for name, value in css_variables.items():
            if name.startswith("--color-"):
                css.append(f"  {name}: {value};")
        
        # Add typography variables
        css.append("\n  /* Typography */")
        for name, value in css_variables.items():
            if name.startswith("--font-"):
                css.append(f"  {name}: {value};")
        
        # Add spacing variables
        css.append("\n  /* Spacing */")
        for name, value in css_variables.items():
            if name.startswith("--space-") or name.startswith("--container-"):
                css.append(f"  {name}: {value};")
        
        css.append("}")
        
        # Add base typography styles
        css.append("\n/* Base Typography */")
        css.append("body {")
        css.append("  font-family: var(--font-body);")
        css.append("  font-size: var(--font-size-1);")
        css.append("  line-height: var(--line-height-normal);")
        css.append("  color: var(--color-text, #333333);")
        css.append("  background-color: var(--color-background, #ffffff);")
        css.append("}")
        
        css.append("h1, h2, h3, h4, h5, h6 {")
        css.append("  font-family: var(--font-heading);")
        css.append("  margin-top: var(--space-4);")
        css.append("  margin-bottom: var(--space-2);")
        css.append("  font-weight: var(--font-weight-bold);")
        css.append("  line-height: var(--line-height-tight);")
        css.append("}")
        
        css.append("h1 {")
        css.append("  font-size: var(--font-size-3);")
        css.append("}")
        
        css.append("h2 {")
        css.append("  font-size: var(--font-size-2);")
        css.append("}")
        
        css.append("h3 {")
        css.append("  font-size: var(--font-size-1p5);")
        css.append("}")
        
        css.append("h4 {")
        css.append("  font-size: var(--font-size-1p25);")
        css.append("}")
        
        css.append("p {")
        css.append("  margin-top: 0;")
        css.append("  margin-bottom: var(--space-1);")
        css.append("}")
        
        css.append("a {")
        css.append("  color: var(--color-primary, #0070f3);")
        css.append("  text-decoration: none;")
        css.append("}")
        
        css.append("a:hover {")
        css.append("  text-decoration: underline;")
        css.append("}")
        
        # Add utility classes
        css.append("\n/* Utility classes */")
        css.append(".container {")
        css.append("  width: 100%;")
        css.append("  max-width: var(--container-xl, 1280px);")
        css.append("  margin-left: auto;")
        css.append("  margin-right: auto;")
        css.append("  padding-left: var(--space-2);")
        css.append("  padding-right: var(--space-2);")
        css.append("}")
        
        css.append("@media (min-width: 768px) {")
        css.append("  .container {")
        css.append("    padding-left: var(--space-4);")
        css.append("    padding-right: var(--space-4);")
        css.append("  }")
        css.append("}")
        
        # Add button styles
        css.append("\n/* Button styles */")
        css.append(".btn {")
        css.append("  display: inline-block;")
        css.append("  font-weight: var(--font-weight-medium);")
        css.append("  text-align: center;")
        css.append("  white-space: nowrap;")
        css.append("  vertical-align: middle;")
        css.append("  user-select: none;")
        css.append("  border: 1px solid transparent;")
        css.append("  padding: var(--space-1) var(--space-2);")
        css.append("  font-size: var(--font-size-1);")
        css.append("  line-height: var(--line-height-normal);")
        css.append("  border-radius: var(--space-0p5);")
        css.append("  transition: all 0.15s ease-in-out;")
        css.append("  cursor: pointer;")
        css.append("}")
        
        css.append(".btn-primary {")
        css.append("  background-color: var(--color-primary, #0070f3);")
        css.append("  color: white;")
        css.append("}")
        
        css.append(".btn-primary:hover {")
        css.append("  background-color: var(--color-primary-600, #0058cc);")
        css.append("}")
        
        css.append(".btn-secondary {")
        css.append("  background-color: var(--color-secondary, #6c757d);")
        css.append("  color: white;")
        css.append("}")
        
        css.append(".btn-secondary:hover {")
        css.append("  background-color: var(--color-secondary-600, #545b62);")
        css.append("}")
        
        # Join all CSS lines
        return "\n".join(css)
    
    async def _generate_component_definitions(
        self,
        document_structure: Dict[str, Any],
        component_mapping: Dict[str, List[Dict[str, Any]]],
        design_system: Dict[str, Any],
        grid_specification: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate component definitions.
        
        Args:
            document_structure: Document structure from semantic parser
            component_mapping: Component mapping from semantic parser
            design_system: Design system definition
            grid_specification: Grid specification
            
        Returns:
            Dictionary mapping component names to definitions
        """
        component_definitions = {}
        
        # Generate base components
        component_definitions["Header"] = await self._generate_header_component(
            component_mapping.get("header", [])
        )
        
        component_definitions["Navigation"] = await self._generate_navigation_component(
            component_mapping.get("navigation", [])
        )
        
        component_definitions["Footer"] = await self._generate_footer_component(
            component_mapping.get("footer", [])
        )
        
        component_definitions["Sidebar"] = await self._generate_sidebar_component(
            component_mapping.get("sidebar", [])
        )
        
        # Generate content components
        component_definitions["Hero"] = await self._generate_hero_component(
            component_mapping.get("hero", [])
        )
        
        component_definitions["CardGrid"] = await self._generate_card_grid_component(
            component_mapping.get("card", [])
        )
        
        component_definitions["FeatureSection"] = await self._generate_feature_section_component(
            component_mapping.get("feature", [])
        )
        
        component_definitions["TestimonialSection"] = await self._generate_testimonial_section_component(
            component_mapping.get("testimonial", [])
        )
        
        component_definitions["CTASection"] = await self._generate_cta_section_component(
            component_mapping.get("cta", [])
        )
        
        # Generate layout components
        component_definitions["Layout"] = await self._generate_layout_component(
            grid_specification, {}, component_definitions
        )
        
        return component_definitions
    
    async def _generate_header_component(
        self, header_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate header component.
        
        Args:
            header_components: List of header components
            
        Returns:
            Header component definition
        """
        has_logo = False
        has_navigation = False
        classes = []
        
        if header_components:
            header = header_components[0]  # Use the first header
            has_logo = header.get("has_logo", False)
            has_navigation = header.get("has_navigation", False)
            classes = header.get("classes", [])
        
        # Generate JSX code
        jsx = []
        jsx.append('<header className="header">')
        jsx.append('  <div className="container">')
        jsx.append('    <div className="header-content">')
        
        if has_logo:
            jsx.append('      <div className="logo">')
            jsx.append('        <a href="/">')
            jsx.append('          <h1>Company Name</h1>')
            jsx.append('        </a>')
            jsx.append('      </div>')
        
        if has_navigation:
            jsx.append('      <nav className="main-nav">')
            jsx.append('        <ul>')
            jsx.append('          <li><a href="/">Home</a></li>')
            jsx.append('          <li><a href="/about">About</a></li>')
            jsx.append('          <li><a href="/services">Services</a></li>')
            jsx.append('          <li><a href="/contact">Contact</a></li>')
            jsx.append('        </ul>')
            jsx.append('      </nav>')
        
        jsx.append('    </div>')
        jsx.append('  </div>')
        jsx.append('</header>')
        
        # Generate CSS
        css = []
        css.append('.header {')
        css.append('  padding: var(--space-2) 0;')
        css.append('  background-color: var(--color-background, #ffffff);')
        css.append('  border-bottom: 1px solid var(--color-border, #eaeaea);')
        css.append('}')
        
        css.append('.header-content {')
        css.append('  display: flex;')
        css.append('  flex-direction: column;')
        css.append('  justify-content: space-between;')
        css.append('  align-items: center;')
        css.append('  gap: var(--space-2);')
        css.append('}')
        
        css.append('@media (min-width: 768px) {')
        css.append('  .header-content {')
        css.append('    flex-direction: row;')
        css.append('  }')
        css.append('}')
        
        css.append('.logo {')
        css.append('  font-size: var(--font-size-1p25);')
        css.append('  font-weight: var(--font-weight-bold);')
        css.append('}')
        
        css.append('.logo a {')
        css.append('  text-decoration: none;')
        css.append('  color: var(--color-text, #333333);')
        css.append('}')
        
        css.append('.logo h1 {')
        css.append('  margin: 0;')
        css.append('  font-size: var(--font-size-1p5);')
        css.append('}')
        
        css.append('.main-nav ul {')
        css.append('  display: flex;')
        css.append('  list-style: none;')
        css.append('  padding: 0;')
        css.append('  margin: 0;')
        css.append('  gap: var(--space-4);')
        css.append('}')
        
        css.append('.main-nav a {')
        css.append('  text-decoration: none;')
        css.append('  color: var(--color-text, #333333);')
        css.append('  font-weight: var(--font-weight-medium);')
        css.append('}')
        
        css.append('.main-nav a:hover {')
        css.append('  color: var(--color-primary, #0070f3);')
        css.append('}')
        
        # Generate React component
        react = []
        if self.typescript:
            react.append('import React from "react";')
            react.append('')
            react.append('interface HeaderProps {')
            react.append('  className?: string;')
            react.append('}')
            react.append('')
            react.append('const Header: React.FC<HeaderProps> = ({ className }) => {')
        else:
            react.append('import React from "react";')
            react.append('')
            react.append('const Header = ({ className }) => {')
        
        react.append('  return (')
        react.append('    <header className={`header ${className || ""}`}>')
        react.append('      <div className="container">')
        react.append('        <div className="header-content">')
        
        if has_logo:
            react.append('          <div className="logo">')
            react.append('            <a href="/">')
            react.append('              <h1>Company Name</h1>')
            react.append('            </a>')
            react.append('          </div>')
        
        if has_navigation:
            react.append('          <nav className="main-nav">')
            react.append('            <ul>')
            react.append('              <li><a href="/">Home</a></li>')
            react.append('              <li><a href="/about">About</a></li>')
            react.append('              <li><a href="/services">Services</a></li>')
            react.append('              <li><a href="/contact">Contact</a></li>')
            react.append('            </ul>')
            react.append('          </nav>')
        
        react.append('        </div>')
        react.append('      </div>')
        react.append('    </header>')
        react.append('  );')
        react.append('};')
        react.append('')
        react.append('export default Header;')
        
        return {
            "name": "Header",
            "jsx": "\n".join(jsx),
            "css": "\n".join(css),
            "react": "\n".join(react),
            "has_logo": has_logo,
            "has_navigation": has_navigation
        }
    
    async def _generate_navigation_component(
        self, navigation_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate navigation component.
        
        Args:
            navigation_components: List of navigation components
            
        Returns:
            Navigation component definition
        """
        horizontal = True
        link_count = 4  # Default
        classes = []
        
        if navigation_components:
            nav = navigation_components[0]  # Use the first navigation
            horizontal = nav.get("horizontal", True)
            link_count = nav.get("link_count", 4)
            classes = nav.get("classes", [])
        
        # Limit link count to a reasonable number
        link_count = min(max(link_count, 2), 6)
        
        # Generate JSX code
        jsx = []
        jsx.append('<nav className="navigation">')
        jsx.append('  <ul>')
        jsx.append('    <li><a href="/">Home</a></li>')
        jsx.append('    <li><a href="/about">About</a></li>')
        
        if link_count > 2:
            jsx.append('    <li><a href="/services">Services</a></li>')
        
        if link_count > 3:
            jsx.append('    <li><a href="/products">Products</a></li>')
        
        if link_count > 4:
            jsx.append('    <li><a href="/blog">Blog</a></li>')
        
        if link_count > 5:
            jsx.append('    <li><a href="/contact">Contact</a></li>')
            
        jsx.append('  </ul>')
        jsx.append('</nav>')
        
        # Generate CSS
        css = []
        css.append('.navigation ul {')
        css.append('  list-style: none;')
        css.append('  padding: 0;')
        css.append('  margin: 0;')
        
        if horizontal:
            css.append('  display: flex;')
            css.append('  flex-wrap: wrap;')
            css.append('  gap: var(--space-4);')
        else:
            css.append('  display: flex;')
            css.append('  flex-direction: column;')
            css.append('  gap: var(--space-2);')
        
        css.append('}')
        
        css.append('.navigation a {')
        css.append('  text-decoration: none;')
        css.append('  color: var(--color-text, #333333);')
        css.append('  font-weight: var(--font-weight-medium);')
        css.append('  display: block;')
        
        if not horizontal:
            css.append('  padding: var(--space-1) 0;')
            
        css.append('}')
        
        css.append('.navigation a:hover {')
        css.append('  color: var(--color-primary, #0070f3);')
        css.append('}')
        
        # Generate React component
        react = []
        if self.typescript:
            react.append('import React from "react";')
            react.append('')
            react.append('interface NavigationProps {')
            react.append('  className?: string;')
            react.append('  horizontal?: boolean;')
            react.append('}')
            react.append('')
            react.append('const Navigation: React.FC<NavigationProps> = ({ className, horizontal = true }) => {')
        else:
            react.append('import React from "react";')
            react.append('')
            react.append('const Navigation = ({ className, horizontal = true }) => {')
        
        react.append('  return (')
        react.append('    <nav className={`navigation ${horizontal ? "horizontal" : "vertical"} ${className || ""}`}>')
        react.append('      <ul>')
        react.append('        <li><a href="/">Home</a></li>')
        react.append('        <li><a href="/about">About</a></li>')
        
        if link_count > 2:
            react.append('        <li><a href="/services">Services</a></li>')
        
        if link_count > 3:
            react.append('        <li><a href="/products">Products</a></li>')
        
        if link_count > 4:
            react.append('        <li><a href="/blog">Blog</a></li>')
        
        if link_count > 5:
            react.append('        <li><a href="/contact">Contact</a></li>')
            
        react.append('      </ul>')
        react.append('    </nav>')
        react.append('  );')
        react.append('};')
        react.append('')
        react.append('export default Navigation;')
        
        return {
            "name": "Navigation",
            "jsx": "\n".join(jsx),
            "css": "\n".join(css),
            "react": "\n".join(react),
            "horizontal": horizontal,
            "link_count": link_count
        }
    
    async def _generate_footer_component(
        self, footer_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate footer component.
        
        Args:
            footer_components: List of footer components
            
        Returns:
            Footer component definition
        """
        has_links = False
        has_social = False
        classes = []
        
        if footer_components:
            footer = footer_components[0]  # Use the first footer
            has_links = footer.get("has_links", False)
            has_social = footer.get("has_social", False)
            classes = footer.get("classes", [])
        
        # Generate JSX code
        jsx = []
        jsx.append('<footer className="footer">')
        jsx.append('  <div className="container">')
        jsx.append('    <div className="footer-content">')
        
        if has_links:
            jsx.append('      <div className="footer-links">')
            jsx.append('        <div className="footer-column">')
            jsx.append('          <h3>Company</h3>')
            jsx.append('          <ul>')
            jsx.append('            <li><a href="/about">About</a></li>')
            jsx.append('            <li><a href="/careers">Careers</a></li>')
            jsx.append('            <li><a href="/contact">Contact</a></li>')
            jsx.append('          </ul>')
            jsx.append('        </div>')
            jsx.append('        <div className="footer-column">')
            jsx.append('          <h3>Resources</h3>')
            jsx.append('          <ul>')
            jsx.append('            <li><a href="/blog">Blog</a></li>')
            jsx.append('            <li><a href="/docs">Documentation</a></li>')
            jsx.append('            <li><a href="/guides">Guides</a></li>')
            jsx.append('          </ul>')
            jsx.append('        </div>')
            jsx.append('        <div className="footer-column">')
            jsx.append('          <h3>Legal</h3>')
            jsx.append('          <ul>')
            jsx.append('            <li><a href="/privacy">Privacy Policy</a></li>')
            jsx.append('            <li><a href="/terms">Terms of Service</a></li>')
            jsx.append('          </ul>')
            jsx.append('        </div>')
            jsx.append('      </div>')
        
        jsx.append('      <div className="copyright">')
        jsx.append('        <p>© 2025 Company Name. All rights reserved.</p>')
        jsx.append('      </div>')
        
        jsx.append('    </div>')
        jsx.append('  </div>')
        jsx.append('</footer>')
        
        # Generate CSS
        css = []
        css.append('.footer {')
        css.append('  padding: var(--space-6) 0;')
        css.append('  background-color: var(--color-light, #f8f9fa);')
        css.append('  border-top: 1px solid var(--color-border, #eaeaea);')
        css.append('}')
        
        if has_links:
            css.append('.footer-links {')
            css.append('  display: grid;')
            css.append('  grid-template-columns: 1fr;')
            css.append('  gap: var(--space-4);')
            css.append('  margin-bottom: var(--space-4);')
            css.append('}')
            
            css.append('@media (min-width: 768px) {')
            css.append('  .footer-links {')
            css.append('    grid-template-columns: repeat(3, 1fr);')
            css.append('  }')
            css.append('}')
            
            css.append('.footer-column h3 {')
            css.append('  font-size: var(--font-size-1);')
            css.append('  margin-bottom: var(--space-2);')
            css.append('}')
            
            css.append('.footer-column ul {')
            css.append('  list-style: none;')
            css.append('  padding: 0;')
            css.append('  margin: 0;')
            css.append('}')
            
            css.append('.footer-column li {')
            css.append('  margin-bottom: var(--space-1);')
            css.append('}')
            
            css.append('.footer-column a {')
            css.append('  text-decoration: none;')
            css.append('  color: var(--color-text, #666666);')
            css.append('  font-size: var(--font-size-0p875);')
            css.append('}')
        
        css.append('.copyright {')
        css.append('  text-align: center;')
        css.append('  font-size: var(--font-size-0p875);')
        css.append('  color: var(--color-text, #666666);')
        css.append('}')
        
        # Generate React component
        react = []
        if self.typescript:
            react.append('import React from "react";')
            react.append('')
            react.append('interface FooterProps {')
            react.append('  className?: string;')
            react.append('}')
            react.append('')
            react.append('const Footer: React.FC<FooterProps> = ({ className }) => {')
        else:
            react.append('import React from "react";')
            react.append('')
            react.append('const Footer = ({ className }) => {')
        
        react.append('  return (')
        react.append('    <footer className={`footer ${className || ""}`}>')
        react.append('      <div className="container">')
        react.append('        <div className="footer-content">')
        
        if has_links:
            react.append('          <div className="footer-links">')
            react.append('            <div className="footer-column">')
            react.append('              <h3>Company</h3>')
            react.append('              <ul>')
            react.append('                <li><a href="/about">About</a></li>')
            react.append('                <li><a href="/careers">Careers</a></li>')
            react.append('                <li><a href="/contact">Contact</a></li>')
            react.append('              </ul>')
            react.append('            </div>')
            react.append('            <div className="footer-column">')
            react.append('              <h3>Resources</h3>')
            react.append('              <ul>')
            react.append('                <li><a href="/blog">Blog</a></li>')
            react.append('                <li><a href="/docs">Documentation</a></li>')
            react.append('                <li><a href="/guides">Guides</a></li>')
            react.append('              </ul>')
            react.append('            </div>')
            react.append('            <div className="footer-column">')
            react.append('              <h3>Legal</h3>')
            react.append('              <ul>')
            react.append('                <li><a href="/privacy">Privacy Policy</a></li>')
            react.append('                <li><a href="/terms">Terms of Service</a></li>')
            react.append('              </ul>')
            react.append('            </div>')
            react.append('          </div>')
        
        react.append('          <div className="copyright">')
        react.append('            <p>© 2025 Company Name. All rights reserved.</p>')
        react.append('          </div>')
        react.append('        </div>')
        react.append('      </div>')
        react.append('    </footer>')
        react.append('  );')
        react.append('};')
        react.append('')
        react.append('export default Footer;')
        
        return {
            "name": "Footer",
            "jsx": "\n".join(jsx),
            "css": "\n".join(css),
            "react": "\n".join(react),
            "has_links": has_links,
            "has_social": has_social
        }
    
    async def _generate_sidebar_component(
        self, sidebar_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate sidebar component."""
        return {
            "name": "Sidebar",
            "jsx": "<div className='sidebar'>Sidebar</div>",
            "css": ".sidebar { padding: var(--space-4); }",
            "react": "const Sidebar = () => <div className='sidebar'>Sidebar</div>; export default Sidebar;"
        }
    
    async def _generate_hero_component(
        self, hero_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate hero component."""
        return {
            "name": "Hero",
            "jsx": "<div className='hero'>Hero</div>",
            "css": ".hero { padding: var(--space-4); }",
            "react": "const Hero = () => <div className='hero'>Hero</div>; export default Hero;"
        }
    
    async def _generate_card_grid_component(
        self, card_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate card grid component."""
        return {
            "name": "CardGrid",
            "jsx": "<div className='card-grid'>Card Grid</div>",
            "css": ".card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: var(--space-4); }",
            "react": "const CardGrid = () => <div className='card-grid'>Card Grid</div>; export default CardGrid;"
        }
    
    async def _generate_feature_section_component(
        self, feature_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate feature section component."""
        return {
            "name": "FeatureSection",
            "jsx": "<div className='feature-section'>Feature Section</div>",
            "css": ".feature-section { padding: var(--space-4); }",
            "react": "const FeatureSection = () => <div className='feature-section'>Feature Section</div>; export default FeatureSection;"
        }
    
    async def _generate_testimonial_section_component(
        self, testimonial_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate testimonial section component."""
        return {
            "name": "TestimonialSection",
            "jsx": "<div className='testimonial-section'>Testimonial Section</div>",
            "css": ".testimonial-section { padding: var(--space-4); }",
            "react": "const TestimonialSection = () => <div className='testimonial-section'>Testimonial Section</div>; export default TestimonialSection;"
        }
    
    async def _generate_cta_section_component(
        self, cta_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate CTA section component."""
        return {
            "name": "CTASection",
            "jsx": "<div className='cta-section'>CTA Section</div>",
            "css": ".cta-section { padding: var(--space-4); }",
            "react": "const CTASection = () => <div className='cta-section'>CTA Section</div>; export default CTASection;"
        }
    
    async def _generate_layout_component(
        self,
        grid_specification: Dict[str, Any],
        responsive_layouts: Dict[str, Dict[str, Any]],
        component_definitions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate layout component."""
        layout_css = grid_specification.get("layout_css", "")
        return {
            "name": "Layout",
            "jsx": "<div className='layout'>Layout</div>",
            "css": layout_css or ".layout { display: grid; grid-template-columns: repeat(12, 1fr); }",
            "react": "const Layout = ({children}) => <div className='layout'>{children}</div>; export default Layout;"
        }
    
    async def _generate_html_output(
        self,
        document_structure: Dict[str, Any],
        component_definitions: Dict[str, Dict[str, Any]],
        layout_component: Dict[str, Any]
    ) -> str:
        """
        Generate HTML output.
        
        Args:
            document_structure: Document structure
            component_definitions: Component definitions
            layout_component: Layout component
            
        Returns:
            HTML output string
        """
        html = []
        
        # DOCTYPE and HTML opening tags
        html.append('<!DOCTYPE html>')
        html.append('<html lang="en">')
        
        # Head section
        html.append('<head>')
        html.append('  <meta charset="UTF-8">')
        html.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html.append('  <title>Generated Website</title>')
        html.append('  <link rel="stylesheet" href="styles.css">')
        html.append('</head>')
        
        # Body section
        html.append('<body>')
        
        # Header
        if "Header" in component_definitions:
            html.append(component_definitions["Header"]["jsx"])
        
        # Main content
        html.append('<main>')
        
        # Hero section
        if "Hero" in component_definitions:
            html.append(component_definitions["Hero"]["jsx"])
        
        # Feature section
        if "FeatureSection" in component_definitions:
            html.append(component_definitions["FeatureSection"]["jsx"])
        
        # Card grid
        if "CardGrid" in component_definitions:
            html.append(component_definitions["CardGrid"]["jsx"])
        
        # Testimonial section
        if "TestimonialSection" in component_definitions:
            html.append(component_definitions["TestimonialSection"]["jsx"])
        
        # CTA section
        if "CTASection" in component_definitions:
            html.append(component_definitions["CTASection"]["jsx"])
        
        html.append('</main>')
        
        # Footer
        if "Footer" in component_definitions:
            html.append(component_definitions["Footer"]["jsx"])
        
        # Closing tags
        html.append('</body>')
        html.append('</html>')
        
        return "\n".join(html)
    
    async def _generate_css_output(self, design_system_css: str, layout_css: str) -> str:
        """
        Generate CSS output.
        
        Args:
            design_system_css: Design system CSS
            layout_css: Layout CSS
            
        Returns:
            CSS output string
        """
        css = []
        
        # Add reset CSS
        css.append('/* Reset CSS */')
        css.append('*, *::before, *::after {')
        css.append('  box-sizing: border-box;')
        css.append('}')
        
        css.append('body, h1, h2, h3, h4, h5, h6, p, figure, blockquote, dl, dd {')
        css.append('  margin: 0;')
        css.append('}')
        
        css.append('html:focus-within {')
        css.append('  scroll-behavior: smooth;')
        css.append('}')
        
        css.append('body {')
        css.append('  min-height: 100vh;')
        css.append('  text-rendering: optimizeSpeed;')
        css.append('  line-height: 1.5;')
        css.append('}')
        
        css.append('img, picture {')
        css.append('  max-width: 100%;')
        css.append('  display: block;')
        css.append('}')
        
        # Add design system CSS
        css.append('\n/* Design System */')
        css.append(design_system_css)
        
        # Add layout CSS
        if layout_css:
            css.append('\n/* Layout */')
            css.append(layout_css)
        
        return "\n".join(css)

