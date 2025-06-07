import os
import asyncio
import tempfile
from pathlib import Path
from urllib.parse import urlparse, urljoin
import re
from typing import Dict, List, Any, Tuple
import base64
import json

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import requests
from PIL import Image, ImageColor
import numpy as np

from .models import ScrapeResult

# Create a directory for storing screenshots
SCREENSHOTS_DIR = Path("screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)

class WebsiteScraper:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    async def scrape(self, url: str) -> ScrapeResult:
        """Scrape a website and extract useful design context."""
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                device_scale_factor=1,
            )
            page = await context.new_page()
            
            try:
                # Navigate to URL
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Take screenshot
                screenshot_path = str(SCREENSHOTS_DIR / f"{urlparse(url).netloc}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                
                # Get HTML content
                html_content = await page.content()
                
                # Extract CSS
                css_content = await self._extract_css(page, url)
                
                # Extract text content
                text_content = await page.evaluate('() => document.body.innerText')
                
                # Extract meta tags
                meta_tags = await self._extract_meta_tags(page)
                
                # Extract color palette
                color_palette = await self._extract_colors(page, screenshot_path)
                
                # Extract fonts
                fonts = await self._extract_fonts(page)
                
                # Extract layout structure
                layout_structure = await self._extract_layout(page)
                
                return ScrapeResult(
                    html=html_content,
                    css=css_content,
                    screenshot_path=screenshot_path,
                    text_content=text_content,
                    meta_tags=meta_tags,
                    color_palette=color_palette,
                    fonts=fonts,
                    layout_structure=layout_structure,
                )
            finally:
                await browser.close()
    
    async def _extract_css(self, page, base_url: str) -> str:
        """Extract CSS content from the page."""
        css_links = await page.evaluate('''() => {
            const linkElements = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
            return linkElements.map(link => link.href);
        }''')
        
        css_content = []
        for link in css_links:
            try:
                if link.startswith('http'):
                    response = requests.get(link, timeout=10)
                    if response.status_code == 200:
                        css_content.append(response.text)
            except Exception:
                pass
        
        # Also extract inline styles
        inline_styles = await page.evaluate('''() => {
            const styleElements = Array.from(document.querySelectorAll('style'));
            return styleElements.map(style => style.textContent).join('\\n');
        }''')
        
        if inline_styles:
            css_content.append(inline_styles)
        
        return "\n".join(css_content)
    
    async def _extract_meta_tags(self, page) -> Dict[str, str]:
        """Extract meta tags from the page."""
        return await page.evaluate('''() => {
            const metaTags = {};
            document.querySelectorAll('meta').forEach(meta => {
                if (meta.name && meta.content) {
                    metaTags[meta.name] = meta.content;
                } else if (meta.getAttribute('property') && meta.content) {
                    metaTags[meta.getAttribute('property')] = meta.content;
                }
            });
            
            // Also grab title
            metaTags['title'] = document.title;
            
            return metaTags;
        }''')
    
    async def _extract_colors(self, page, screenshot_path: str) -> List[str]:
        """Extract dominant colors from the page."""
        colors = await page.evaluate('''() => {
            const computedStyles = [];
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                computedStyles.push(style.color, style.backgroundColor);
            });
            
            return computedStyles.filter(color => 
                color && 
                color !== 'transparent' && 
                color !== 'rgba(0, 0, 0, 0)' && 
                !color.includes('var(')
            );
        }''')
        
        # Normalize and deduplicate colors
        unique_colors = set()
        for color in colors:
            # Try to convert any color format to hex
            try:
                if color.startswith('rgb'):
                    match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                    if match:
                        r, g, b = map(int, match.groups())
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        unique_colors.add(hex_color)
                elif color.startswith('#'):
                    unique_colors.add(color.lower())
            except Exception:
                pass
                
        # If we have an image, also extract colors from it
        try:
            img = Image.open(screenshot_path)
            img = img.resize((100, 100))  # Resize for faster processing
            colors = img.getcolors(10000)  # Get all colors
            if colors:
                # Sort colors by count
                colors.sort(reverse=True, key=lambda x: x[0])
                # Add top 10 colors
                for _, (r, g, b, _) in colors[:10]:
                    unique_colors.add(f"#{r:02x}{g:02x}{b:02x}")
        except Exception:
            pass
            
        return list(unique_colors)[:20]  # Return top 20 colors
    
    async def _extract_fonts(self, page) -> List[str]:
        """Extract fonts used in the page."""
        return await page.evaluate('''() => {
            const fontFamilies = new Set();
            document.querySelectorAll('*').forEach(el => {
                const fontFamily = window.getComputedStyle(el).fontFamily;
                if (fontFamily) {
                    fontFamilies.add(fontFamily);
                }
            });
            return Array.from(fontFamilies);
        }''')
    
    async def _extract_layout(self, page) -> Dict[str, Any]:
        """Extract layout structure from the page."""
        return await page.evaluate('''() => {
            // Function to get basic element data
            function getElementInfo(el, depth = 0) {
                if (!el || depth > 5) return null; // Limit depth to avoid too much complexity
                
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return null;
                
                const computedStyle = window.getComputedStyle(el);
                
                return {
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    classes: Array.from(el.classList).join(' ') || null,
                    text: el.innerText ? (el.innerText.substring(0, 100) + (el.innerText.length > 100 ? '...' : '')) : null,
                    position: {
                        x: Math.round(rect.left),
                        y: Math.round(rect.top),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                    },
                    styles: {
                        display: computedStyle.display,
                        position: computedStyle.position,
                        flexDirection: computedStyle.flexDirection,
                        justifyContent: computedStyle.justifyContent,
                        alignItems: computedStyle.alignItems,
                        backgroundColor: computedStyle.backgroundColor,
                        color: computedStyle.color,
                        fontFamily: computedStyle.fontFamily,
                        fontSize: computedStyle.fontSize,
                        fontWeight: computedStyle.fontWeight,
                    },
                    role: el.getAttribute('role') || null,
                    isVisible: computedStyle.display !== 'none' && 
                               computedStyle.visibility !== 'hidden' && 
                               computedStyle.opacity !== '0'
                };
            }
            
            // Function to get main sections (limit depth to reduce complexity)
            function buildStructure(rootElement, maxDepth = 2, currentDepth = 0) {
                const info = getElementInfo(rootElement, currentDepth);
                if (!info || !info.isVisible) return null;
                
                if (currentDepth >= maxDepth) return info;
                
                info.children = [];
                
                // Select significant children to avoid too many elements
                const potentialChildren = Array.from(rootElement.children);
                for (const child of potentialChildren) {
                    const rect = child.getBoundingClientRect();
                    // Skip tiny elements or invisible elements
                    if (rect.width > 20 && rect.height > 20) {
                        const childInfo = buildStructure(child, maxDepth, currentDepth + 1);
                        if (childInfo) info.children.push(childInfo);
                    }
                }
                
                return info;
            }
            
            // Start with body and select major sections
            const mainSections = {
                header: null,
                main: null,
                footer: null,
                sections: []
            };
            
            // Try to identify major sections
            const header = document.querySelector('header') || document.querySelector('.header');
            const main = document.querySelector('main');
            const footer = document.querySelector('footer') || document.querySelector('.footer');
            
            if (header) mainSections.header = buildStructure(header);
            if (main) mainSections.main = buildStructure(main);
            if (footer) mainSections.footer = buildStructure(footer);
            
            // Add other significant sections if they exist
            document.querySelectorAll('section, .section, article, .content, .container, [role="region"]').forEach(section => {
                const sectionInfo = buildStructure(section);
                if (sectionInfo) mainSections.sections.push(sectionInfo);
            });
            
            // If no major sections are found, get direct children of body
            if (!mainSections.header && !mainSections.main && !mainSections.footer && mainSections.sections.length === 0) {
                const bodyChildren = [];
                document.body.childNodes.forEach(child => {
                    if (child.nodeType === 1) { // Element nodes only
                        const childInfo = buildStructure(child);
                        if (childInfo) bodyChildren.push(childInfo);
                    }
                });
                mainSections.sections = bodyChildren;
            }
            
            // Get viewport size
            mainSections.viewport = {
                width: window.innerWidth,
                height: window.innerHeight
            };
            
            return mainSections;
        }''')
