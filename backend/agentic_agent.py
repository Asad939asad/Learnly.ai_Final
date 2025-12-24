import os
import sys
import json
import requests
from datetime import datetime, timedelta

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from tools.LLM_APIS import GEMINI_API_KEY
from tools.Googlecalender import authenticate, schedule_meeting, list_meetings_by_date_range
from tools.task_scheduler import create_schedule_from_query
from tools.unified_search import unified_search
from backend.query_rag import query_book_rag


# ==================== GPT-4.1 INTEGRATION ====================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
ENDPOINT = "https://models.github.ai/inference"
MODEL = "openai/gpt-4.1-mini"


def ask_gpt4(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """
    Query OpenAI GPT-4.1-mini via GitHub Models API.
    
    Args:
        prompt: User prompt
        system_prompt: System instructions
        
    Returns:
        str: Response from GPT-4.1
    """
    try:
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 1.0,
            "top_p": 1.0,
            "model": MODEL
        }
        
        response = requests.post(
            f"{ENDPOINT}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f" GPT-4.1 Error: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f" GPT-4.1 Error: {e}"


# ==================== QUERY ROUTING ====================

def route_query(user_query):
    """
    Uses Gemini LLM to determine which branch the query belongs to.
    
    Args:
        user_query: User's input query
    
    Returns:
        Dictionary with 'branch' and 'confidence' keys
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = f"""
Current Date and Time: {current_time}

Analyze the following user query and determine which category it belongs to:

User Query: "{user_query}"

Categories:
1. "calendar" - Scheduling meetings, adding calendar events, setting reminders
2. "calendar_view" - Viewing, listing, or displaying existing meetings/events
3. "task_scheduler" - Creating task plans, project schedules, breaking down work into days
4. "search_rag" - General questions, information lookup, knowledge queries

Return ONLY a valid JSON object with this exact structure:
{{
    "branch": "calendar" | "calendar_view" | "task_scheduler" | "search_rag",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}}

Rules:
- Use "calendar" if the query is about scheduling/creating a specific meeting or event
- Use "calendar_view" if the query is about viewing/listing/displaying existing meetings
- Use "task_scheduler" if the query is about creating a multi-day plan or schedule
- Use "search_rag" for all other queries (questions, information lookup, etc.)
- Confidence should be high (>0.8) only if you're very certain
- Return ONLY the JSON object, no additional text
"""
    
    try:
        # Use GPT-4.1 instead of Gemini to avoid quota issues
        response_text = ask_gpt4(prompt, "You are a query routing assistant. Return only valid JSON.")
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON response
        routing = json.loads(response_text)
        
        # Validate structure
        if 'branch' not in routing or 'confidence' not in routing:
            raise ValueError("Invalid routing structure")
        
        print(f"🎯 Routing Decision:")
        print(f"   Branch: {routing['branch']}")
        print(f"   Confidence: {routing['confidence']}")
        print(f"   Reasoning: {routing.get('reasoning', 'N/A')}\n")
        
        return routing
    
    except Exception as e:
        print(f" Routing error: {e}")
        print(f"   Defaulting to search_rag branch\n")
        return {
            'branch': 'search_rag',
            'confidence': 0.5,
            'reasoning': 'Error in routing, using default'
        }


# ==================== RAG SIMILARITY CHECK ====================

def get_rag_with_confidence(user_query, book_name="default"):
    """
    Queries RAG and returns results with similarity confidence score.
    
    Args:
        user_query: User's query
        book_name: Name of the book to query
    
    Returns:
        Dictionary with 'confidence', 'response', and 'use_rag' keys
    """
    try:
        # Query RAG system - it should return similarity scores
        # For now, using placeholder that returns confidence
        rag_response = query_book_rag(book_name, user_query)
        
        # TODO: Modify query_book_rag to return similarity scores
        # For now, we'll extract confidence from the response or default to 0.5
        # In a real implementation, query_book_rag should return:
        # {'response': str, 'confidence': float, 'similarity_scores': list}
        
        if isinstance(rag_response, dict) and 'confidence' in rag_response:
            confidence = rag_response['confidence']
            response = rag_response.get('response', '')
        else:
            # Placeholder: assume medium confidence for now
            confidence = 0.5
            response = rag_response
        
        print(f"📚 RAG Query Results:")
        print(f"   Confidence: {confidence}")
        print(f"   Response length: {len(str(response))} chars\n")
        
        # Only use RAG if confidence/similarity is high
        use_rag = confidence > 0.8
        
        return {
            'confidence': confidence,
            'response': response,
            'use_rag': use_rag
        }
        
    except Exception as e:
        print(f" RAG query error: {e}\n")
        return {
            'confidence': 0.0,
            'response': None,
            'use_rag': False
        }


# ==================== AGENTIC SYSTEM ====================

def agentic_agent(user_query, book_name="default"):
    """
    Main agentic system that routes queries and generates final responses.
    
    Args:
        user_query: User's input query
        book_name: Optional book name for RAG queries
    
    Returns:
        Dictionary with final response and metadata
    """
    print("=" * 70)
    print("🤖 AGENTIC SYSTEM")
    print("=" * 70)
    print(f"Query: {user_query}\n")
    
    # Step 1: Route the query
    routing = route_query(user_query)
    branch = routing['branch']
    
    # Step 2: Execute the appropriate branch
    branch_result = None
    
    # IMPORTANT: Only search_rag branch uses web search and RAG
    # Calendar and task_scheduler branches should NOT trigger any searches
    
    if branch == "calendar":
        print("📅 Executing Calendar Branch...\n")
        # Parse query with GPT-4.1 to extract meeting details
        parse_prompt = f"""
Extract meeting details from this query: "{user_query}"

Current date/time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Pakistan Time, GMT+5)

IMPORTANT: The user is in Pakistan (GMT+5 timezone). When they say "5 PM", they mean 5 PM Pakistan Time.
Convert all times to Pakistan Time (GMT+5) format.

Return JSON with:
{{
    "title": "meeting title",
    "start_time": "YYYY-MM-DDTHH:MM:SS+05:00",
    "duration_minutes": number
}}

Example: If user says "meeting at 5 PM", the start_time should be "YYYY-MM-DDT17:00:00+05:00"
"""
        details_response = ask_gpt4(parse_prompt)
        
        try:
            # Parse the response
            import re
            details_text = details_response.strip()
            if details_text.startswith('```json'):
                details_text = details_text[7:]
            if details_text.startswith('```'):
                details_text = details_text[3:]
            if details_text.endswith('```'):
                details_text = details_text[:-3]
            details_text = details_text.strip()
            
            meeting_details = json.loads(details_text)
            
            # Schedule the meeting
            service = authenticate()
            event_id = schedule_meeting(
                service,
                meeting_details['title'],
                meeting_details['start_time'],
                meeting_details.get('duration_minutes', 60)
            )
            
            branch_result = {
                'type': 'calendar',
                'event_id': event_id,
                'title': meeting_details['title'],
                'start_time': meeting_details['start_time'],
                'message': f"Meeting '{meeting_details['title']}' scheduled successfully"
            }
        except Exception as e:
            print(f"Error scheduling meeting: {e}")
            branch_result = {
                'type': 'calendar',
                'error': str(e),
                'message': 'Failed to schedule meeting. Please provide clear date, time, and title.'
            }
    
    elif branch == "calendar_view":
        print("📅 Executing Calendar View Branch...\n")
        # For now, use a default range (today to 7 days from now)
        today = datetime.now()
        end_date = today + timedelta(days=7)
        
        start_time_iso = today.strftime("%Y-%m-%dT00:00:00")
        end_time_iso = end_date.strftime("%Y-%m-%dT23:59:59")
        
        service = authenticate()
        meetings = list_meetings_by_date_range(service, start_time_iso, end_time_iso)
        
        branch_result = {
            'type': 'calendar_view',
            'meetings': meetings,
            'count': len(meetings),
            'date_range': f"{today.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        }
    
    elif branch == "task_scheduler":
        print("📋 Executing Task Scheduler Branch...\n")
        result = create_schedule_from_query(user_query)
        branch_result = {
            'type': 'task_scheduler',
            'csv_path': result.get('csv_path'),
            'total_days': result.get('total_days'),
            'calendar_event_id': result.get('calendar_event_id'),
            'message': f"Created {result.get('total_days')} day task plan"
        }
    
    elif branch == "search_rag":
        print("🔍 Executing Search/RAG Branch...\n")
        
        # ALWAYS execute web search (mandatory)
        print("🌐 Executing Web Search (mandatory)...\n")
        web_search_result = unified_search(user_query)
        
        # Try RAG and check similarity confidence
        print("📚 Checking RAG similarity...\n")
        rag_result = get_rag_with_confidence(user_query, book_name)
        
        # Build combined result
        branch_result = {
            'type': 'search_rag',
            'web_search': web_search_result,
            'rag_used': rag_result['use_rag'],
            'rag_confidence': rag_result['confidence']
        }
        
        # Only include RAG if confidence is high enough
        if rag_result['use_rag']:
            print(f" RAG confidence ({rag_result['confidence']}) is high enough (>0.8), including RAG results\n")
            branch_result['rag_response'] = rag_result['response']
        else:
            print(f" RAG confidence ({rag_result['confidence']}) is too low (<0.8), using only web search\n")
            branch_result['rag_response'] = None
    
    # Step 3: Generate final response with GPT-4.1
    print("🎯 Generating Final Response with GPT-4.1...\n")
    
    # Prepare context for GPT-4.1
    context = f"User Query: {user_query}\n\n"
    context += f"Branch Used: {branch}\n\n"
    context += f"Branch Result:\n{json.dumps(branch_result, indent=2)}\n"
    
    system_prompt = """You are Learnly.AI, an intelligent learning assistant. 
Based on the user's query and the information gathered from various tools, 
provide a helpful, concise, and accurate response. 
If task scheduling or calendar events were created, confirm the details.
If web search or RAG was used, synthesize the information into a clear answer."""
    
    final_response = ask_gpt4(context, system_prompt)
    
    # Build final result
    result = {
        'query': user_query,
        'routing': routing,
        'branch_result': branch_result,
        'final_response': final_response
    }
    
    print("=" * 70)
    print(" AGENTIC SYSTEM COMPLETE")
    print("=" * 70)
    
    return result


# ==================== MAIN EXECUTION ====================

# if __name__ == "__main__":
#     # Test queries
#     test_queries = [
#         "Show me my meetings this week"
#     ]
    
#     # Test with first query
#     query = test_queries[0]
    
#     result = agentic_agent(query)
    
#     # Print final response
#     print("\n" + "=" * 70)
#     print("📄 FINAL RESPONSE")
#     print("=" * 70)
#     print(result['final_response'])
#     print("=" * 70)
