import os
import sys
import json
import re
import requests
from bs4 import BeautifulSoup

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from groq import Groq
from LLM_APIS import GROQ_API_KEY
from web_search import RobustWebSearcher


# ------------------ LLM QUERY GENERATION ------------------

def generate_search_queries(user_query):
    """
    Uses Groq LLM to generate optimized queries for web search and Wikipedia.
    Output structure is STRICTLY preserved.
    """

    prompt = f"""
User query: "{user_query}"

Your task:
- Generate TWO queries: one for WEB search, one for WIKIPEDIA.

WEB QUERY RULES:
- Can include qualifiers (price, net worth, today, history, facts, etc.)
- Optimized for search engines

WIKIPEDIA QUERY RULES (VERY IMPORTANT):
- MUST be a single main entity or concept
- Usually ONE proper noun or title
- No dates, no numbers, no question words
- No qualifiers like: net worth, price, today, latest, history
- Think: Wikipedia article TITLE

Examples:
"Elon musk net worth today" → "Elon Musk"
"taj mahal history" → "Taj Mahal"
"pizza origin italy" → "Pizza"
"bitcoin price now" → "Bitcoin"
"paris france tourism" → "Paris"

Return ONLY valid JSON:
{{
  "web_query": "...",
  "wiki_query": "..."
}}

No explanations.
No markdown.
No extra text.
"""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.7,
            max_completion_tokens=512,
            top_p=1,
            stream=False,
            stop=None
        )

        raw_text = completion.choices[0].message.content.strip()

        # Extract JSON safely
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found")

        queries = json.loads(match.group())

        if not all(k in queries for k in ("web_query", "wiki_query")):
            raise ValueError("Invalid structure")

        # ---- HARD SAFETY CLEANUP FOR WIKIPEDIA QUERY ----
        wiki = queries["wiki_query"]

        # Remove common non-encyclopedic terms if model slips
        wiki = re.sub(
            r"\b(net worth|price|today|latest|now|history|facts|info|information|how|why|when)\b",
            "",
            wiki,
            flags=re.IGNORECASE,
        )

        wiki = re.sub(r"\s+", " ", wiki).strip()

        # If wiki query still looks bad, fallback to core nouns from user query
        if len(wiki.split()) > 4:
            wiki = user_query.split("?")[0].strip()

        queries["wiki_query"] = wiki

        print(f" Generated queries:")
        print(f"   Web: {queries['web_query']}")
        print(f"   Wiki: {queries['wiki_query']}\n")

        return queries

    except Exception as e:
        print(f" Error generating queries: {e}")
        print("   Falling back to original query\n")
        return {
            "web_query": user_query,
            "wiki_query": user_query
        }



# ------------------ WEB SEARCH ------------------

def _clean_html_text(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
    return re.sub(r"\s+", " ", text).strip()


def search_web(query, max_chars=2000):
    print(f"🔍 Searching web for: {query}")

    searcher = None
    try:
        searcher = RobustWebSearcher(headless=True)
        results = searcher.search_and_scrape(query, max_results=1)

        if not results:
            print(" Web search failed: No results\n")
            return None

        result = results[0]
        content = result.get("content", "")

        if "<p" in content.lower():
            content = _clean_html_text(content)
        else:
            content = re.sub(r"\s+", " ", content).strip()

        content = content[:max_chars]

        print(f" Web search successful: {len(content)} chars\n")

        return {
            "query": query,
            "title": result.get("title", "No title"),
            "url": result.get("url", ""),
            "content": content
        }

    except Exception as e:
        print(f" Web search error: {e}\n")
        return None

    finally:
        if searcher:
            searcher.close()


# ------------------ WIKIPEDIA SEARCH ------------------

def search_wikipedia(query, max_chars=2000):
    print(f"📚 Searching Wikipedia for: {query}")

    try:
        api_url = "https://en.wikipedia.org/w/api.php"
        headers = {
            "User-Agent": "UnifiedSearchTool/1.0"
        }

        search_params = {
            "action": "opensearch",
            "search": query,
            "limit": 1,
            "format": "json"
        }

        r = requests.get(api_url, params=search_params, headers=headers, timeout=10)
        if r.status_code != 200:
            print(" Wikipedia search failed: HTTP error\n")
            return None

        data = r.json()
        if not data or not data[1]:
            print(" Wikipedia search failed: No results\n")
            return None

        title = data[1][0]
        wiki_url = data[3][0] if len(data) > 3 and data[3] else \
            f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"

        summary_params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "format": "json",
            "titles": title
        }

        summary_resp = requests.get(
            api_url, params=summary_params, headers=headers, timeout=10
        ).json()

        pages = summary_resp.get("query", {}).get("pages", {})
        page = next(iter(pages.values()), {})
        summary = page.get("extract", "")

        if not summary:
            print(" Wikipedia search failed: Empty summary\n")
            return None

        summary = summary.strip()[:max_chars]

        print(f" Wikipedia search successful: {len(summary)} chars\n")

        return {
            "query": query,
            "title": title,
            "url": wiki_url,
            "content": summary
        }

    except Exception as e:
        print(f" Wikipedia search error: {e}\n")
        return None


# ------------------ UNIFIED SEARCH ------------------

def unified_search(user_query, max_chars_per_source=1500):
    print("=" * 70)
    print("🔎 UNIFIED SEARCH")
    print("=" * 70)
    print(f"Query: {user_query}\n")

    print("🤖 Generating optimized queries with Groq...")
    queries = generate_search_queries(user_query)

    web_result = search_web(queries["web_query"], max_chars_per_source)
    wiki_result = search_wikipedia(queries["wiki_query"], max_chars_per_source)

    total_chars = 0
    if web_result:
        total_chars += len(web_result["content"])
    if wiki_result:
        total_chars += len(wiki_result["content"])

    if web_result or wiki_result:
        status = "success"
        message = "Search completed successfully"
        if web_result and not wiki_result:
            message += " (web only)"
        elif wiki_result and not web_result:
            message += " (Wikipedia only)"
    else:
        status = "error"
        message = "Both searches failed"

    response = {
        "status": status,
        "web_search": web_result,
        "wikipedia_search": wiki_result,
        "total_chars": total_chars,
        "message": message
    }

    print("=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    print(f"Status: {status}")
    print(f"Web search: {'' if web_result else ''}")
    print(f"Wikipedia search: {'' if wiki_result else ''}")
    print(f"Total characters: {total_chars}")
    print(f"Message: {message}")
    print("=" * 70)

    return response


if __name__ == "__main__":
    test_queries = [
        "Elon musk net worth today"
    ]

    for q in test_queries:
        print("\n" + "#" * 80)
        result = unified_search(q)
        print("\nJSON OUTPUT:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
