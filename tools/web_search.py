import time
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from DrissionPage import ChromiumPage, ChromiumOptions
import html2text
import re
from googleapiclient.discovery import build

class RobustWebSearcher:
    """
    A robust web search and scraping tool with multiple strategies:
    1. Google Custom Search API (primary - best quality results)
    2. DuckDuckGo API (fallback - fast, reliable)
    3. Browser automation (fallback - handles dynamic content)
    4. HTTP requests (emergency - lightweight)
    """
    
    def __init__(self, headless=True, google_api_key=None, google_cse_id=None):
        """
        Initialize the web searcher.
        
        Args:
            headless: Run browser in headless mode (invisible)
            google_api_key: Google Custom Search API key (optional)
            google_cse_id: Google Custom Search Engine ID (optional)
        """
        self.headless = headless
        self.browser = None
        
        # Google Custom Search credentials
        self.google_api_key = google_api_key or "AIzaSyCGLkcZuJY7HKVBk-tetToWXxpyezHS6Ro"
        self.google_cse_id = google_cse_id or "d31276b53ca024edc"  # User's Custom Search Engine ID
        
        # Setup Markdown converter
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = True  # Remove all links
        self.converter.ignore_images = True
        self.converter.ignore_tables = False
        self.converter.body_width = 0  # No wrapping
        
        print("🚀 Web Searcher initialized")
        if self.google_api_key:
            print("    Google Custom Search API configured")

    def _init_browser(self):
        """Lazy initialization of browser (only when needed)"""
        if self.browser is None:
            print("🌐 Starting browser...")
            co = ChromiumOptions()
            co.headless(self.headless)
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-dev-shm-usage')
            co.set_argument('--lang=en-US')
            co.set_user_agent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            co.auto_port()
            
            self.browser = ChromiumPage(co)
            print(" Browser ready")

    # ==================== STRATEGY 1: Google Custom Search ====================
    
    def search_with_google(self, query, max_results=5):
        """
        Search using Google Custom Search API (best quality results).
        
        Args:
            query: Search query string
            max_results: Number of results to return (max 10 per request)
            
        Returns:
            List of result dictionaries with 'title', 'url', 'snippet'
        """
        print(f"🔍 Strategy 1: Searching with Google Custom Search for '{query}'...")
        
        try:
            # Build the Custom Search service
            service = build("customsearch", "v1", developerKey=self.google_api_key)
            
            # Execute the search
            # If no CSE ID provided, it will search the entire web
            search_params = {
                'q': query,
                'num': min(max_results, 10)  # Google allows max 10 per request
            }
            
            if self.google_cse_id:
                search_params['cx'] = self.google_cse_id
            
            result = service.cse().list(**search_params).execute()
            
            # Extract search results
            if 'items' in result:
                items = result['items']
                print(f" Found {len(items)} results")
                
                formatted_results = []
                for i, item in enumerate(items, 1):
                    formatted_results.append({
                        'rank': i,
                        'title': item.get('title', 'No title'),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', 'No description')
                    })
                    print(f"  {i}. {item.get('title', 'No title')}")
                    print(f"     {item.get('link', '')}")
                
                return formatted_results
            else:
                print(" No results found")
                return []
                
        except Exception as e:
            print(f" Google Search API Error: {e}")
            print("   Falling back to alternative search methods...")
            return []

    # ==================== STRATEGY 2: DuckDuckGo API ====================
    
    def search_with_ddgs(self, query, max_results=5):
        """
        Search using DuckDuckGo API (fastest, most reliable).
        
        Args:
            query: Search query string
            max_results: Number of results to return
            
        Returns:
            List of result dictionaries with 'title', 'url', 'snippet'
        """
        print(f"🔍 Strategy 1: Searching with DuckDuckGo API for '{query}'...")
        
        try:
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=max_results))
            
            if results:
                print(f" Found {len(results)} results")
                formatted_results = []
                for i, r in enumerate(results, 1):
                    formatted_results.append({
                        'rank': i,
                        'title': r.get('title', 'No title'),
                        'url': r.get('href', ''),
                        'snippet': r.get('body', 'No description')
                    })
                    print(f"  {i}. {r.get('title', 'No title')}")
                    print(f"     {r.get('href', '')}")
                
                return formatted_results
            else:
                print(" No results found")
                return []
                
        except Exception as e:
            print(f" DuckDuckGo API Error: {e}")
            return []

    # ==================== STRATEGY 2: Browser Automation ====================
    
    def search_with_browser(self, query):
        """
        Search using browser automation (fallback method).
        
        Args:
            query: Search query string
            
        Returns:
            URL of the first result or None
        """
        print(f"🔍 Strategy 2: Searching with browser automation for '{query}'...")
        
        try:
            self._init_browser()
            
            # Use regular DuckDuckGo (not HTML version)
            search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
            self.browser.get(search_url)
            
            # Wait a bit for results to load
            time.sleep(2)
            
            # Try multiple selectors for result links
            selectors = [
                'a[data-testid="result-title-a"]',  # New DuckDuckGo
                'a.result__a',                       # Old HTML version
                'article h2 a',                      # Alternative
                'a[href^="http"]'                    # Generic fallback
            ]
            
            for selector in selectors:
                try:
                    results = self.browser.eles(selector)
                    if results:
                        # Filter out DuckDuckGo's own links
                        for result in results:
                            url = result.attr('href')
                            if url and 'duckduckgo.com' not in url and url.startswith('http'):
                                title = result.text or "No title"
                                print(f" Found: {title}")
                                print(f"   URL: {url}")
                                return url
                except:
                    continue
            
            print(" No valid results found with browser")
            return None
            
        except Exception as e:
            print(f" Browser Search Error: {e}")
            return None

    # ==================== STRATEGY 3: HTTP Requests ====================
    
    def search_with_requests(self, query):
        """
        Search using simple HTTP requests (emergency fallback).
        
        Args:
            query: Search query string
            
        Returns:
            URL of the first result or None
        """
        print(f"🔍 Strategy 3: Searching with HTTP requests for '{query}'...")
        
        try:
            # Use DuckDuckGo Lite (HTML only, no JS)
            url = "https://lite.duckduckgo.com/lite/"
            params = {'q': query}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.post(url, data=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result links
                links = soup.find_all('a', class_='result-link')
                
                if links:
                    first_link = links[0]
                    result_url = first_link.get('href')
                    title = first_link.text.strip()
                    
                    print(f" Found: {title}")
                    print(f"   URL: {result_url}")
                    return result_url
                else:
                    print(" No results found")
                    return None
            else:
                print(f" HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f" HTTP Request Error: {e}")
            return None

    # ==================== CONTENT SCRAPING ====================
    
    def scrape_with_browser(self, url):
        """
        Scrape content using browser (handles JavaScript).
        
        Args:
            url: URL to scrape
            
        Returns:
            Cleaned markdown content
        """
        print(f"📄 Scraping with browser: {url}")
        
        try:
            self._init_browser()
            self.browser.get(url, timeout=15)
            
            # Wait for content to load
            time.sleep(2)
            
            # Get the main content
            raw_html = self.browser.html
            
            # Convert to markdown
            markdown_content = self.converter.handle(raw_html)
            
            # Clean up the content
            cleaned = self._clean_content(markdown_content)
            
            print(f" Scraped {len(cleaned)} characters")
            return cleaned
            
        except Exception as e:
            print(f" Browser Scraping Error: {e}")
            return None

    def scrape_with_requests(self, url):
        """
        Scrape content using HTTP requests (faster, but no JS).
        
        Args:
            url: URL to scrape
            
        Returns:
            Cleaned markdown content
        """
        print(f"📄 Scraping with HTTP: {url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Convert to markdown
                markdown_content = self.converter.handle(response.text)
                
                # Clean up the content
                cleaned = self._clean_content(markdown_content)
                
                print(f" Scraped {len(cleaned)} characters")
                return cleaned
            else:
                print(f" HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f" HTTP Scraping Error: {e}")
            return None

    def _clean_content(self, content):
        """Clean and format scraped content"""
        if not content:
            return ""
        
        # Remove excessive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove navigation/menu artifacts
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip very short lines that are likely navigation
            if len(line.strip()) < 3:
                continue
            # Skip lines that are just symbols
            if re.match(r'^[\s\*\-_#]+$', line):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()

    # ==================== MAIN SEARCH & SCRAPE ====================
    
    def search_and_scrape(self, query, max_results=1):
        """
        Search for a query and scrape the top result(s).
        Uses cascading fallback strategies.
        
        Args:
            query: Search query
            max_results: Number of results to scrape (default: 1)
            
        Returns:
            Dictionary with search results and scraped content
        """
        print("\n" + "="*70)
        print(f"🔎 SEARCHING FOR: {query}")
        print("="*70 + "\n")
        
        results = []
        search_results = []
        
        # Try Strategy 1: Google Custom Search API
        if self.google_api_key:
            search_results = self.search_with_google(query, max_results=5)
        
        # Fallback to Strategy 2: DuckDuckGo API
        if not search_results:
            print("\n  Falling back to DuckDuckGo API...")
            search_results = self.search_with_ddgs(query, max_results=max_results)
        
        # Fallback to Strategy 3: Browser
        if not search_results:
            print("\n  Falling back to browser search...")
            url = self.search_with_browser(query)
            if url:
                search_results = [{'rank': 1, 'title': 'Browser Result', 'url': url, 'snippet': ''}]
        
        # Fallback to Strategy 4: HTTP Requests
        if not search_results:
            print("\n  Falling back to HTTP requests...")
            url = self.search_with_requests(query)
            if url:
                search_results = [{'rank': 1, 'title': 'HTTP Result', 'url': url, 'snippet': ''}]
        
        if not search_results:
            print("\n All search strategies failed")
            return None
        
        # Show all results
        if len(search_results) > 1:
            print("\n" + "-"*70)
            print(f"📋 ALL SEARCH RESULTS (showing top {len(search_results)})")
            print("-"*70)
            for r in search_results:
                print(f"\n{r['rank']}. {r['title']}")
                print(f"   URL: {r['url']}")
                print(f"   {r['snippet'][:150]}...")
        
        # Scrape the top result(s)
        print("\n" + "-"*70)
        print(f"📥 SCRAPING TOP {max_results} RESULT(S)")
        print("-"*70 + "\n")
        
        for result in search_results[:max_results]:
            url = result['url']
            
            # Try scraping with requests first (faster)
            content = self.scrape_with_requests(url)
            
            # Fallback to browser if needed
            if not content or len(content) < 100:
                print("  Content too short, trying browser...")
                content = self.scrape_with_browser(url)
            
            if content:
                results.append({
                    'rank': result['rank'],
                    'title': result['title'],
                    'url': url,
                    'snippet': result.get('snippet', ''),
                    'content': content
                })
        
        return results
        
        # Fallback to Strategy 2: Browser
        if not search_results:
            print("\n  Falling back to browser search...")
            url = self.search_with_browser(query)
            if url:
                search_results = [{'rank': 1, 'title': 'Browser Result', 'url': url, 'snippet': ''}]
        
        # Fallback to Strategy 3: HTTP Requests
        if not search_results:
            print("\n  Falling back to HTTP requests...")
            url = self.search_with_requests(query)
            if url:
                search_results = [{'rank': 1, 'title': 'HTTP Result', 'url': url, 'snippet': ''}]
        
        if not search_results:
            print("\n All search strategies failed")
            return None
        
        # Scrape the top result(s)
        print("\n" + "-"*70)
        print("📥 SCRAPING CONTENT")
        print("-"*70 + "\n")
        
        for result in search_results[:max_results]:
            url = result['url']
            
            # Try scraping with requests first (faster)
            content = self.scrape_with_requests(url)
            
            # Fallback to browser if needed
            if not content or len(content) < 100:
                print("  Content too short, trying browser...")
                content = self.scrape_with_browser(url)
            
            if content:
                results.append({
                    'rank': result['rank'],
                    'title': result['title'],
                    'url': url,
                    'snippet': result.get('snippet', ''),
                    'content': content
                })
        
        return results

    def close(self):
        """Clean up resources"""
        if self.browser:
            try:
                self.browser.quit()
                print("🔒 Browser closed")
            except:
                pass


# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Example query
    query = "who is elon musk?"
    
    searcher = RobustWebSearcher(headless=True)
    
    try:
        # Search and scrape - only get 1 result
        results = searcher.search_and_scrape(query, max_results=1)
        
        if results:
            print("\n" + "="*70)
            print("📊 RESULTS")
            print("="*70 + "\n")
            
            for result in results:
                print(f"Title: {result['title']}")
                print(f"URL: {result['url']}")
                print(f"\nContent Preview (first 2000 chars):")
                print("-" * 70)
                print(result['content'][:2000])
                if len(result['content']) > 2000:
                    print("\n... (content truncated)")
                print("-" * 70)
                print(f"\nTotal content length: {len(result['content'])} characters")
        else:
            print("\n No results found")
    
    finally:
        searcher.close()
        print("\n✨ Done!")