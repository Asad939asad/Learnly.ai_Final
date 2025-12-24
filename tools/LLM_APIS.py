"""
LLM API Integration Module
Supports: Google Gemini and Groq
"""
#AIzaSyCO_u2fToeQ1_Q-d7DLMRc2mjmSXJkxX9I
from google import genai
from groq import Groq

# ==================== API KEYS ====================


# ==================== GEMINI API ====================

def ask_gemini(prompt, model="models/gemini-2.5-flash"):
    """
    Query Google Gemini API.
    
    Args:
        prompt: The question or prompt to send
        model: Gemini model to use (default: models/gemini-2.5-flash)
        
    Returns:
        str: The response text from Gemini
    """
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        
        return response.text
    
    except Exception as e:
        return f" Gemini Error: {e}"

def ask_gemini_structured(prompt, model="models/gemini-2.5-flash", use_learning_key=False, history=None):
    """
    Query Google Gemini API with structured JSON response support.
    
    Args:
        prompt: The question or prompt to send
        model: Gemini model to use (default: models/gemini-2.5-flash)
        use_learning_key: Use the learning agent API key instead of default
        history: Optional conversation history list of dicts with 'role' and 'content'
        
    Returns:
        dict: Parsed JSON response from Gemini, or error dict
    """
    import json
    import re
    
    try:
        api_key = GEMINI_LEARNING_API_KEY if use_learning_key else GEMINI_API_KEY
        client = genai.Client(api_key=api_key)
        
        # Build contents with history if provided
        contents = []
        if history:
            for turn in history:
                contents.append(turn)
        contents.append(prompt)
        
        response = client.models.generate_content(
            model=model,
            contents=contents,
        )
        
        raw_text = response.text.strip()
        
        # Extract JSON from response (handles markdown code blocks)
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if not match:
            return {"error": "No JSON found in response", "raw": raw_text}
        
        parsed = json.loads(match.group())
        return parsed
    
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}", "raw": response.text if 'response' in locals() else ""}
    except Exception as e:
        return {"error": f"Gemini Error: {e}"}

# ==================== GROQ API ====================

def ask_groq(prompt, stream=True):
    """
    Query Groq API with GPT-OSS-20B model.
    
    Args:
        prompt: The question or prompt to send
        model: Groq model to use (default: openai/gpt-oss-20b)
        stream: Whether to stream the response (default: True)
        
    Returns:
        str: The response text from Groq
    """
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
            {
                "role": "user",
                "content": prompt
            }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None
        )
        
        if stream:
            # Handle streaming response
            result = ""
            for chunk in completion:
                content = chunk.choices[0].delta.content or ""
                result += content
            return result
        else:
            # Return complete response
            return completion.choices[0].message.content
    
    except Exception as e:
        return f" Groq Error: {e}"

def ask_groq_structured(prompt, model="llama-3.3-70b-versatile", history=None):
    """
    Query Groq API with structured JSON response support.
    
    Args:
        prompt: The question or prompt to send
        model: Groq model to use (default: llama-3.3-70b-versatile)
        history: Optional conversation history list of dicts with 'role' and 'content'
        
    Returns:
        dict: Parsed JSON response from Groq, or error dict
    """
    import json
    import re
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # Build messages with history if provided
        messages = []
        if history:
            for turn in history:
                messages.append({
                    "role": turn.get("role", "user"),
                    "content": turn.get("content", "")
                })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_completion_tokens=2048,
            top_p=1,
            stream=False,
            stop=None
        )
        
        raw_text = completion.choices[0].message.content.strip()
        
        # Extract JSON from response (handles markdown code blocks)
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if not match:
            return {"error": "No JSON found in response", "raw": raw_text}
        
        parsed = json.loads(match.group())
        return parsed
    
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}", "raw": completion.choices[0].message.content if 'completion' in locals() else ""}
    except Exception as e:
        return {"error": f"Groq Error: {e}"}

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Example prompt
    prompt = "where is imran khan right now?"
    
    print("="*70)
    print("🤖 LLM API COMPARISON")
    print("="*70)
    print(f"\nPrompt: {prompt}\n")
    
    # Test Gemini
    print("-"*70)
    print("📘 GEMINI RESPONSE:")
    print("-"*70)
    gemini_response = ask_gemini(prompt)
    print(gemini_response)
    
    # Test Groq
    print("\n" + "-"*70)
    print("🚀 GROQ RESPONSE:")
    print("-"*70)
    groq_response = ask_groq(prompt)
    print(groq_response)
    
    print("\n" + "="*70)
    print("✨ Done!")
    print("="*70)