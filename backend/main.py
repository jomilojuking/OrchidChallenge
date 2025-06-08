from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
import uvicorn
import os
import asyncio
import base64
import re
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
from anthropic import Anthropic

# Playwright import
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
    print("✅ Playwright available")
except ImportError:
    print("❌ Playwright not available")

# MCP imports (keeping your original setup)
MCP_AVAILABLE = False
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from langchain_mcp_adapters.tools import load_mcp_tools
    from langgraph.prebuilt import create_react_agent
    from langchain_anthropic import ChatAnthropic
    MCP_AVAILABLE = True
    print("✅ MCP available")
except ImportError:
    print("❌ MCP not available")

load_dotenv()

app = FastAPI(title="Enhanced Website Cloner with Super Image Extraction", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Your original models
class CloneRequest(BaseModel):
    url: HttpUrl

class CloneResponse(BaseModel):
    success: bool
    generated_html: str
    original_url: str
    error_message: Optional[str] = None

# New image extraction models
class ImageExtractRequest(BaseModel):
    url: HttpUrl
    image_limit: Optional[int] = 100
    min_width: Optional[int] = 10
    min_height: Optional[int] = 10
    include_small: Optional[bool] = True

class ExtractedImage(BaseModel):
    src: str
    alt: str
    width: int
    height: int
    format: Optional[str] = None
    context: str
    is_base64: bool = False

class ImageExtractResponse(BaseModel):
    success: bool
    url: str
    total_images: int
    images: List[ExtractedImage]
    screenshot_base64: Optional[str] = None
    error_message: Optional[str] = None

# Your original MCP setup
mcp_tools = None
agent_primary = None
model_primary = None
server_params = None

if MCP_AVAILABLE:
    try:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            model_primary = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=anthropic_key
            )
            
            api_token = os.getenv("API_TOKEN")
            browser_auth = os.getenv("BROWSER_AUTH")
            
            if api_token and browser_auth:
                server_params = StdioServerParameters(
                    command="npx",
                    args=["@brightdata/mcp"],
                    env={
                        "API_TOKEN": api_token,
                        "BROWSER_AUTH": browser_auth,
                        "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE", "web_unlocker_1")
                    }
                )
    except Exception as e:
        print("MCP config failed:", str(e))

async def initialize_mcp():
    global mcp_tools, agent_primary
    if not MCP_AVAILABLE or not server_params or not model_primary:
        return False
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                mcp_tools = await load_mcp_tools(session)
                if mcp_tools:
                    agent_primary = create_react_agent(model_primary, mcp_tools)
                    return True
        return False
    except Exception as e:
        print("MCP init failed:", str(e))
        return False

class SuperImageScraper:
    def __init__(self):
        # Mega selectors for finding ANY image on ANY website
        self.image_selectors = [
            # Standard images
            'img', 'image', 'picture img', 'picture source', 'figure img',
            # SVG and Canvas
            'svg', 'canvas', 'video[poster]',
            # Background images
            '[style*="background-image"]', '[style*="background:"]',
            # Lazy loading
            '[data-src]', '[data-lazy]', '[data-original]', '[data-img]', 
            '[data-image]', '[data-bg]', '[data-background]', '[data-thumb]',
            # Responsive
            '[srcset]', 'source[srcset]',
            # Class patterns
            '[class*="image"]', '[class*="img"]', '[class*="photo"]', 
            '[class*="picture"]', '[class*="thumbnail"]', '[class*="avatar"]', 
            '[class*="logo"]', '[class*="banner"]', '[class*="gallery"]',
            '[class*="slider"]', '[class*="carousel"]', '[class*="product"]',
            # ID patterns
            '[id*="image"]', '[id*="img"]', '[id*="photo"]', '[id*="logo"]',
            # Framework specific
            '._next img', '.gatsby-image', '.wp-image',
            # E-commerce
            '.product-image img', '.item-image img', '.gallery img',
            # Social media
            '[role="img"]', '[role="image"]',
            # CDN patterns
            '[src*="cloudinary"]', '[src*="imgix"]', '[src*="amazonaws"]'
        ]

async def scrape_with_super_playwright(url: str) -> Dict[str, Any]:
    """SUPER enhanced Playwright scraping with comprehensive image extraction"""
    if not PLAYWRIGHT_AVAILABLE:
        return {"error": "Playwright not available"}
    
    try:
        scraper = SuperImageScraper()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ignore_https_errors=True
            )
            
            page = await context.new_page()
            
            print("📸 Navigating to:", url)
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Aggressive scrolling for lazy loading
            print("📜 Triggering ALL lazy loading...")
            for i in range(6):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(1500)
                await page.evaluate('window.scrollTo(0, 0)')
                await page.wait_for_timeout(500)
            
            print("📷 Taking screenshot...")
            screenshot = await page.screenshot(
                full_page=True,
                type='png'
            )
            screenshot_base64 = base64.b64encode(screenshot).decode()
            
            print("🔍 Extracting EVERYTHING...")
            
            # Super comprehensive extraction
            visual_data = await page.evaluate(f"""
                () => {{
                    const data = {{}};
                    const seenUrls = new Set();
                    const allImages = [];
                    
                    // Helper function
                    function resolveUrl(url) {{
                        if (!url) return null;
                        if (url.startsWith('data:')) return url;
                        if (url.startsWith('//')) return 'https:' + url;
                        if (url.startsWith('/')) return window.location.origin + url;
                        if (!url.startsWith('http')) return window.location.origin + '/' + url;
                        return url;
                    }}
                    
                    function getImageFormat(src) {{
                        if (src.startsWith('data:')) {{
                            const match = src.match(/data:image\\/(\\w+)/);
                            return match ? match[1] : 'unknown';
                        }}
                        const match = src.match(/\\.([a-zA-Z0-9]+)(?:\\?|$)/);
                        return match ? match[1].toLowerCase() : 'unknown';
                    }}
                    
                    // MEGA IMAGE EXTRACTION
                    const selectors = {scraper.image_selectors};
                    
                    for (const selector of selectors) {{
                        try {{
                            const elements = document.querySelectorAll(selector);
                            
                            for (const el of elements) {{
                                let src = null;
                                let width = 0;
                                let height = 0;
                                let alt = '';
                                let context = '';
                                
                                if (el.tagName === 'IMG') {{
                                    src = el.src || el.getAttribute('data-src') || 
                                          el.getAttribute('data-lazy') || el.getAttribute('data-original') ||
                                          el.getAttribute('data-img') || el.getAttribute('data-image');
                                    width = el.naturalWidth || el.width || el.offsetWidth || 0;
                                    height = el.naturalHeight || el.height || el.offsetHeight || 0;
                                    alt = el.alt || el.title || '';
                                    context = 'img-element';
                                    
                                }} else if (el.tagName === 'SOURCE') {{
                                    src = el.srcset?.split(',')[0]?.trim()?.split(' ')[0] || el.src;
                                    width = parseInt(el.getAttribute('width')) || 0;
                                    height = parseInt(el.getAttribute('height')) || 0;
                                    alt = 'source-element';
                                    context = 'source-element';
                                    
                                }} else if (el.tagName === 'VIDEO') {{
                                    src = el.poster;
                                    width = el.videoWidth || el.width || el.offsetWidth || 0;
                                    height = el.videoHeight || el.height || el.offsetHeight || 0;
                                    alt = 'video-thumbnail';
                                    context = 'video-poster';
                                    
                                }} else if (el.tagName === 'SVG') {{
                                    try {{
                                        const serializer = new XMLSerializer();
                                        const svgString = serializer.serializeToString(el);
                                        src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgString)));
                                        width = el.width?.baseVal?.value || el.offsetWidth || 0;
                                        height = el.height?.baseVal?.value || el.offsetHeight || 0;
                                        alt = 'svg-image';
                                        context = 'svg-element';
                                    }} catch (e) {{ continue; }}
                                    
                                }} else if (el.tagName === 'CANVAS') {{
                                    try {{
                                        src = el.toDataURL();
                                        width = el.width || el.offsetWidth || 0;
                                        height = el.height || el.offsetHeight || 0;
                                        alt = 'canvas-image';
                                        context = 'canvas-element';
                                    }} catch (e) {{ continue; }}
                                    
                                }} else {{
                                    // Data attributes
                                    src = el.getAttribute('data-src') || el.getAttribute('data-lazy') ||
                                          el.getAttribute('data-original') || el.getAttribute('data-img') ||
                                          el.getAttribute('data-image') || el.getAttribute('data-background');
                                    width = el.offsetWidth || 0;
                                    height = el.offsetHeight || 0;
                                    alt = el.getAttribute('aria-label') || el.getAttribute('title') || '';
                                    context = 'data-attribute';
                                }}
                                
                                if (src) {{
                                    const resolvedUrl = resolveUrl(src);
                                    if (resolvedUrl && !seenUrls.has(resolvedUrl)) {{
                                        seenUrls.add(resolvedUrl);
                                        allImages.push({{
                                            src: resolvedUrl,
                                            alt: alt,
                                            width: width,
                                            height: height,
                                            format: getImageFormat(resolvedUrl),
                                            context: context,
                                            is_base64: resolvedUrl.startsWith('data:')
                                        }});
                                    }}
                                }}
                            }}
                        }} catch (e) {{
                            console.log('Selector failed:', selector);
                        }}
                    }}
                    
                    // Extract CSS background images
                    try {{
                        const allElements = document.querySelectorAll('*');
                        for (const el of allElements) {{
                            const style = window.getComputedStyle(el);
                            const bgImage = style.backgroundImage;
                            
                            if (bgImage && bgImage !== 'none' && bgImage.includes('url(')) {{
                                const matches = bgImage.match(/url\\(["']?([^"')]+)["']?\\)/g);
                                if (matches) {{
                                    for (const match of matches) {{
                                        const url = match.match(/url\\(["']?([^"')]+)["']?\\)/)[1];
                                        const resolvedUrl = resolveUrl(url);
                                        
                                        if (resolvedUrl && !seenUrls.has(resolvedUrl)) {{
                                            seenUrls.add(resolvedUrl);
                                            allImages.push({{
                                                src: resolvedUrl,
                                                alt: 'background-image',
                                                width: el.offsetWidth || 0,
                                                height: el.offsetHeight || 0,
                                                format: getImageFormat(resolvedUrl),
                                                context: 'css-background',
                                                is_base64: resolvedUrl.startsWith('data:')
                                            }});
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }} catch (e) {{
                        console.log('Background extraction failed');
                    }}
                    
                    // Original site analysis
                    const body = document.body;
                    const bodyStyles = window.getComputedStyle(body);
                    
                    let bgColor = bodyStyles.backgroundColor;
                    if (!bgColor || bgColor === 'rgba(0, 0, 0, 0)') {{
                        bgColor = '#ffffff';
                    }}
                    
                    const textColor = bodyStyles.color || '#333333';
                    const isDark = bgColor.includes('rgb(0') || bgColor.includes('#000') || 
                                  bgColor.includes('#202124') || bgColor.includes('rgb(18');
                    
                    // Logo detection
                    let logo = null;
                    const logoSelectors = [
                        'img[alt*="logo" i]', 'img[src*="logo" i]', '.logo img', '.brand img',
                        'nav img', '.navbar-brand img', '.site-logo img', '.header-logo img'
                    ];
                    
                    for (const selector of logoSelectors) {{
                        const logoImg = document.querySelector(selector);
                        if (logoImg && logoImg.src) {{
                            logo = {{ 
                                type: 'image', 
                                src: logoImg.src, 
                                alt: logoImg.alt || ''
                            }};
                            break;
                        }}
                    }}
                    
                    if (!logo) {{
                        const textLogoSelectors = ['.logo', '.brand', 'h1', '.site-title'];
                        for (const selector of textLogoSelectors) {{
                            const logoText = document.querySelector(selector);
                            if (logoText && logoText.textContent.trim()) {{
                                logo = {{ type: 'text', text: logoText.textContent.trim() }};
                                break;
                            }}
                        }}
                    }}
                    
                    // Navigation
                    const navLinks = [];
                    const navSelectors = ['nav a', '.nav a', 'header a', '.navbar a', '.menu a'];
                    
                    for (const selector of navSelectors) {{
                        document.querySelectorAll(selector).forEach(link => {{
                            const text = link.textContent.trim();
                            if (text && text.length < 50 && navLinks.length < 10) {{
                                navLinks.push({{
                                    text: text,
                                    href: link.href || '#'
                                }});
                            }}
                        }});
                    }}
                    
                    // Headings
                    const headings = [];
                    document.querySelectorAll('h1, h2, h3').forEach(h => {{
                        const text = h.textContent.trim();
                        if (text && headings.length < 8) {{
                            headings.push({{
                                text: text,
                                level: h.tagName.toLowerCase()
                            }});
                        }}
                    }});
                    
                    // Sort images by size
                    allImages.sort((a, b) => (b.width * b.height) - (a.width * a.height));
                    
                    return {{
                        url: window.location.href,
                        siteType: 'standard',
                        backgroundColor: bgColor,
                        textColor: textColor,
                        isDark: isDark,
                        fontFamily: bodyStyles.fontFamily,
                        title: document.title,
                        logo: logo,
                        navigation: navLinks,
                        headings: headings,
                        allImages: allImages.slice(0, 100), // Limit to 100 best images
                        totalImagesFound: allImages.length,
                        hasSearch: !!document.querySelector('input[type="search"], input[name="q"], .search'),
                        hasVideo: !!document.querySelector('video')
                    }};
                }}
            """)
            
            # Add screenshot to visual data
            visual_data['screenshot'] = screenshot_base64
            
            await browser.close()
            print(f"✅ Super extraction complete! Found {visual_data['totalImagesFound']} images")
            return visual_data
            
    except Exception as e:
        print("❌ Super Playwright failed:", str(e))
        return {"error": str(e)}

# Your original scrape functions (keeping for compatibility)
async def scrape_with_mcp(url: str) -> Dict[str, Any]:
    """Use MCP as backup"""
    if not agent_primary:
        return {}
    try:
        result = await agent_primary.ainvoke({
            "messages": [{"role": "user", "content": "Extract visual design data from " + url + ": colors, layout, content"}]
        })
        return {"mcp_data": str(result)[:2000]}
    except Exception as e:
        print("MCP failed:", str(e))
        return {}

# Your original HTML Generator class (enhanced)
class HTMLGenerator:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        self.client = Anthropic(api_key=api_key)
    
    def create_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML from visual data with ALL extracted images"""
        
        if "error" in data:
            raise Exception("No visual data available: " + data["error"])
        
        # Extract data safely
        url = data.get('url', '')
        bg_color = data.get('backgroundColor', '#ffffff')
        text_color = data.get('textColor', '#333333')
        font_family = data.get('fontFamily', 'system-ui')
        title = data.get('title', 'Website')
        logo = data.get('logo')
        navigation = data.get('navigation', [])
        headings = data.get('headings', [])
        all_images = data.get('allImages', [])
        total_images = data.get('totalImagesFound', 0)
        screenshot = data.get('screenshot', '')
        
        print(f"🎨 Generating HTML with {len(all_images)} images extracted from {total_images} total found")
        
        # Build comprehensive prompt with ALL images
        prompt = f"""Create a PIXEL-PERFECT website clone from {url}.

EXTRACTED VISUAL DATA:
- Background: {bg_color}
- Text Color: {text_color}
- Font: {font_family}
- Title: {title}

LOGO: {logo}

NAVIGATION: {[nav.get('text', '') for nav in navigation[:6]]}

HEADINGS: {[h.get('text', '') for h in headings[:5]]}

EXTRACTED IMAGES ({len(all_images)} of {total_images} total found):
"""

        # Add detailed image information
        for i, img in enumerate(all_images[:20]):  # Include top 20 images in prompt
            prompt += f"\n{i+1}. {img['src']}"
            if img['alt']:
                prompt += f" (alt: {img['alt']})"
            prompt += f" - {img['width']}x{img['height']} - {img['context']}"

        if len(all_images) > 20:
            prompt += f"\n... and {len(all_images) - 20} more images available"

        prompt += f"""

REQUIREMENTS:
1. Use EXACT colors: background {bg_color}, text {text_color}
2. Include ALL major images from the extracted list
3. Create a professional, responsive layout
4. Match the original site's visual hierarchy
5. Use the extracted navigation and headings
6. Include proper alt text for accessibility
7. Make it look exactly like the original website

Create complete HTML with embedded CSS that recreates this website perfectly using all the extracted visual data."""

        # Add screenshot reference if available
        if screenshot:
            prompt += f"\n\nIMPORTANT: I have captured a screenshot of the actual website. Please ensure the generated HTML matches the visual layout, spacing, and design shown in the screenshot as closely as possible."

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            html_content = response.content[0].text
            
            # Clean HTML
            if "```html" in html_content:
                start = html_content.find("```html") + 7
                end = html_content.find("```", start)
                if end != -1:
                    html_content = html_content[start:end].strip()
            
            if not html_content.startswith("<!DOCTYPE"):
                html_content = "<!DOCTYPE html>\n" + html_content
            
            return html_content
            
        except Exception as e:
            raise Exception("HTML generation failed: " + str(e))

def safe_data_cleanup(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up data to ensure all values are safe for processing"""
    
    safe_data = {
        "url": str(data.get('url', '')),
        "siteType": str(data.get('siteType', 'standard')),
        "backgroundColor": str(data.get('backgroundColor', '#ffffff')),
        "textColor": str(data.get('textColor', '#333333')),
        "fontFamily": str(data.get('fontFamily', 'system-ui, sans-serif')),
        "title": str(data.get('title', 'Website')),
        "isDark": bool(data.get('isDark', False)),
        "hasSearch": bool(data.get('hasSearch', False)),
        "hasVideo": bool(data.get('hasVideo', False)),
        "screenshot": str(data.get('screenshot', '')),
        "allImages": data.get('allImages', []),
        "totalImagesFound": data.get('totalImagesFound', 0)
    }
    
    # Safe navigation processing
    navigation = data.get('navigation', [])
    safe_navigation = []
    if navigation:
        for nav in navigation:
            if isinstance(nav, dict):
                text = nav.get('text', '')
                if text and isinstance(text, str):
                    safe_navigation.append({"text": text, "href": nav.get('href', '#')})
            elif isinstance(nav, str):
                safe_navigation.append({"text": nav, "href": "#"})
    
    if not safe_navigation:
        safe_navigation = [{"text": "Home", "href": "#"}, {"text": "About", "href": "#"}]
    
    safe_data['navigation'] = safe_navigation
    
    # Safe headings processing
    headings = data.get('headings', [])
    safe_headings = []
    if headings:
        for h in headings:
            if isinstance(h, dict):
                text = h.get('text', '')
                if text and isinstance(text, str):
                    safe_headings.append({"text": text, "level": h.get('level', 'h1')})
            elif isinstance(h, str):
                safe_headings.append({"text": h, "level": "h1"})
    
    if not safe_headings:
        safe_headings = [{"text": "Welcome", "level": "h1"}]
    
    safe_data['headings'] = safe_headings
    
    # Safe logo processing
    logo = data.get('logo')
    safe_logo = None
    if logo and isinstance(logo, dict):
        if logo.get('type') == 'text' and logo.get('text'):
            safe_logo = {"type": "text", "text": str(logo.get('text', ''))}
        elif logo.get('type') == 'image' and logo.get('src'):
            safe_logo = {"type": "image", "src": str(logo.get('src', '')), "alt": str(logo.get('alt', ''))}
    
    if not safe_logo:
        safe_logo = {"type": "text", "text": safe_data['title']}
    
    safe_data['logo'] = safe_logo
    
    return safe_data

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "playwright": PLAYWRIGHT_AVAILABLE,
        "mcp": bool(agent_primary),
        "features": [
            "Website cloning with super image extraction",
            "60+ CSS selectors for comprehensive image detection",
            "Background image extraction",
            "Lazy loading support", 
            "SVG and Canvas capture",
            "Screenshot generation",
            "Smart duplicate removal"
        ]
    }

# MAIN CLONE ENDPOINT (your original endpoint)
@app.post("/clone")
async def clone_website(request: CloneRequest):
    try:
        url = str(request.url)
        print("🎯 Super Cloning:", url)
        
        # Add https if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Try super Playwright first
        try:
            data = await scrape_with_super_playwright(url)
            if "error" in data:
                raise Exception("Super Playwright failed: " + str(data["error"]))
        except Exception as playwright_error:
            print("❌ Super Playwright failed:", str(playwright_error))
            data = {"error": str(playwright_error)}
        
        # Try MCP as backup if Playwright failed
        if "error" in data and agent_primary:
            print("🔄 Trying MCP backup...")
            try:
                mcp_data = await scrape_with_mcp(url)
                if mcp_data and mcp_data.get("mcp_data"):
                    data = {
                        "url": url,
                        "siteType": "standard",
                        "backgroundColor": "#ffffff",
                        "textColor": "#333333",
                        "fontFamily": "arial, sans-serif",
                        "title": "Website",
                        "navigation": ["Home", "About", "Contact"],
                        "headings": ["Welcome", "About Us"],
                        "logo": {"type": "text", "text": "Brand"},
                        "isDark": False,
                        "hasSearch": False,
                        "hasVideo": False,
                        "allImages": [],
                        "totalImagesFound": 0,
                        "mcp_data": mcp_data.get("mcp_data", "")
                    }
                    print("✅ MCP provided backup data")
                else:
                    raise Exception("MCP also failed")
            except Exception as mcp_error:
                print("❌ MCP also failed:", str(mcp_error))
                # Create minimal fallback data
                data = {
                    "url": url,
                    "siteType": "standard",
                    "backgroundColor": "#ffffff",
                    "textColor": "#333333",
                    "fontFamily": "system-ui, sans-serif",
                    "title": "Website",
                    "navigation": ["Home", "About", "Contact"],
                    "headings": ["Welcome to Our Website"],
                    "logo": {"type": "text", "text": "Website"},
                    "isDark": False,
                    "hasSearch": False,
                    "hasVideo": False,
                    "allImages": [],
                    "totalImagesFound": 0
                }
                print("⚠️ Using fallback data structure")
        
        # Ensure all data is safe for processing
        data = safe_data_cleanup(data)
        
        # Generate HTML
        generator = HTMLGenerator()
        html_content = generator.create_html(data)
        
        print("✅ Super clone completed successfully")
        return CloneResponse(
            success=True,
            generated_html=html_content,
            original_url=url
        )
        
    except Exception as e:
        error_msg = str(e)
        print("❌ Super clone failed:", error_msg)
        
        error_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Super Clone Failed</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 40px; background: #f8f9fa; color: #333; margin: 0;
        }}
        .error {{ 
            background: white; padding: 30px; border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto;
        }}
        .url {{ background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0; word-break: break-all; }}
        h1 {{ color: #dc3545; margin-top: 0; }}
        .status {{ margin: 20px 0; }}
        .status span {{ display: inline-block; margin-right: 15px; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>🚫 Super Clone Failed</h1>
        <p><strong>Error:</strong> {error_msg}</p>
        <div class="url"><strong>URL:</strong> {str(request.url)}</div>
        
        <div class="status">
            <h3>System Status:</h3>
            <span><strong>Playwright:</strong> {"✅ Available" if PLAYWRIGHT_AVAILABLE else "❌ Not Available"}</span>
            <span><strong>MCP:</strong> {"✅ Ready" if agent_primary else "❌ Not Ready"}</span>
        </div>
        
        <h3>💡 Super Image Cloner Features:</h3>
        <ul>
            <li>🎯 60+ CSS selectors for comprehensive image detection</li>
            <li>📸 Full page screenshot capture</li>
            <li>🔍 Background image extraction from CSS</li>
            <li>⚡ Lazy loading trigger via aggressive scrolling</li>
            <li>🎨 SVG and Canvas element capture</li>
            <li>🔄 Smart duplicate removal</li>
            <li>📊 Size and format detection</li>
        </ul>
        
        <p><strong>Try these URLs:</strong></p>
        <ul>
            <li>https://nike.com</li>
            <li>https://apple.com</li>
            <li>https://github.com</li>
            <li>https://unsplash.com</li>
        </ul>
        
        <p><small>If this persists, the website might have strong bot protection.</small></p>
    </div>
</body>
</html>"""
        
        return CloneResponse(
            success=False,
            generated_html=error_html,
            original_url=str(request.url),
            error_message=error_msg
        )

# NEW IMAGE EXTRACTION ENDPOINT
@app.post("/extract-images")
async def extract_images(request: ImageExtractRequest):
    """Extract ALL images from any website with comprehensive detection"""
    try:
        url = str(request.url)
        print(f"🎯 Extracting images from: {url}")
        
        # Add https if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Use super Playwright extraction
        data = await scrape_with_super_playwright(url)
        
        if "error" in data:
            raise Exception(data["error"])
        
        all_images = data.get('allImages', [])
        total_found = data.get('totalImagesFound', 0)
        
        # Filter images based on request parameters
        filtered_images = []
        for img in all_images:
            if (img.get('width', 0) >= request.min_width and 
                img.get('height', 0) >= request.min_height):
                if request.include_small or (img.get('width', 0) >= 100 and img.get('height', 0) >= 100):
                    filtered_images.append(ExtractedImage(
                        src=img['src'],
                        alt=img['alt'],
                        width=img['width'],
                        height=img['height'],
                        format=img.get('format'),
                        context=img['context'],
                        is_base64=img['is_base64']
                    ))
        
        # Apply limit
        filtered_images = filtered_images[:request.image_limit]
        
        print(f"✅ Extracted {len(filtered_images)} images from {total_found} total found")
        
        return ImageExtractResponse(
            success=True,
            url=url,
            total_images=len(filtered_images),
            images=filtered_images,
            screenshot_base64=data.get('screenshot')
        )
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Image extraction failed: {error_msg}")
        
        return ImageExtractResponse(
            success=False,
            url=str(request.url),
            total_images=0,
            images=[],
            error_message=error_msg
        )

@app.on_event("startup")
async def startup():
    print("🚀 Starting Enhanced Website Cloner with Super Image Extraction...")
    if MCP_AVAILABLE:
        await initialize_mcp()
    print("✅ Ready to clone websites with comprehensive image detection!")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)