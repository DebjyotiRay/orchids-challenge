import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple
import asyncio

from .base_agent import BaseAgent


class LayoutGeneratorAgent(BaseAgent):
    """
    Agent responsible for generating responsive layout specifications.
    
    This agent creates CSS Grid and Flexbox specifications based on the
    document structure and layout type identified by the semantic parser.
    """
    
    def __init__(self, **kwargs):
        """Initialize the Layout Generator Agent with specific configurations."""
        super().__init__(**kwargs)
        
        # Grid configuration
        self.column_counts = kwargs.get("column_counts", {
            "mobile": 4,
            "tablet": 8,
            "desktop": 12
        })
        self.breakpoints = kwargs.get("breakpoints", {
            "mobile": "0px",
            "tablet": "768px",
            "desktop": "1200px"
        })
        self.generate_responsive = kwargs.get("generate_responsive", True)
        self.mobile_first = kwargs.get("mobile_first", True)
        self.use_grid = kwargs.get("use_grid", True)
        self.use_flex = kwargs.get("use_flex", True)
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and generate layout specifications.
        
        Args:
            input_data: Dictionary containing document structure and semantic components
            
        Returns:
            Dictionary containing layout specifications
        """
        document_structure = input_data.get("document_structure", {})
        component_mapping = input_data.get("component_mapping", {})
        layout_type = input_data.get("layout_type", "single-column")
        design_system = input_data.get("design_system", {})
        
        if self.debug:
            print(f"[LayoutGeneratorAgent] Generating layout for type: {layout_type}")
        
        # Generate grid specification based on layout type
        grid_specification = await self._generate_grid_specification(layout_type, component_mapping)
        
        # Generate responsive layouts
        responsive_layouts = {}
        if self.generate_responsive:
            responsive_layouts = await self._generate_responsive_layouts(layout_type, grid_specification)
            
        # Generate CSS Grid styles
        layout_css = await self._generate_layout_css(grid_specification, responsive_layouts)
        
        # Add the layout CSS to the grid specification
        grid_specification["layout_css"] = layout_css
        
        return {
            "grid_specification": grid_specification,
            "responsive_layouts": responsive_layouts
        }
    
    async def _generate_grid_specification(
        self, layout_type: str, component_mapping: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Generate a grid specification based on the layout type.
        
        Args:
            layout_type: Layout type string
            component_mapping: Component mapping from semantic parser
            
        Returns:
            Grid specification dictionary
        """
        # Initialize grid specification
        grid_specification = {
            "type": layout_type,
            "columns": self.column_counts["desktop"],
            "rows": [],
            "areas": {},
            "gap": "1rem",
            "container_width": "1280px"
        }
        
        # Define areas based on layout type
        if layout_type == "header-main-footer":
            grid_specification["areas"] = {
                "header": {"row": 1, "column": 1, "row_span": 1, "column_span": 12},
                "main": {"row": 2, "column": 1, "row_span": 1, "column_span": 12},
                "footer": {"row": 3, "column": 1, "row_span": 1, "column_span": 12}
            }
            grid_specification["rows"] = ["auto", "1fr", "auto"]
            
        elif layout_type == "header-sidebar-main-footer":
            grid_specification["areas"] = {
                "header": {"row": 1, "column": 1, "row_span": 1, "column_span": 12},
                "sidebar": {"row": 2, "column": 1, "row_span": 1, "column_span": 3},
                "main": {"row": 2, "column": 4, "row_span": 1, "column_span": 9},
                "footer": {"row": 3, "column": 1, "row_span": 1, "column_span": 12}
            }
            grid_specification["rows"] = ["auto", "1fr", "auto"]
            
        elif layout_type == "nav-main":
            grid_specification["areas"] = {
                "nav": {"row": 1, "column": 1, "row_span": 1, "column_span": 3},
                "main": {"row": 1, "column": 4, "row_span": 1, "column_span": 9}
            }
            grid_specification["rows"] = ["1fr"]
            
        elif layout_type == "nav-main-sidebar":
            grid_specification["areas"] = {
                "nav": {"row": 1, "column": 1, "row_span": 1, "column_span": 2},
                "main": {"row": 1, "column": 3, "row_span": 1, "column_span": 8},
                "sidebar": {"row": 1, "column": 11, "row_span": 1, "column_span": 2}
            }
            grid_specification["rows"] = ["1fr"]
            
        elif layout_type == "header-main":
            grid_specification["areas"] = {
                "header": {"row": 1, "column": 1, "row_span": 1, "column_span": 12},
                "main": {"row": 2, "column": 1, "row_span": 1, "column_span": 12}
            }
            grid_specification["rows"] = ["auto", "1fr"]
            
        elif layout_type == "sidebar-main":
            grid_specification["areas"] = {
                "sidebar": {"row": 1, "column": 1, "row_span": 1, "column_span": 3},
                "main": {"row": 1, "column": 4, "row_span": 1, "column_span": 9}
            }
            grid_specification["rows"] = ["1fr"]
            
        else:  # single-column or unknown
            grid_specification["areas"] = {
                "main": {"row": 1, "column": 1, "row_span": 1, "column_span": 12}
            }
            grid_specification["rows"] = ["1fr"]
            
        return grid_specification
    
    async def _generate_responsive_layouts(
        self, layout_type: str, grid_specification: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate responsive layout variations for different breakpoints.
        
        Args:
            layout_type: Layout type string
            grid_specification: Base grid specification
            
        Returns:
            Dictionary with responsive layout variations
        """
        # Initialize responsive layouts
        responsive_layouts = {
            "mobile": {},
            "tablet": {}
        }
        
        # Mobile layout (stacked)
        mobile_layout = {
            "type": f"{layout_type}-mobile",
            "columns": self.column_counts["mobile"],
            "rows": [],
            "areas": {},
            "gap": "0.5rem"
        }
        
        # Tablet layout (simplified)
        tablet_layout = {
            "type": f"{layout_type}-tablet",
            "columns": self.column_counts["tablet"],
            "rows": [],
            "areas": {},
            "gap": "0.75rem"
        }
        
        # Adjust areas based on layout type
        if layout_type == "header-main-footer":
            # Mobile (stacked vertically)
            mobile_layout["areas"] = {
                "header": {"row": 1, "column": 1, "row_span": 1, "column_span": 4},
                "main": {"row": 2, "column": 1, "row_span": 1, "column_span": 4},
                "footer": {"row": 3, "column": 1, "row_span": 1, "column_span": 4}
            }
            mobile_layout["rows"] = ["auto", "auto", "auto"]
            
            # Tablet (same layout but adjusted columns)
            tablet_layout["areas"] = {
                "header": {"row": 1, "column": 1, "row_span": 1, "column_span": 8},
                "main": {"row": 2, "column": 1, "row_span": 1, "column_span": 8},
                "footer": {"row": 3, "column": 1, "row_span": 1, "column_span": 8}
            }
            tablet_layout["rows"] = ["auto", "1fr", "auto"]
            
        elif layout_type == "header-sidebar-main-footer":
            # Mobile (stacked vertically)
            mobile_layout["areas"] = {
                "header": {"row": 1, "column": 1, "row_span": 1, "column_span": 4},
                "sidebar": {"row": 3, "column": 1, "row_span": 1, "column_span": 4},
                "main": {"row": 2, "column": 1, "row_span": 1, "column_span": 4},
                "footer": {"row": 4, "column": 1, "row_span": 1, "column_span": 4}
            }
            mobile_layout["rows"] = ["auto", "auto", "auto", "auto"]
            
            # Tablet (same layout but adjusted columns)
            tablet_layout["areas"] = {
                "header": {"row": 1, "column": 1, "row_span": 1, "column_span": 8},
                "sidebar": {"row": 2, "column": 1, "row_span": 1, "column_span": 3},
                "main": {"row": 2, "column": 4, "row_span": 1, "column_span": 5},
                "footer": {"row": 3, "column": 1, "row_span": 1, "column_span": 8}
            }
            tablet_layout["rows"] = ["auto", "1fr", "auto"]
            
        elif layout_type in ["nav-main", "nav-main-sidebar"]:
            # Mobile (stacked vertically)
            mobile_layout["areas"] = {
                "nav": {"row": 1, "column": 1, "row_span": 1, "column_span": 4},
                "main": {"row": 2, "column": 1, "row_span": 1, "column_span": 4},
                "sidebar": {"row": 3, "column": 1, "row_span": 1, "column_span": 4} if layout_type == "nav-main-sidebar" else {}
            }
            mobile_layout["rows"] = ["auto", "auto"] + (["auto"] if layout_type == "nav-main-sidebar" else [])
            
            # Tablet (adjusted columns)
            if layout_type == "nav-main":
                tablet_layout["areas"] = {
                    "nav": {"row": 1, "column": 1, "row_span": 1, "column_span": 2},
                    "main": {"row": 1, "column": 3, "row_span": 1, "column_span": 6}
                }
                tablet_layout["rows"] = ["1fr"]
            else:  # nav-main-sidebar
                tablet_layout["areas"] = {
                    "nav": {"row": 1, "column": 1, "row_span": 1, "column_span": 2},
                    "main": {"row": 1, "column": 3, "row_span": 1, "column_span": 4},
                    "sidebar": {"row": 1, "column": 7, "row_span": 1, "column_span": 2}
                }
                tablet_layout["rows"] = ["1fr"]
                
        elif layout_type == "header-main":
            # Mobile (stacked vertically)
            mobile_layout["areas"] = {
                "header": {"row": 1, "column": 1, "row_span": 1, "column_span": 4},
                "main": {"row": 2, "column": 1, "row_span": 1, "column_span": 4}
            }
            mobile_layout["rows"] = ["auto", "auto"]
            
            # Tablet (adjusted columns)
            tablet_layout["areas"] = {
                "header": {"row": 1, "column": 1, "row_span": 1, "column_span": 8},
                "main": {"row": 2, "column": 1, "row_span": 1, "column_span": 8}
            }
            tablet_layout["rows"] = ["auto", "1fr"]
            
        elif layout_type == "sidebar-main":
            # Mobile (stacked vertically)
            mobile_layout["areas"] = {
                "sidebar": {"row": 1, "column": 1, "row_span": 1, "column_span": 4},
                "main": {"row": 2, "column": 1, "row_span": 1, "column_span": 4}
            }
            mobile_layout["rows"] = ["auto", "auto"]
            
            # Tablet (adjusted columns)
            tablet_layout["areas"] = {
                "sidebar": {"row": 1, "column": 1, "row_span": 1, "column_span": 3},
                "main": {"row": 1, "column": 4, "row_span": 1, "column_span": 5}
            }
            tablet_layout["rows"] = ["1fr"]
            
        else:  # single-column or unknown
            # Mobile (full width)
            mobile_layout["areas"] = {
                "main": {"row": 1, "column": 1, "row_span": 1, "column_span": 4}
            }
            mobile_layout["rows"] = ["1fr"]
            
            # Tablet (full width)
            tablet_layout["areas"] = {
                "main": {"row": 1, "column": 1, "row_span": 1, "column_span": 8}
            }
            tablet_layout["rows"] = ["1fr"]
            
        # Save to responsive layouts
        responsive_layouts["mobile"] = mobile_layout
        responsive_layouts["tablet"] = tablet_layout
        
        return responsive_layouts
    
    async def _generate_layout_css(
        self, 
        grid_specification: Dict[str, Any],
        responsive_layouts: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Generate CSS for the layout grid.
        
        Args:
            grid_specification: Grid specification dictionary
            responsive_layouts: Dictionary with responsive layout variations
            
        Returns:
            CSS string for the layout
        """
        css = []
        
        # Add base grid styles
        css.append('/* Layout Grid */')
        css.append('.layout-grid {')
        css.append('  display: grid;')
        css.append(f'  gap: {grid_specification.get("gap", "1rem")};')
        css.append('  height: 100vh;')
        css.append('  width: 100%;')
        css.append('  max-width: 100%;')
        css.append('}')
        
        # Add container styles
        css.append('')
        css.append('.layout-container {')
        css.append('  width: 100%;')
        css.append(f'  max-width: {grid_specification.get("container_width", "1280px")};')
        css.append('  margin-left: auto;')
        css.append('  margin-right: auto;')
        css.append('}')
        
        # Mobile styles (base styles if mobile-first)
        if self.mobile_first and "mobile" in responsive_layouts:
            mobile_layout = responsive_layouts["mobile"]
            
            css.append('')
            css.append('/* Mobile Layout (Base) */')
            css.append('.layout-grid {')
            css.append(f'  grid-template-columns: repeat({mobile_layout.get("columns", 4)}, 1fr);')
            
            # Add grid template rows
            rows = mobile_layout.get("rows", ["auto"])
            css.append(f'  grid-template-rows: {" ".join(rows)};')
            
            # Define grid template areas if using named areas
            areas = mobile_layout.get("areas", {})
            if areas:
                area_names = set(areas.keys())
                max_row = max(area["row"] + area["row_span"] - 1 for area in areas.values())
                
                area_layout = []
                for row in range(1, max_row + 1):
                    row_areas = []
                    for col in range(1, mobile_layout.get("columns", 4) + 1):
                        area_name = "."
                        for name, area in areas.items():
                            if (area["row"] <= row < area["row"] + area["row_span"] and
                                area["column"] <= col < area["column"] + area["column_span"]):
                                area_name = name
                                break
                        row_areas.append(area_name)
                    area_layout.append(f'    "{" ".join(row_areas)}"')
                
                css.append('  grid-template-areas:')
                css.append("\n".join(area_layout) + ";")
            
            css.append('}')
            
            # Add area styles
            for area_name in areas:
                css.append(f'.layout-{area_name} {{')
                css.append(f'  grid-area: {area_name};')
                css.append('}')
            
            # Add area-specific styles
            await self._add_area_specific_styles(css)
            
        # Tablet media query
        if "tablet" in responsive_layouts:
            tablet_layout = responsive_layouts["tablet"]
            tablet_breakpoint = self.breakpoints.get("tablet", "768px")
            
            css.append('')
            css.append(f'/* Tablet Layout (>={tablet_breakpoint}) */')
            css.append(f'@media (min-width: {tablet_breakpoint}) {{')
            css.append('  .layout-grid {')
            css.append(f'    grid-template-columns: repeat({tablet_layout.get("columns", 8)}, 1fr);')
            
            # Add grid template rows
            rows = tablet_layout.get("rows", ["auto"])
            css.append(f'    grid-template-rows: {" ".join(rows)};')
            
            # Define grid template areas if using named areas
            areas = tablet_layout.get("areas", {})
            if areas:
                area_names = set(areas.keys())
                max_row = max(area["row"] + area["row_span"] - 1 for area in areas.values() if "row" in area and "row_span" in area)
                
                area_layout = []
                for row in range(1, max_row + 1):
                    row_areas = []
                    for col in range(1, tablet_layout.get("columns", 8) + 1):
                        area_name = "."
                        for name, area in areas.items():
                            if (area.get("row", 0) <= row < area.get("row", 0) + area.get("row_span", 1) and
                                area.get("column", 0) <= col < area.get("column", 0) + area.get("column_span", 1)):
                                area_name = name
                                break
                        row_areas.append(area_name)
                    area_layout.append(f'      "{" ".join(row_areas)}"')
                
                css.append('    grid-template-areas:')
                css.append("\n".join(area_layout) + ";")
            
            css.append('  }')
            
            # Add any tablet-specific styles here
            
            css.append('}')
        
        # Desktop media query
        if not self.mobile_first or "tablet" in responsive_layouts:
            desktop_breakpoint = self.breakpoints.get("desktop", "1200px")
            
            css.append('')
            css.append(f'/* Desktop Layout (>={desktop_breakpoint}) */')
            css.append(f'@media (min-width: {desktop_breakpoint}) {{')
            css.append('  .layout-grid {')
            css.append(f'    grid-template-columns: repeat({grid_specification.get("columns", 12)}, 1fr);')
            
            # Add grid template rows
            rows = grid_specification.get("rows", ["auto"])
            css.append(f'    grid-template-rows: {" ".join(rows)};')
            
            # Define grid template areas if using named areas
            areas = grid_specification.get("areas", {})
            if areas:
                area_names = set(areas.keys())
                max_row = max(area["row"] + area["row_span"] - 1 for area in areas.values())
                
                area_layout = []
                for row in range(1, max_row + 1):
                    row_areas = []
                    for col in range(1, grid_specification.get("columns", 12) + 1):
                        area_name = "."
                        for name, area in areas.items():
                            if (area["row"] <= row < area["row"] + area["row_span"] and
                                area["column"] <= col < area["column"] + area["column_span"]):
                                area_name = name
                                break
                        row_areas.append(area_name)
                    area_layout.append(f'      "{" ".join(row_areas)}"')
                
                css.append('    grid-template-areas:')
                css.append("\n".join(area_layout) + ";")
            
            css.append('  }')
            
            # Add any desktop-specific styles here
            
            css.append('}')
        
        return "\n".join(css)
    
    async def _add_area_specific_styles(self, css: List[str]) -> None:
        """
        Add area-specific styles to the CSS.
        
        Args:
            css: List of CSS rules to append to
        """
        # Header styles
        css.append('')
        css.append('/* Area-specific styles */')
        css.append('.layout-header {')
        css.append('  position: sticky;')
        css.append('  top: 0;')
        css.append('  z-index: 100;')
        css.append('  background-color: var(--color-background, #ffffff);')
        css.append('}')
        
        # Main styles
        css.append('')
        css.append('.layout-main {')
        css.append('  min-height: 50vh;')
        css.append('}')
        
        # Sidebar styles
        css.append('')
        css.append('.layout-sidebar {')
        css.append('  background-color: var(--color-light, #f8f9fa);')
        css.append('  padding: var(--space-4, 1rem);')
        css.append('}')
        
        # Navigation styles
        css.append('')
        css.append('.layout-nav {')
        css.append('  background-color: var(--color-light, #f8f9fa);')
        css.append('  padding: var(--space-2, 0.5rem);')
        css.append('}')
        
        # Footer styles
        css.append('')
        css.append('.layout-footer {')
        css.append('  margin-top: auto;')
        css.append('  padding: var(--space-4, 1rem) 0;')
        css.append('  background-color: var(--color-dark, #343a40);')
        css.append('  color: var(--color-light, #f8f9fa);')
        css.append('}')
