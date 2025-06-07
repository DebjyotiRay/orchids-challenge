import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

from .base_agent import BaseAgent


class ValidationAgent(BaseAgent):
    """
    Agent responsible for validating the generated website.
    
    This agent performs quality assurance checks including accessibility,
    performance, SEO, and best practices validation.
    """
    
    def __init__(self, **kwargs):
        """Initialize the Validation Agent with specific configurations."""
        super().__init__(**kwargs)
        
        # Configure validation thresholds
        self.performance_threshold = kwargs.get("performance_threshold", 90)
        self.accessibility_threshold = kwargs.get("accessibility_threshold", 95)
        self.seo_threshold = kwargs.get("seo_threshold", 90)
        self.best_practices_threshold = kwargs.get("best_practices_threshold", 85)
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and validate the website.
        
        Args:
            input_data: Dictionary containing the generated website data
            
        Returns:
            Dictionary containing validation results
        """
        html_output = input_data.get("html_output", "")
        css_output = input_data.get("css_output", "")
        
        if not html_output or not css_output:
            raise ValueError("HTML and CSS outputs are required")
            
        if self.debug:
            print("[ValidationAgent] Validating generated website")
        
        # Perform accessibility validation
        accessibility_results = await self._validate_accessibility(html_output)
        
        # Perform SEO validation
        seo_results = await self._validate_seo(html_output)
        
        # Perform performance validation
        performance_results = await self._validate_performance(html_output, css_output)
        
        # Perform best practices validation
        best_practices_results = await self._validate_best_practices(html_output, css_output)
        
        # Calculate overall quality score
        quality_score = await self._calculate_quality_score(
            accessibility_results, 
            seo_results,
            performance_results,
            best_practices_results
        )
        
        # Generate validation report
        validation_report = await self._generate_validation_report(
            accessibility_results,
            seo_results,
            performance_results,
            best_practices_results,
            quality_score
        )
        
        return {
            "accessibility_results": accessibility_results,
            "seo_results": seo_results,
            "performance_results": performance_results,
            "best_practices_results": best_practices_results,
            "quality_score": quality_score,
            "validation_report": validation_report,
            "passed": quality_score >= 90
        }
        
    async def _validate_accessibility(self, html_output: str) -> Dict[str, Any]:
        """
        Validate accessibility of the HTML.
        
        Args:
            html_output: HTML content
            
        Returns:
            Dictionary containing accessibility validation results
        """
        # Check for common accessibility issues
        issues = []
        score = 100
        
        # Check for alt attributes on images
        img_tags = re.findall(r'<img[^>]*>', html_output)
        img_tags_without_alt = [tag for tag in img_tags if 'alt=' not in tag]
        
        if img_tags_without_alt:
            issues.append({
                "rule": "images-alt",
                "impact": "critical",
                "description": "Images must have alternate text",
                "elements": len(img_tags_without_alt),
                "help": "Provide an alt attribute for images"
            })
            score -= 10 * len(img_tags_without_alt)
        
        # Check for form labels
        input_tags = re.findall(r'<input[^>]*>', html_output)
        input_tags_without_label = [tag for tag in input_tags if 'type="hidden"' not in tag and 'aria-label=' not in tag and 'id=' not in tag]
        
        if input_tags_without_label:
            issues.append({
                "rule": "label",
                "impact": "critical",
                "description": "Form elements must have labels",
                "elements": len(input_tags_without_label),
                "help": "Provide labels for form controls"
            })
            score -= 10 * len(input_tags_without_label)
        
        # Check for heading structure
        headings = re.findall(r'<h([1-6])[^>]*>', html_output)
        if headings and '1' not in headings:
            issues.append({
                "rule": "heading-order",
                "impact": "moderate",
                "description": "Page should contain a level-one heading",
                "help": "Ensure page has a descriptive heading structure starting with h1"
            })
            score -= 5
        
        # Check for color contrast (simplified)
        if 'color:' in html_output.lower() and 'background-color:' in html_output.lower():
            # This is a simplified check - in a real implementation, 
            # we would parse the CSS and check contrast ratios
            pass
        
        # Check for language attribute
        if '<html' in html_output and 'lang=' not in html_output:
            issues.append({
                "rule": "html-has-lang",
                "impact": "serious",
                "description": "HTML element must have a lang attribute",
                "help": "Specify the language of the page"
            })
            score -= 10
            
        # Ensure the score is within bounds
        score = max(0, min(100, score))
            
        # Check if the accessibility score meets the threshold
        passed = score >= self.accessibility_threshold
        
        return {
            "score": score,
            "passed": passed,
            "issues": issues,
            "threshold": self.accessibility_threshold
        }
    
    async def _validate_seo(self, html_output: str) -> Dict[str, Any]:
        """
        Validate SEO of the HTML.
        
        Args:
            html_output: HTML content
            
        Returns:
            Dictionary containing SEO validation results
        """
        issues = []
        score = 100
        
        # Check for title tag
        title_match = re.search(r'<title>([^<]*)</title>', html_output)
        if not title_match:
            issues.append({
                "rule": "document-title",
                "impact": "high",
                "description": "Document must have a title",
                "help": "Provide a title that describes the page content"
            })
            score -= 15
        elif len(title_match.group(1)) < 10:
            issues.append({
                "rule": "document-title-length",
                "impact": "medium",
                "description": "Title is too short",
                "help": "Provide a descriptive title that is at least 10 characters long"
            })
            score -= 5
            
        # Check for meta description
        meta_desc = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html_output)
        if not meta_desc:
            issues.append({
                "rule": "meta-description",
                "impact": "medium",
                "description": "Document does not have a meta description",
                "help": "Provide a meta description that summarizes the page content"
            })
            score -= 10
            
        # Check for heading structure
        h1_tags = re.findall(r'<h1[^>]*>([^<]*)</h1>', html_output)
        if not h1_tags:
            issues.append({
                "rule": "heading-structure",
                "impact": "medium",
                "description": "Document does not have an H1 heading",
                "help": "Include an H1 heading that describes the main topic of the page"
            })
            score -= 10
        elif len(h1_tags) > 1:
            issues.append({
                "rule": "multiple-h1",
                "impact": "low",
                "description": "Document has multiple H1 headings",
                "help": "Use only one H1 heading per page"
            })
            score -= 5
            
        # Check for canonical tag
        canonical = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)["\']', html_output)
        if not canonical:
            issues.append({
                "rule": "canonical-url",
                "impact": "low",
                "description": "Document does not have a canonical URL",
                "help": "Include a canonical link to prevent duplicate content issues"
            })
            score -= 5
            
        # Check for structured data (simplified)
        if 'itemtype="http://schema.org/' not in html_output and 'itemtype="https://schema.org/' not in html_output:
            issues.append({
                "rule": "structured-data",
                "impact": "medium",
                "description": "No structured data found",
                "help": "Add schema.org structured data to enhance search results"
            })
            score -= 8
            
        # Check for responsive viewport
        viewport = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*content=["\']([^"\']*)["\']', html_output)
        if not viewport:
            issues.append({
                "rule": "viewport",
                "impact": "high",
                "description": "Document does not have a viewport meta tag",
                "help": "Include a viewport meta tag for responsive design"
            })
            score -= 12
            
        # Ensure the score is within bounds
        score = max(0, min(100, score))
            
        # Check if the SEO score meets the threshold
        passed = score >= self.seo_threshold
        
        return {
            "score": score,
            "passed": passed,
            "issues": issues,
            "threshold": self.seo_threshold
        }
        
    async def _validate_performance(self, html_output: str, css_output: str) -> Dict[str, Any]:
        """
        Validate performance of the HTML and CSS.
        
        Args:
            html_output: HTML content
            css_output: CSS content
            
        Returns:
            Dictionary containing performance validation results
        """
        issues = []
        score = 100
        
        # Check for render-blocking resources
        script_tags = re.findall(r'<script[^>]*src=["\'][^"\']*["\'][^>]*>', html_output)
        if script_tags:
            for script in script_tags:
                if 'defer' not in script and 'async' not in script:
                    issues.append({
                        "rule": "render-blocking-resources",
                        "impact": "medium",
                        "description": "Script tag without defer or async attribute",
                        "help": "Add defer or async attribute to non-critical scripts"
                    })
                    score -= 5
                    break
        
        # Check for large CSS files
        css_size = len(css_output)
        if css_size > 100000:  # 100KB threshold
            issues.append({
                "rule": "unminified-css",
                "impact": "medium",
                "description": "Large CSS file detected",
                "help": "Minify CSS and remove unused styles",
                "size": css_size
            })
            score -= 10
        
        # Check for unoptimized images (simplified)
        img_tags = re.findall(r'<img[^>]*>', html_output)
        for img in img_tags:
            if 'loading=' not in img:
                issues.append({
                    "rule": "offscreen-images",
                    "impact": "medium",
                    "description": "Image without lazy loading",
                    "help": "Add loading='lazy' to images below the fold"
                })
                score -= 3
                break
        
        # Check for proper cache headers (simplified - can't check this from HTML/CSS alone)
        
        # Check for text compression (simplified - can't check this from HTML/CSS alone)
        
        # Check for excessive DOM size
        dom_elements = len(re.findall(r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*>', html_output))
        if dom_elements > 1500:
            issues.append({
                "rule": "dom-size",
                "impact": "low",
                "description": "Excessive DOM size",
                "help": "Reduce the number of DOM elements",
                "elements": dom_elements
            })
            score -= 8
        
        # Ensure the score is within bounds
        score = max(0, min(100, score))
            
        # Check if the performance score meets the threshold
        passed = score >= self.performance_threshold
        
        return {
            "score": score,
            "passed": passed,
            "issues": issues,
            "threshold": self.performance_threshold
        }
    
    async def _validate_best_practices(self, html_output: str, css_output: str) -> Dict[str, Any]:
        """
        Validate best practices of the HTML and CSS.
        
        Args:
            html_output: HTML content
            css_output: CSS content
            
        Returns:
            Dictionary containing best practices validation results
        """
        issues = []
        score = 100
        
        # Check for doctype declaration
        if '<!DOCTYPE html>' not in html_output:
            issues.append({
                "rule": "doctype",
                "impact": "medium",
                "description": "Document does not have a valid doctype declaration",
                "help": "Add <!DOCTYPE html> at the beginning of the HTML document"
            })
            score -= 10
        
        # Check for character encoding
        if '<meta charset="utf-8">' not in html_output and '<meta charset="UTF-8">' not in html_output:
            issues.append({
                "rule": "charset",
                "impact": "medium",
                "description": "Document does not have a character encoding declaration",
                "help": "Add <meta charset=\"utf-8\"> to the document head"
            })
            score -= 10
        
        # Check for deprecated HTML tags
        deprecated_tags = ['applet', 'basefont', 'center', 'dir', 'font', 'isindex', 'menu', 's', 'strike', 'u']
        for tag in deprecated_tags:
            pattern = r'<' + tag + r'[^>]*>'
            if re.search(pattern, html_output):
                issues.append({
                    "rule": "deprecated-tags",
                    "impact": "low",
                    "description": f"Use of deprecated HTML tag: {tag}",
                    "help": f"Replace the deprecated {tag} tag with modern HTML and CSS"
                })
                score -= 5
                break
        
        # Check for inline styles
        inline_styles = re.findall(r'style=["\'][^"\']*["\']', html_output)
        if len(inline_styles) > 5:
            issues.append({
                "rule": "inline-styles",
                "impact": "low",
                "description": "Excessive use of inline styles",
                "help": "Move inline styles to an external stylesheet",
                "count": len(inline_styles)
            })
            score -= 5
        
        # Check for console logs
        console_logs = re.findall(r'console\.log\(', html_output)
        if console_logs:
            issues.append({
                "rule": "console-logs",
                "impact": "low",
                "description": "Console logs detected",
                "help": "Remove console logs from production code",
                "count": len(console_logs)
            })
            score -= 3
            
        # Check for CSS vendor prefixes
        vendor_prefixes = re.findall(r'(-webkit-|-moz-|-ms-|-o-)[a-zA-Z-]+\s*:', css_output)
        if vendor_prefixes and len(vendor_prefixes) > 10:
            issues.append({
                "rule": "vendor-prefixes",
                "impact": "low",
                "description": "Excessive use of vendor prefixes",
                "help": "Consider using autoprefixer or similar tools",
                "count": len(vendor_prefixes)
            })
            score -= 3
            
        # Check for !important usage
        important_count = css_output.count('!important')
        if important_count > 5:
            issues.append({
                "rule": "important-usage",
                "impact": "medium",
                "description": "Excessive use of !important",
                "help": "Avoid using !important in CSS",
                "count": important_count
            })
            score -= 5
            
        # Ensure the score is within bounds
        score = max(0, min(100, score))
            
        # Check if the best practices score meets the threshold
        passed = score >= self.best_practices_threshold
        
        return {
            "score": score,
            "passed": passed,
            "issues": issues,
            "threshold": self.best_practices_threshold
        }
    
    async def _calculate_quality_score(
        self,
        accessibility_results: Dict[str, Any],
        seo_results: Dict[str, Any],
        performance_results: Dict[str, Any],
        best_practices_results: Dict[str, Any]
    ) -> float:
        """
        Calculate an overall quality score based on individual validation results.
        
        Args:
            accessibility_results: Accessibility validation results
            seo_results: SEO validation results
            performance_results: Performance validation results
            best_practices_results: Best practices validation results
            
        Returns:
            Overall quality score between 0 and 100
        """
        # Get individual scores
        accessibility_score = accessibility_results.get("score", 0)
        seo_score = seo_results.get("score", 0)
        performance_score = performance_results.get("score", 0)
        best_practices_score = best_practices_results.get("score", 0)
        
        # Calculate weighted average
        # Accessibility and performance are weighted more heavily
        weighted_score = (
            (accessibility_score * 0.35) +
            (performance_score * 0.30) +
            (seo_score * 0.20) +
            (best_practices_score * 0.15)
        )
        
        # Round to 1 decimal place
        return round(weighted_score, 1)
    
    async def _generate_validation_report(
        self,
        accessibility_results: Dict[str, Any],
        seo_results: Dict[str, Any],
        performance_results: Dict[str, Any],
        best_practices_results: Dict[str, Any],
        quality_score: float
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.
        
        Args:
            accessibility_results: Accessibility validation results
            seo_results: SEO validation results
            performance_results: Performance validation results
            best_practices_results: Best practices validation results
            quality_score: Overall quality score
            
        Returns:
            Dictionary containing the validation report
        """
        # Determine overall status
        status = "PASS" if quality_score >= 90 else "FAIL"
        
        # Compile all issues for the report
        all_issues = []
        all_issues.extend([{**issue, "category": "accessibility"} for issue in accessibility_results.get("issues", [])])
        all_issues.extend([{**issue, "category": "seo"} for issue in seo_results.get("issues", [])])
        all_issues.extend([{**issue, "category": "performance"} for issue in performance_results.get("issues", [])])
        all_issues.extend([{**issue, "category": "best-practices"} for issue in best_practices_results.get("issues", [])])
        
        # Sort issues by impact
        impact_priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_issues = sorted(all_issues, key=lambda x: impact_priority.get(x.get("impact", "low"), 3))
        
        # Generate improvement recommendations
        recommendations = []
        
        # Add recommendations for critical and high impact issues
        for issue in sorted_issues:
            if issue.get("impact") in ["critical", "high"]:
                recommendations.append({
                    "category": issue.get("category"),
                    "rule": issue.get("rule"),
                    "recommendation": issue.get("help")
                })
        
        # Generate summary metrics
        metrics = {
            "accessibility": {
                "score": accessibility_results.get("score"),
                "passed": accessibility_results.get("passed"),
                "issueCount": len(accessibility_results.get("issues", []))
            },
            "seo": {
                "score": seo_results.get("score"),
                "passed": seo_results.get("passed"),
                "issueCount": len(seo_results.get("issues", []))
            },
            "performance": {
                "score": performance_results.get("score"),
                "passed": performance_results.get("passed"),
                "issueCount": len(performance_results.get("issues", []))
            },
            "bestPractices": {
                "score": best_practices_results.get("score"),
                "passed": best_practices_results.get("passed"),
                "issueCount": len(best_practices_results.get("issues", []))
            }
        }
        
        return {
            "status": status,
            "qualityScore": quality_score,
            "timestamp": None,  # Will be set by the calling service
            "metrics": metrics,
            "issues": sorted_issues[:10],  # Limit to top 10 issues
            "recommendationCount": len(recommendations),
            "recommendations": recommendations
        }
