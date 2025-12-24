"""
Adaptive Learning Agent
Uses dual-phase Groq architecture for true agentic behavior:
- Phase 1: Analyze and Plan
- Phase 2: Execute and Test
"""

import os
import sys
import json
from typing import Dict, Optional, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.LLM_APIS import ask_groq_structured, ask_gemini_structured
from tools.ocr_tool import image_to_ocr_string
from tools.unified_search import unified_search
from backend.history_manager import HistoryManager


# ==================== PHASE 1: ANALYZE & PLAN ====================

def phase_1_analyze_and_plan(
    user_input: str,
    ocr_text: Optional[str] = None,
    history_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    First Groq call: Analyze query and create execution plan
    
    Args:
        user_input: User's query or input
        ocr_text: Optional text extracted from image via OCR
        history_summary: Optional conversation history summary
        
    Returns:
        Dictionary with analysis and plan:
        {
            'needs_search': bool,
            'search_query': str,
            'search_type': 'web'|'wikipedia'|'both',
            'action_plan': str,
            'reasoning': str,
            'learning_goal': str
        }
    """
    
    prompt = f"""You are an intelligent learning assistant planner. Your job is to analyze the user's query and create an execution plan.

CONTEXT:
- User query: "{user_input}"
{f'- Text from uploaded image (OCR): "{ocr_text}"' if ocr_text else '- No image provided'}
{f'- Recent conversation context: {history_summary}' if history_summary else '- No previous conversation'}

YOUR TASK:
Analyze this learning query and decide what actions to take.

DECISION CRITERIA:
1. Does this query need external information (web search or Wikipedia)?
   - Use search for: factual questions, current events, definitions, explanations
   - Skip search for: personal questions, greetings, clarifications about previous answers
   
2. What is the user trying to learn?
   - Identify the core learning goal
   - Consider their knowledge level from context

3. What's the best approach to help them learn?
   - Should we explain concepts step-by-step?
   - Should we provide examples?
   - Should we create a quiz or test?

OUTPUT FORMAT (STRICT JSON):
{{
  "needs_search": true/false,
  "search_query": "optimized query if search needed, empty string otherwise",
  "search_type": "web" or "wikipedia" or "both" or "none",
  "action_plan": "Brief plan of how to respond (2-3 sentences)",
  "reasoning": "Why you made these decisions (1-2 sentences)",
  "learning_goal": "What the user wants to learn (1 sentence)"
}}

IMPORTANT:
- Return ONLY valid JSON
- No markdown, no explanations outside JSON
- Be decisive and clear
"""
    
    print("🤖 Phase 1: Analyzing and Planning...")
    result = ask_groq_structured(
        prompt=prompt
    )
    
    if "error" in result:
        print(f"    Error: {result['error']}")
        # Return fallback plan
        return {
            "needs_search": False,
            "search_query": "",
            "search_type": "none",
            "action_plan": "Provide a direct response based on general knowledge",
            "reasoning": "Error in planning phase, falling back to direct response",
            "learning_goal": "Answer user's question"
        }
    
    print(f"    Plan created:")
    print(f"      - Needs search: {result.get('needs_search', False)}")
    print(f"      - Learning goal: {result.get('learning_goal', 'Unknown')}")
    
    return result


# ==================== PHASE 2: EXECUTE & TEST ====================

def phase_2_execute_and_test(
    user_input: str,
    plan: Dict[str, Any],
    search_results: Optional[Dict] = None,
    ocr_text: Optional[str] = None,
    history_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    Second Groq call: Execute plan and generate response with test
    
    Args:
        user_input: Original user query
        plan: Plan from phase 1
        search_results: Optional search results if search was performed
        ocr_text: Optional OCR text
        history_summary: Optional conversation history
        
    Returns:
        Dictionary with response and validation:
        {
            'response': str,
            'test_snippet': str,
            'confidence': float,
            'follow_up_suggestions': list,
            'key_concepts': list
        }
    """
    
    # Build context from available resources
    context_parts = []
    
    if ocr_text:
        context_parts.append(f"Text from image: {ocr_text}")
    
    if search_results:
        if search_results.get('web_search'):
            web = search_results['web_search']
            context_parts.append(f"Web source ({web['title']}): {web['content'][:800]}")
        
        if search_results.get('wikipedia_search'):
            wiki = search_results['wikipedia_search']
            context_parts.append(f"Wikipedia ({wiki['title']}): {wiki['content'][:800]}")
    
    context_str = "\n\n".join(context_parts) if context_parts else "No external resources available"
    
    prompt = f"""You are an expert learning tutor. Your job is to help the user learn effectively.

USER QUERY: "{user_input}"

EXECUTION PLAN:
{json.dumps(plan, indent=2)}

AVAILABLE RESOURCES:
{context_str}

{f'CONVERSATION CONTEXT: {history_summary}' if history_summary else ''}

YOUR TASK:
Generate an educational response that helps the user learn. Follow the execution plan.

GUIDELINES:
1. Explain concepts clearly and step-by-step
2. Use analogies and examples when helpful
3. Adapt to the user's knowledge level
4. Be encouraging and supportive
5. Create a test/quiz question to validate understanding
6. Suggest relevant follow-up topics

OUTPUT FORMAT (STRICT JSON):
{{
  "response": "Your clear, educational explanation (3-5 paragraphs)",
  "test_snippet": "A quiz question or code snippet to test understanding",
  "confidence": 0.0-1.0 (how confident you are in this response),
  "follow_up_suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
  "key_concepts": ["concept 1", "concept 2", "concept 3"]
}}

IMPORTANT:
- Return ONLY valid JSON
- No markdown, no explanations outside JSON
- Make the response educational and engaging
- The test_snippet should be practical and relevant
"""
    
    print("🎓 Phase 2: Executing and Creating Response...")
    result = ask_gemini_structured(
        prompt=prompt,
        use_learning_key=True
    )
    
    if "error" in result:
        print(f"    Error: {result['error']}")
        # Return fallback response
        return {
            "response": "I encountered an error generating a detailed response. Let me try to help with what I know: " + user_input,
            "test_snippet": "What did you learn from this explanation?",
            "confidence": 0.5,
            "follow_up_suggestions": ["Ask a follow-up question", "Request more details"],
            "key_concepts": []
        }
    
    print(f"    Response generated:")
    print(f"      - Confidence: {result.get('confidence', 0.0)}")
    print(f"      - Key concepts: {len(result.get('key_concepts', []))}")
    
    # Ensure test_snippet is always a string
    if 'test_snippet' in result and not isinstance(result['test_snippet'], str):
        result['test_snippet'] = str(result['test_snippet']) if result['test_snippet'] else "No test available"
    
    # Ensure all required fields have proper defaults
    result.setdefault('test_snippet', 'No test available')
    result.setdefault('follow_up_suggestions', [])
    result.setdefault('key_concepts', [])
    
    return result


# ==================== MAIN ORCHESTRATOR ====================

def process_learning_query(
    user_input: str,
    image_path: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main orchestrator for the learning agent
    Coordinates both phases and manages history
    
    Args:
        user_input: User's query or input
        image_path: Optional path to image file
        session_id: Optional session ID for history
        
    Returns:
        Complete response dictionary with all metadata
    """
    
    print("\n" + "=" * 70)
    print("🎯 ADAPTIVE LEARNING AGENT")
    print("=" * 70)
    print(f"Query: {user_input}\n")
    
    # Initialize or load history
    if session_id:
        history_manager = HistoryManager.load_session(session_id)
        if not history_manager:
            print(f"  Session {session_id} not found, creating new session")
            history_manager = HistoryManager()
    else:
        history_manager = HistoryManager()
    
    print(f"📝 Session: {history_manager.session_id}")
    
    # Process OCR if image provided
    ocr_text = None
    if image_path:
        print(f"\n📸 Processing image: {image_path}")
        ocr_text = image_to_ocr_string(image_path)
        if ocr_text and not ocr_text.startswith("Error"):
            print(f"    OCR extracted: {len(ocr_text)} characters")
        else:
            print(f"    OCR failed: {ocr_text}")
            ocr_text = None
    
    # Get conversation history summary
    history_summary = history_manager.summarize_history() if history_manager.history["turns"] else None
    
    # PHASE 1: Analyze and Plan
    print()
    plan = phase_1_analyze_and_plan(
        user_input=user_input,
        ocr_text=ocr_text,
        history_summary=history_summary
    )
    
    # Execute search if needed
    search_results = None
    tools_used = []
    
    if image_path:
        tools_used.append("ocr")
    
    if plan.get("needs_search", False):
        print(f"\n🔍 Performing search: {plan.get('search_query', user_input)}")
        
        try:
            # Add timeout to prevent getting stuck on PDFs or slow URLs
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Search operation timed out after 30 seconds")
            
            # Set 30 second timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            
            try:
                search_results = unified_search(
                    plan.get("search_query", user_input),
                    max_chars_per_source=1500
                )
                signal.alarm(0)  # Cancel alarm on success
                tools_used.append("unified_search")
                
                if search_results.get("status") == "success":
                    print(f"    Search completed: {search_results.get('total_chars', 0)} chars")
                else:
                    print(f"     Search had issues: {search_results.get('message', 'Unknown')}")
                    
            except TimeoutError as e:
                signal.alarm(0)
                print(f"     Search timed out - skipping search results")
                print(f"   💡 Continuing with available information...")
                search_results = {"status": "timeout", "message": "Search timed out"}
                
            except Exception as search_error:
                signal.alarm(0)
                print(f"     Search error: {str(search_error)[:150]}")
                print(f"   💡 Continuing without search results...")
                search_results = {"status": "error", "message": str(search_error)[:200]}
                
        except Exception as outer_error:
            print(f"    Unexpected error in search wrapper: {str(outer_error)[:150]}")
            search_results = {"status": "error", "message": "Search failed"}
    
    # PHASE 2: Execute and Test
    print()
    response_data = phase_2_execute_and_test(
        user_input=user_input,
        plan=plan,
        search_results=search_results,
        ocr_text=ocr_text,
        history_summary=history_summary
    )
    
    # Save to history
    history_manager.save_turn(
        user_input=user_input,
        agent_response=response_data.get("response", ""),
        metadata={
            "tools_used": tools_used,
            "confidence": response_data.get("confidence", 0.0),
            "plan": plan,
            "key_concepts": response_data.get("key_concepts", []),
            "test_snippet": response_data.get("test_snippet", ""),
            "follow_up_suggestions": response_data.get("follow_up_suggestions", []),
            "had_image": image_path is not None,
            "had_search": search_results is not None
        }
    )
    
    # Build final response
    final_response = {
        "session_id": history_manager.session_id,
        "response": response_data.get("response", ""),
        "test_snippet": response_data.get("test_snippet", ""),
        "confidence": response_data.get("confidence", 0.0),
        "follow_up_suggestions": response_data.get("follow_up_suggestions", []),
        "key_concepts": response_data.get("key_concepts", []),
        "metadata": {
            "tools_used": tools_used,
            "plan": plan,
            "ocr_text": ocr_text,
            "search_performed": search_results is not None,
            "turn_number": len(history_manager.history["turns"])
        }
    }
    
    print("\n" + "=" * 70)
    print(" PROCESSING COMPLETE")
    print("=" * 70)
    
    return final_response


# ==================== MAIN EXECUTION ====================

# if __name__ == "__main__":
#     # Test the learning agent
#     test_queries = [
#         {
#             "input": "What is elon musk networth right now?",
#             "image": None
#         },
#         {
#             "input": "Solve the math problem?",
#             "image": "/Users/asadirfan358/Documents/Learnly.AI-main/New Project (21)(111).jpg"
#         }
#     ]
    
#     # Test first query
#     query = test_queries[1]
    
#     result = process_learning_query(
#         user_input=query["input"],
#         image_path=query["image"]
#     )
    
#     # Print results
#     print("\n" + "=" * 70)
#     print("📄 FINAL RESPONSE")
#     print("=" * 70)
#     print(f"\nSession: {result['session_id']}")
#     print(f"\nResponse:\n{result['response']}")
#     print(f"\nTest/Quiz:\n{result['test_snippet']}")
#     print(f"\nConfidence: {result['confidence']}")
#     print(f"\nKey Concepts: {', '.join(result['key_concepts'])}")
#     print(f"\nFollow-up Suggestions:")
#     for i, suggestion in enumerate(result['follow_up_suggestions'], 1):
#         print(f"  {i}. {suggestion}")
#     print("\n" + "=" * 70)
