import asyncio
import base64
import json
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from io import BytesIO

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
from PIL import Image
import httpx

class WebsiteScraper:
    def __init__(self):
        self.viewport_sizes = [
            {"width": 1920, "height": 1080, "name": "desktop"},
            {"width": 1024, "height": 768, "name": "tablet"},
            {"width": 375, "height": 812, "name": "mobile"}
        ]

    async def scrape_website(self, url: str) -> Dict[str, Any]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()

            try:
                await self._smart_navigation(page, url)
                await self._wait_for_content(page)
                await self._handle_overlays(page)
                await self._comprehensive_scroll(page)

                html_content = await page.content()
                title = await page.title()
                soup = BeautifulSoup(html_content, 'html.parser')
                for tag in soup(['script', 'style', 'noscript', 'meta', 'link']):
                    tag.decompose()

                body_text = soup.get_text(separator=' ', strip=True)

                return {
                    "url": url,
                    "title": title,
                    "meta_data": await self._extract_meta_data(page),
                    "screenshots": await self._capture_advanced_screenshots(page),
                    "html_structure": await self._extract_advanced_html(page),
                    "visual_elements": await self._extract_visual_elements(page),
                    "interactive_elements": await self._extract_interactive_elements(page),
                    "media_content": await self._extract_media_content(page),
                    "design_system": await self._extract_design_system(page),
                    "layout_analysis": await self._analyze_advanced_layout(page),
                    "typography": await self._analyze_typography(page),
                    "animations": await self._detect_animations(page),
                    "responsive_behavior": await self._analyze_responsive_advanced(page),
                    "performance_metrics": await self._measure_performance(page),
                    "accessibility": await self._analyze_accessibility(page)
                }
            finally:
                await browser.close()

    async def _smart_navigation(self, page: Page, url: str):
        strategies = [
            {"wait_until": "networkidle", "timeout": 30000},
            {"wait_until": "domcontentloaded", "timeout": 20000},
            {"wait_until": "load", "timeout": 15000}
        ]
        for i, strategy in enumerate(strategies):
            try:
                print(f"🌐 Navigation attempt {i+1}: {strategy}")
                await page.goto(url, **strategy)
                break
            except Exception as e:
                print(f"⚠️ Strategy {i+1} failed: {e}")
                if i == len(strategies) - 1:
                    raise e

    async def _wait_for_content(self, page: Page):
        await page.evaluate("""
            () => {
                return new Promise((resolve) => {
                    if (window.React || document.querySelector('[data-reactroot]')) {
                        const checkReact = () => {
                            const root = document.querySelector('[data-reactroot]');
                            if (root && root.children.length > 0) {
                                resolve();
                            } else {
                                setTimeout(checkReact, 100);
                            }
                        };
                        checkReact();
                    } else if (window.Vue || document.querySelector('[data-v-]')) {
                        setTimeout(resolve, 2000);
                    } else if (window.ng || document.querySelector('[ng-app], [ng-controller]')) {
                        setTimeout(resolve, 2000);
                    } else {
                        setTimeout(resolve, 1500);
                    }
                });
            }
        """)

        try:
            await page.wait_for_function("""
                () => {
                    const images = Array.from(document.images);
                    return images.every(img => img.complete);
                }
            """, timeout=10000)
        except Exception:
            print("⚠️ Not all images finished loading within timeout.")

    async def _handle_overlays(self, page: Page):
        overlay_selectors = [
            'button[id*="accept"]', 'button[class*="accept"]', 'button[aria-label*="Accept"]',
            'button:has-text("Accept")', 'button:has-text("Allow")', 'button:has-text("OK")',
            'button:has-text("Got it")', 'button:has-text("Continue")', 'button:has-text("Agree")',
            'button[aria-label*="Close"]', 'button[class*="close"]', '[data-dismiss="modal"]',
            'button:has-text("No thanks")', 'button:has-text("Maybe later")',
            'button:has-text("Yes")', 'button:has-text("Enter")', 'button:has-text("I am over")',
            'button:has-text("Allow Location")', 'button:has-text("Enable")'
        ]
        for selector in overlay_selectors:
            try:
                await page.click(selector, timeout=2000)
                await page.wait_for_timeout(1000)
                break
            except:
                continue

    async def _comprehensive_scroll(self, page: Page):
        await page.evaluate("""
            async () => {
                const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
                let totalHeight = Math.max(
                    document.body.scrollHeight,
                    document.documentElement.scrollHeight
                );
                let position = 0;
                const step = 300;
                while (position < totalHeight) {
                    window.scrollTo(0, position);
                    await delay(200);
                    position += step;
                }
                window.scrollTo(0, 0);
                await delay(500);
            }
        """)

    async def _extract_meta_data(self, page: Page) -> Dict:
        return await page.evaluate("""
            () => {
                const meta = {};
                document.querySelectorAll('meta').forEach(tag => {
                    const name = tag.getAttribute('name') || tag.getAttribute('property') || tag.getAttribute('itemprop');
                    const content = tag.getAttribute('content');
                    if (name && content) {
                        meta[name] = content;
                    }
                });
                return meta;
            }
        """)

    async def _extract_advanced_html(self, page: Page) -> Dict[str, Any]:
        html_content = await page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        for tag in soup(['script', 'style', 'noscript', 'meta', 'link']):
            tag.decompose()
        return {
            "cleaned_html": str(soup)[:15000],
            "headings": self._extract_headings_hierarchy(soup),
            "text_content": soup.get_text(separator=' ', strip=True)[:500]
        }

    def _extract_headings_hierarchy(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract heading hierarchy from the parsed HTML"""
        headings = []
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            headings.append({
                'level': int(heading.name[1]),
                'text': heading.get_text(strip=True),
                'id': heading.get('id', ''),
                'class': heading.get('class', [])
            })
        return headings

    async def _capture_advanced_screenshots(self, page: Page) -> Dict[str, Any]:
        screenshots = {}
        for viewport in self.viewport_sizes:
            await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
            await page.wait_for_timeout(2000)
            screenshot = await page.screenshot(full_page=True)
            screenshots[viewport["name"]] = base64.b64encode(screenshot).decode()
        return screenshots

    async def _extract_visual_elements(self, page: Page) -> Dict[str, Any]:
        return await page.evaluate("""
            () => {
                const elements = { buttons: [], cards: [] };
                document.querySelectorAll('button').forEach(btn => {
                    elements.buttons.push({
                        text: btn.innerText,
                        classList: btn.className
                    });
                });
                document.querySelectorAll('.card').forEach(card => {
                    elements.cards.push({
                        html: card.innerHTML,
                        classList: card.className
                    });
                });
                return elements;
            }
        """)

    async def _extract_interactive_elements(self, page: Page) -> Dict[str, Any]:
        return await page.evaluate("""
            () => {
                const forms = Array.from(document.querySelectorAll('form')).map(f => f.outerHTML);
                const modals = Array.from(document.querySelectorAll('[class*="modal"]')).map(m => m.outerHTML);
                return { forms, modals };
            }
        """)

    async def _extract_media_content(self, page: Page) -> Dict[str, Any]:
        return await page.evaluate("""
            () => {
                const images = Array.from(document.querySelectorAll('img')).map(img => ({
                    src: img.src,
                    alt: img.alt,
                    classList: img.className
                }));
                const videos = Array.from(document.querySelectorAll('video')).map(vid => ({
                    src: vid.currentSrc || vid.src,
                    poster: vid.poster,
                    classList: vid.className
                }));
                return { images, videos };
            }
        """)

    async def _extract_design_system(self, page: Page) -> Dict[str, Any]:
        return await page.evaluate("""
            () => {
                const styles = new Set();
                document.querySelectorAll('*').forEach(el => {
                    const s = window.getComputedStyle(el);
                    styles.add(s.color);
                    styles.add(s.backgroundColor);
                    styles.add(s.fontFamily);
                });
                return { collected_styles: Array.from(styles).filter(Boolean) };
            }
        """)

    async def _analyze_advanced_layout(self, page: Page) -> Dict[str, Any]:
        return await page.evaluate("""
            () => {
                const body = document.body;
                return {
                    width: body.scrollWidth,
                    height: body.scrollHeight,
                    sections: Array.from(document.querySelectorAll('section')).map(s => s.innerText.substring(0, 100))
                };
            }
        """)

    async def _analyze_typography(self, page: Page) -> Dict[str, Any]:
        return await page.evaluate("""
            () => {
                const fonts = new Set();
                document.querySelectorAll('*').forEach(el => {
                    const font = window.getComputedStyle(el).fontFamily;
                    if (font) fonts.add(font);
                });
                return { fonts: Array.from(fonts) };
            }
        """)

    async def _detect_animations(self, page: Page) -> Dict[str, Any]:
        return await page.evaluate("""
            () => {
                const animated = Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    return style.animationName !== 'none' || style.transition !== 'all 0s ease 0s';
                });
                return { animated_elements: animated.length };
            }
        """)

    async def _analyze_responsive_advanced(self, page: Page) -> Dict[str, Any]:
        breakpoints = [320, 768, 1024, 1440]
        responsive_data = {}
        for width in breakpoints:
            await page.set_viewport_size({"width": width, "height": 800})
            await page.wait_for_timeout(500)
            layout_data = await page.evaluate("""
                () => {
                    return {
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        visible_nav: !!document.querySelector('nav')
                    };
                }
            """)
            responsive_data[str(width)] = layout_data
        return responsive_data

    async def _measure_performance(self, page: Page) -> Dict[str, Any]:
        return await page.evaluate("""
            () => JSON.parse(JSON.stringify(window.performance.timing))
        """)

    async def _analyze_accessibility(self, page: Page) -> Dict[str, Any]:
        return await page.evaluate("""
            () => {
                const accessibility = {
                    images_with_alt: Array.from(document.querySelectorAll('img')).filter(img => img.alt).length,
                    buttons_with_labels: Array.from(document.querySelectorAll('button')).filter(btn => btn.innerText.trim() !== '').length
                };
                return accessibility;
            }
        """)


# Example usage
async def main():
    scraper = WebsiteScraper()
    try:
        result = await scraper.scrape_website("https://example.com")
        print(f"Successfully scraped: {result['title']}")
        # Process the result as needed
    except Exception as e:
        print(f"Scraping failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())