import os
from typing import Dict, Any, List
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class LLMWebsiteCloner:
    def __init__(self, model="claude-3.5"):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        
        # Model selection
        if model == "claude-4":
            self.model_name = "claude-sonnet-4-20250514"
        else:
            self.model_name = "claude-3-5-sonnet-20241022"
        
    async def clone_website(self, scrape_data: Dict[str, Any]) -> str:
        """
        Use Claude to analyze the scraped website data and generate a cloned HTML page
        """
        # Prepare the context for Claude
        context = self._prepare_context(scrape_data)
        
        # Create the prompt for Claude
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(context)
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=8000,
                temperature=0.1,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract HTML from response
            html_content = response.content[0].text
            
            # Clean up the response to extract just the HTML
            html_content = self._extract_html_from_response(html_content)
            
            # Post-process the HTML for better quality
            html_content = self._post_process_html(html_content)
            
            return html_content
            
        except Exception as e:
            raise Exception(f"LLM cloning failed: {str(e)}")
    
    def _prepare_context(self, scrape_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and clean the scraped data for LLM consumption"""
        
        # Remove base64 screenshots to reduce token usage
        screenshots_info = {}
        if "screenshots" in scrape_data:
            for device, screenshot_b64 in scrape_data["screenshots"].items():
                screenshots_info[device] = {
                    "has_screenshot": True,
                    "size_kb": len(screenshot_b64) // 1024 if screenshot_b64 else 0
                }
        
        return {
            "url": scrape_data.get("url", ""),
            "title": scrape_data.get("title", ""),
            "screenshots_info": screenshots_info,
            "html_structure": {
                "headings": scrape_data.get("html_structure", {}).get("headings", []),
                "navigation": scrape_data.get("html_structure", {}).get("navigation", []),
                "body_html_preview": scrape_data.get("html_structure", {}).get("body_html", "")[:4000],
                "sections": scrape_data.get("html_structure", {}).get("sections", []),
                "semantic_tags": scrape_data.get("html_structure", {}).get("semantic_tags", {})
            },
            "text_content": scrape_data.get("text_content", {}),
            "media_content": scrape_data.get("media_content", {}),
            "colors": scrape_data.get("colors", [])[:15],
            "fonts": scrape_data.get("fonts", [])[:5],
            "layout": scrape_data.get("layout_analysis", {}),
            "components": scrape_data.get("components", {}),
            "interactions": scrape_data.get("interactions", {}),
            "responsive_behavior": scrape_data.get("responsive_behavior", {}),
            "visual_hierarchy": scrape_data.get("visual_hierarchy", {}),
            "meta_info": scrape_data.get("meta_info", {}),
        }
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for Claude"""
        return """You are an expert web developer and designer with years of experience creating pixel-perfect HTML replicas of websites. Your mission is to analyze comprehensive website data and generate a complete, standalone HTML page that replicates the original design with exceptional accuracy.

CORE PRINCIPLES:
1. **Visual Fidelity**: Recreate the exact visual appearance - layouts, spacing, colors, typography, shadows
2. **Modern Standards**: Use semantic HTML5, CSS Grid, Flexbox, CSS custom properties, modern CSS features
3. **Component Design**: Create reusable, modular components with clean CSS architecture
4. **Responsive Excellence**: Ensure flawless behavior across all devices with mobile-first approach
5. **Interactive Polish**: Include hover effects, transitions, and smooth animations
6. **Performance**: Efficient CSS, minimal redundancy, fast loading
7. **Accessibility**: Proper semantic markup, ARIA labels, keyboard navigation

TECHNICAL REQUIREMENTS:
- Create a complete, self-contained HTML document with internal CSS
- Use CSS custom properties (--variables) for consistent theming
- Implement CSS Grid for layouts, Flexbox for component alignment
- Use modern CSS functions: clamp(), min(), max(), calc() for responsive design
- Include smooth transitions and micro-interactions
- Ensure pixel-perfect spacing using consistent spacing scale
- Implement proper semantic HTML structure
- Use CSS animations for dynamic elements
- Include hover and focus states for interactive elements
- Make it production-ready with clean, well-commented CSS

OUTPUT FORMAT:
Respond with ONLY the complete HTML document. Start with <!DOCTYPE html> and end with </html>. Include no explanations, markdown formatting, or additional text - just the pure HTML code."""
    
    def _create_user_prompt(self, context: Dict[str, Any]) -> str:
        """Create the user prompt with website context"""
        
        prompt = f"""WEBSITE CLONING REQUEST

Target Website: {context['url']}
Page Title: {context['title']}

=== VISUAL HIERARCHY ===
{json.dumps(context.get('visual_hierarchy', {}), indent=2)}

=== LAYOUT STRUCTURE ===
Layout Analysis:
{json.dumps(context.get('layout', {}), indent=2)}

Responsive Breakpoints:
{json.dumps(context.get('responsive_behavior', {}), indent=2)}

=== UI COMPONENTS IDENTIFIED ===
{json.dumps(context.get('components', {}), indent=2)}

=== DESIGN SYSTEM ===
Primary Colors (use these exact colors):
{context.get('colors', [])[:8]}

Typography Stack:
{context.get('fonts', [])[:3]}

=== CONTENT STRUCTURE ===
Navigation Items: {context.get('html_structure', {}).get('navigation', [])[:10]}
Headings Hierarchy: {context.get('html_structure', {}).get('headings', [])[:15]}

Text Content:
{json.dumps(context.get('text_content', {}), indent=2)}

Media Content:
{json.dumps(context.get('media_content', {}), indent=2)}

=== INTERACTIVE ELEMENTS ===
{json.dumps(context.get('interactions', {}), indent=2)}

=== HTML STRUCTURE REFERENCE ===
```html
{context.get('html_structure', {}).get('body_html_preview', '')}
```

=== CLONING REQUIREMENTS ===

1. **Exact Visual Recreation**: Match the layout, spacing, colors, and typography precisely
2. **Component Fidelity**: Recreate all identified UI components (buttons, cards, forms, navigation)
3. **Responsive Behavior**: Implement the responsive patterns observed at different breakpoints
4. **Interactive States**: Include hover effects, focus states, and transitions
5. **Modern Implementation**: Use CSS Grid for layouts, Flexbox for components, CSS custom properties for theming
6. **Content Strategy**: Use meaningful placeholder content that matches the original's tone and structure
7. **Performance**: Optimize CSS with efficient selectors and minimal redundancy

Generate a complete, production-ready HTML page that perfectly replicates this website's design and functionality."""

        return prompt
    
    def _extract_html_from_response(self, response: str) -> str:
        """Extract HTML from Claude's response"""
        # Look for HTML content
        if "```html" in response:
            start = response.find("```html") + 7
            end = response.find("```", start)
            html = response[start:end].strip()
        elif "<!DOCTYPE html" in response:
            start = response.find("<!DOCTYPE html")
            html = response[start:].strip()
        else:
            # If no clear HTML markers, assume the whole response is HTML
            html = response.strip()
        
        # Clean up any trailing text after </html>
        if "</html>" in html:
            end = html.rfind("</html>") + 7
            html = html[:end]
        
        return html
    
    def _post_process_html(self, html: str) -> str:
        """Post-process the HTML for better quality"""
        # Ensure DOCTYPE
        if not html.startswith("<!DOCTYPE html"):
            html = "<!DOCTYPE html>\n" + html
        
        # Basic validation - ensure we have html, head, and body tags
        if "<html" not in html:
            html = f"<!DOCTYPE html>\n<html>\n<head>\n<title>Cloned Website</title>\n</head>\n<body>\n{html}\n</body>\n</html>"
        elif "<head>" not in html and "<body>" not in html:
            # Wrap in head and body if missing
            html = html.replace("<html>", "<html>\n<head>\n<title>Cloned Website</title>\n</head>\n<body>")
            html = html.replace("</html>", "</body>\n</html>")
        
        return html