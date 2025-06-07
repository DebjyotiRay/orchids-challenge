import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urlparse

from .base_agent import BaseAgent


class SemanticParserAgent(BaseAgent):
    """
    Agent responsible for semantic parsing of website content.
    
    This agent analyzes the DOM structure and content to identify semantic components,
    layout patterns, and content relationships to generate a structured representation
    of the website's semantic organization.
    """
    
    def __init__(self, **kwargs):
        """Initialize the Semantic Parser Agent with specific configurations."""
        super().__init__(**kwargs)
        
        # Configuration options
        self.analyze_text_semantics = kwargs.get("analyze_text_semantics", True)
        self.analyze_component_patterns = kwargs.get("analyze_component_patterns", True)
        self.analyze_heading_structure = kwargs.get("analyze_heading_structure", True)
        self.analyze_navigation = kwargs.get("analyze_navigation", True)
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and parse website semantic structure.
        
        Args:
            input_data: Dictionary containing the scraped website data
            
        Returns:
            Dictionary containing semantic structure and component mapping
        """
        html = input_data.get("html", "")
        markdown = input_data.get("markdown", "")
        dom_structure = input_data.get("dom_structure", {})
        headings = input_data.get("headings", [])
        
        if not html:
            raise ValueError("HTML content is required")
            
        if self.debug:
            print("[SemanticParserAgent] Analyzing semantic structure")
        
        # Parse HTML content
        soup = BeautifulSoup(html, "html.parser")
        
        # Get page metadata
        meta_info = await self._extract_meta_info(soup, input_data.get("meta_info", {}))
        
        # Analyze document structure
        document_structure = await self._analyze_document_structure(soup, headings, markdown)
        
        # Identify semantic components
        component_mapping = await self._identify_components(soup, document_structure)
        
        # Identify layout type
        layout_type = await self._identify_layout_type(soup, document_structure, component_mapping)
        
        return {
            "meta_info": meta_info,
            "document_structure": document_structure,
            "component_mapping": component_mapping,
            "layout_type": layout_type
        }
    
    async def _extract_meta_info(
        self, soup: BeautifulSoup, existing_meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract and enhance metadata information.
        
        Args:
            soup: BeautifulSoup object of the HTML
            existing_meta: Existing metadata from the scraper
            
        Returns:
            Enhanced metadata dictionary
        """
        meta_info = existing_meta.copy()
        
        # Extract title if not already present
        if "title" not in meta_info:
            title_tag = soup.find("title")
            if title_tag:
                meta_info["title"] = title_tag.text.strip()
                
        # Extract description if not already present
        if "description" not in meta_info:
            desc_tag = soup.find("meta", attrs={"name": "description"})
            if desc_tag:
                meta_info["description"] = desc_tag.get("content", "")
                
        # Extract Open Graph metadata
        for prop in ["title", "description", "image", "url", "type"]:
            og_key = f"og:{prop}"
            if og_key not in meta_info:
                og_tag = soup.find("meta", attrs={"property": og_key})
                if og_tag:
                    meta_info[og_key] = og_tag.get("content", "")
                    
        # Extract Twitter Card metadata
        for name in ["card", "title", "description", "image"]:
            twitter_key = f"twitter:{name}"
            if twitter_key not in meta_info:
                twitter_tag = soup.find("meta", attrs={"name": twitter_key})
                if twitter_tag:
                    meta_info[twitter_key] = twitter_tag.get("content", "")
                    
        # Extract canonical URL
        if "canonical" not in meta_info:
            canonical_tag = soup.find("link", attrs={"rel": "canonical"})
            if canonical_tag:
                meta_info["canonical"] = canonical_tag.get("href", "")
                
        # Extract language
        if "language" not in meta_info:
            html_tag = soup.find("html")
            if html_tag and html_tag.get("lang"):
                meta_info["language"] = html_tag.get("lang")
                
        return meta_info
    
    async def _analyze_document_structure(
        self, soup: BeautifulSoup, headings: List[Dict[str, Any]], markdown: str
    ) -> Dict[str, Any]:
        """
        Analyze the document structure.
        
        Args:
            soup: BeautifulSoup object of the HTML
            headings: List of headings from markdown
            markdown: Markdown content
            
        Returns:
            Document structure dictionary
        """
        # Initialize document structure
        document_structure = {
            "headings": headings,
            "sections": [],
            "content_density": {}
        }
        
        # Analyze heading structure
        if self.analyze_heading_structure and not headings:
            # Extract headings from HTML if not provided
            html_headings = []
            for level in range(1, 7):
                for h_tag in soup.find_all(f"h{level}"):
                    html_headings.append({
                        "level": level,
                        "text": h_tag.get_text(strip=True)
                    })
            document_structure["headings"] = html_headings
            
        # Identify sections based on headings
        sections = []
        current_section = {"title": "", "level": 0, "content": "", "subsections": []}
        
        # Use headings to detect sections
        headings = document_structure["headings"]
        if headings:
            for i, heading in enumerate(headings):
                if heading["level"] == 1:
                    # Top-level section
                    if current_section["title"]:
                        sections.append(current_section)
                    current_section = {
                        "title": heading["text"],
                        "level": heading["level"],
                        "content": "",
                        "subsections": []
                    }
                elif heading["level"] > 1:
                    # Subsection
                    subsection = {
                        "title": heading["text"],
                        "level": heading["level"],
                        "content": ""
                    }
                    current_section["subsections"].append(subsection)
            
            # Add the last section
            if current_section["title"]:
                sections.append(current_section)
                
        document_structure["sections"] = sections
        
        # Analyze content density
        content_density = {}
        
        # Calculate text length in different parts of the document
        for tag_name in ["p", "div", "section", "article", "header", "footer", "main", "aside"]:
            total_text = 0
            elements_count = 0
            
            for tag in soup.find_all(tag_name):
                text_length = len(tag.get_text(strip=True))
                total_text += text_length
                elements_count += 1
                
            if elements_count > 0:
                content_density[tag_name] = {
                    "total_text": total_text,
                    "count": elements_count,
                    "average": total_text / elements_count
                }
                
        document_structure["content_density"] = content_density
        
        return document_structure
    
    async def _identify_components(
        self, soup: BeautifulSoup, document_structure: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify semantic components in the document.
        
        Args:
            soup: BeautifulSoup object of the HTML
            document_structure: Document structure dictionary
            
        Returns:
            Component mapping dictionary
        """
        component_mapping = {
            "header": [],
            "footer": [],
            "navigation": [],
            "sidebar": [],
            "hero": [],
            "card": [],
            "feature": [],
            "testimonial": [],
            "cta": [],
            "form": [],
            "gallery": []
        }
        
        # Identify header
        header_elements = soup.find_all(["header", "div"], class_=lambda c: c and any(x in str(c) for x in ["header", "top-bar"]))
        if not header_elements:
            # Try to identify header by position
            first_elements = list(soup.body.children if soup.body else [])
            for element in first_elements[:3]:  # Check first 3 elements
                if element.name and element.name not in ["script", "style", "meta", "link"]:
                    header_elements = [element]
                    break
                    
        # Process identified headers
        for header in header_elements:
            has_logo = bool(header.find(["img", "svg"]) or header.find(class_=lambda c: c and "logo" in str(c)))
            has_navigation = bool(header.find(["nav", "ul", "ol"]))
            
            component_mapping["header"].append({
                "element": str(header.name),
                "has_logo": has_logo,
                "has_navigation": has_navigation,
                "classes": header.get("class", []),
                "text_length": len(header.get_text(strip=True))
            })
            
        # Identify footer
        footer_elements = soup.find_all(["footer", "div"], class_=lambda c: c and any(x in str(c) for x in ["footer", "bottom"]))
        if not footer_elements:
            # Try to identify footer by position
            last_elements = list(soup.body.children if soup.body else [])
            for element in reversed(last_elements[:3]):  # Check last 3 elements
                if element.name and element.name not in ["script", "style", "meta", "link"]:
                    footer_elements = [element]
                    break
                    
        # Process identified footers
        for footer in footer_elements:
            has_links = bool(footer.find_all("a"))
            has_social = bool(footer.find(class_=lambda c: c and any(x in str(c) for x in ["social", "twitter", "facebook", "linkedin"])))
            
            component_mapping["footer"].append({
                "element": str(footer.name),
                "has_links": has_links,
                "has_social": has_social,
                "classes": footer.get("class", []),
                "text_length": len(footer.get_text(strip=True))
            })
            
        # Identify navigation
        nav_elements = soup.find_all(["nav", "ul"], class_=lambda c: c and any(x in str(c) for x in ["nav", "menu"]))
        
        # Process identified navigation elements
        for nav in nav_elements:
            links = nav.find_all("a")
            horizontal = True
            
            # Check if navigation is horizontal or vertical
            if nav.name == "ul":
                list_items = nav.find_all("li", recursive=False)
                if list_items:
                    # Check if list items are block elements
                    first_li = list_items[0]
                    comp_style = first_li.get("style", "")
                    if "display: block" in comp_style or "flex-direction: column" in comp_style:
                        horizontal = False
            
            component_mapping["navigation"].append({
                "element": str(nav.name),
                "horizontal": horizontal,
                "link_count": len(links),
                "classes": nav.get("class", [])
            })
            
        # Identify hero sections
        hero_elements = soup.find_all(class_=lambda c: c and any(x in str(c) for x in ["hero", "banner", "jumbotron"]))
        if not hero_elements:
            # Look for large elements at the top with images or headings
            main_content = soup.find("main") or soup.body
            if main_content:
                for element in list(main_content.children)[:3]:
                    if element.name in ["div", "section"] and (
                        element.find("h1") or 
                        (element.find("img") and len(element.get_text(strip=True)) > 50)
                    ):
                        hero_elements = [element]
                        break
                        
        # Process identified hero sections
        for hero in hero_elements:
            has_heading = bool(hero.find(["h1", "h2"]))
            has_image = bool(hero.find("img"))
            has_button = bool(hero.find(["button", "a"], class_=lambda c: c and any(x in str(c) for x in ["btn", "button"])))
            
            component_mapping["hero"].append({
                "element": str(hero.name),
                "has_heading": has_heading,
                "has_image": has_image,
                "has_button": has_button,
                "classes": hero.get("class", []),
                "text_length": len(hero.get_text(strip=True))
            })
            
        # Identify cards
        card_elements = soup.find_all(class_=lambda c: c and any(x in str(c) for x in ["card", "tile", "box"]))
        if not card_elements:
            # Look for repeating patterns
            potential_cards = []
            for div in soup.find_all("div"):
                if div.parent and len(div.parent.find_all("div", recursive=False)) >= 3:
                    # Parent has multiple div children - potential card container
                    siblings = div.parent.find_all("div", recursive=False)
                    if all(len(s.get_text(strip=True)) > 10 for s in siblings):
                        potential_cards.extend(siblings)
                        
            card_elements = potential_cards
            
        # Process identified cards
        for card in card_elements:
            has_heading = bool(card.find(["h1", "h2", "h3", "h4", "h5", "h6"]))
            has_image = bool(card.find("img"))
            has_text = len(card.get_text(strip=True)) > 20
            has_button = bool(card.find(["button", "a"], class_=lambda c: c and any(x in str(c) for x in ["btn", "button"])))
            
            component_mapping["card"].append({
                "element": str(card.name),
                "has_heading": has_heading,
                "has_image": has_image,
                "has_text": has_text,
                "has_button": has_button,
                "classes": card.get("class", [])
            })
            
        # Identify feature sections
        feature_elements = soup.find_all(class_=lambda c: c and any(x in str(c) for x in ["feature", "benefits"]))
        if not feature_elements:
            # Look for sections with icons/images and text
            for section in soup.find_all(["section", "div"]):
                if section.find("img") and section.find(["h2", "h3"]):
                    children = list(section.children)
                    if any(c.name == "div" and c.find("img") for c in children if c.name):
                        feature_elements.append(section)
                        
        # Process identified feature sections
        for feature in feature_elements:
            component_mapping["feature"].append({
                "element": str(feature.name),
                "has_icons": bool(feature.find(class_=lambda c: c and "icon" in str(c))),
                "has_images": bool(feature.find("img")),
                "classes": feature.get("class", [])
            })
            
        # Identify testimonials
        testimonial_elements = soup.find_all(class_=lambda c: c and any(x in str(c) for x in ["testimonial", "review", "quote"]))
        
        # Process identified testimonials
        for testimonial in testimonial_elements:
            component_mapping["testimonial"].append({
                "element": str(testimonial.name),
                "has_image": bool(testimonial.find("img")),
                "has_quote": bool(testimonial.find("blockquote") or testimonial.find("q")),
                "classes": testimonial.get("class", [])
            })
            
        # Identify CTA sections
        cta_elements = soup.find_all(class_=lambda c: c and any(x in str(c) for x in ["cta", "call-to-action", "action"]))
        if not cta_elements:
            # Look for sections with buttons/links
            for section in soup.find_all(["section", "div"]):
                buttons = section.find_all(["button", "a"], class_=lambda c: c and any(x in str(c) for x in ["btn", "button"]))
                heading = section.find(["h1", "h2", "h3"])
                if buttons and heading and len(section.get_text(strip=True)) < 200:  # Short sections with buttons
                    cta_elements.append(section)
                    
        # Process identified CTA sections
        for cta in cta_elements:
            component_mapping["cta"].append({
                "element": str(cta.name),
                "has_heading": bool(cta.find(["h1", "h2", "h3"])),
                "has_button": bool(cta.find(["button", "a"], class_=lambda c: c and any(x in str(c) for x in ["btn", "button"]))),
                "classes": cta.get("class", [])
            })
            
        # Identify forms
        form_elements = soup.find_all("form")
        
        # Process identified forms
        for form in form_elements:
            component_mapping["form"].append({
                "element": "form",
                "input_count": len(form.find_all("input")),
                "has_submit": bool(form.find("input", attrs={"type": "submit"}) or form.find("button", attrs={"type": "submit"})),
                "classes": form.get("class", [])
            })
            
        # Identify sidebars
        sidebar_elements = soup.find_all(["aside", "div"], class_=lambda c: c and any(x in str(c) for x in ["sidebar", "side-nav"]))
        
        # Process identified sidebars
        for sidebar in sidebar_elements:
            component_mapping["sidebar"].append({
                "element": str(sidebar.name),
                "has_nav": bool(sidebar.find("nav") or sidebar.find("ul")),
                "has_widgets": bool(sidebar.find(class_=lambda c: c and "widget" in str(c))),
                "classes": sidebar.get("class", [])
            })
            
        return component_mapping
    
    async def _identify_layout_type(
        self, 
        soup: BeautifulSoup, 
        document_structure: Dict[str, Any],
        component_mapping: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """
        Identify the layout type of the document.
        
        Args:
            soup: BeautifulSoup object of the HTML
            document_structure: Document structure dictionary
            component_mapping: Component mapping dictionary
            
        Returns:
            Layout type string
        """
        # Check for common layout patterns
        has_header = bool(component_mapping["header"])
        has_footer = bool(component_mapping["footer"])
        has_navigation = bool(component_mapping["navigation"])
        has_sidebar = bool(component_mapping["sidebar"])
        
        # Check for explicit grid/flex layouts
        body_classes = soup.body.get("class", []) if soup.body else []
        main_element = soup.find("main")
        main_classes = main_element.get("class", []) if main_element else []
        
        # Look for grid layout indicators
        is_grid_layout = any("grid" in str(c) for c in body_classes + main_classes)
        
        # Look for flex layout indicators
        is_flex_layout = any("flex" in str(c) for c in body_classes + main_classes)
        
        # Identify layout type based on combinations
        if has_sidebar:
            if has_header and has_footer:
                return "header-sidebar-main-footer"
            elif has_navigation:
                return "nav-main-sidebar"
            else:
                return "sidebar-main"
        elif has_navigation and not has_header:
            return "nav-main"
        elif has_header and has_footer:
            return "header-main-footer"
        elif has_header and not has_footer:
            return "header-main"
        elif is_grid_layout:
            return "grid-layout"
        elif is_flex_layout:
            return "flex-layout"
        else:
            return "single-column"
