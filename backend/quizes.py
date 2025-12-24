# backend/quizes.py

import os
import sys
import requests
import json
import datetime
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor # NEW: For concurrent grading

# Import unified search and Gemini
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.unified_search import unified_search
from google import genai
from tools.LLM_APIS import GEMINI_API_KEY, GROQ_API_KEY

# Ensure this is set in your environment
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_quiz(
    prompt: str,
    num_questions: int,
    difficulty: str,
    mcq_percent: int,
    rag_context: Optional[str] = None # Added for future RAG integration
) -> Dict[str, Any]:
    """
    Calls the Groq LLM to generate a quiz based on user-defined parameters.
    (This function remains the same as the previous version)
    """
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY environment variable")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Calculate question mix
    num_mcq = round(num_questions * (mcq_percent / 100))
    num_short_answer = num_questions - num_mcq
    
    # === Web Search Integration (ALWAYS) ===
    # ALWAYS use unified search (compulsory)
    print(f"🌐 Using unified search to gather information about: {prompt}")
    search_result = unified_search(prompt)
    
    search_context = []
    if search_result.get('status') == 'success':
        web_content = search_result.get('web_search', {})
        wiki_content = search_result.get('wikipedia_search', {})
        
        if web_content:
            search_context.append(f"Web Source: {web_content.get('content', '')}")
        if wiki_content:
            search_context.append(f"Wikipedia: {wiki_content.get('content', '')}")
        
        print(f" Retrieved information from unified search")
    
    # Additionally use RAG context if provided
    if rag_context:
        search_context.append(f"Additional Context: {rag_context}")
        print(f" Added RAG context")
    
    rag_instruction = ""
    if search_context:
        rag_instruction = f"Use the following information to create relevant quiz questions:\n{chr(10).join(search_context)}\n\n"
    # ========================================

    # Construct the dynamic system prompt
    system_prompt = f"""
    You are a professional quiz generator. Your task is to create a quiz based on the user's request.
    
    # Quiz Generation Requirements
    1. The quiz must have exactly {num_questions} questions.
    2. The difficulty level must be **{difficulty}**.
    3. The question mix must be: 
        - Approximately {num_mcq} Multiple Choice Questions (MCQ)
        - Approximately {num_short_answer} Short Answer Questions
    4. Ensure the Short Answer questions require a concise, single correct answer for future automated grading.
    5. {rag_instruction}

    # Question Quality Guidelines
    - Keep questions CLEAR and CONCISE - avoid overly complex or wordy questions
    - Focus on testing UNDERSTANDING and APPLICATION rather than memorization
    - Make questions PRACTICAL and relevant to real-world scenarios when possible
    - Avoid questions that are too philosophical or abstract
    - For MCQ: Ensure all options are plausible but only one is clearly correct
    - For MCQ: Keep options SHORT (1-2 lines maximum)
    - Questions should be straightforward and easy to understand

    # Output Format
    Always return the output as a JSON object in this exact schema. The 'correct_answer' and 'explanation' fields are critical for the grading system.
    {{
      "quiz": {{
        "title": string,
        "topic": string,
        "metadata": {{
          "difficulty": "{difficulty}",
          "num_questions": {num_questions},
          "generated_at": string (ISO8601 datetime)
        }},
        "questions": [
          {{
            "id": string (unique ID for the question),
            "type": "mcq" | "short_answer",
            "question": string (clear and concise),
            "options": [string] (only if type='mcq' and must have 4 SHORT options),
            "correct_answer": string (the exact correct option text for mcq, or the exact expected answer for short_answer),
            "explanation": string (A clear explanation of why this answer is correct)
          }}
        ]
      }}
    }}
    Do not include any text before or after the JSON. Return only valid JSON.
    """

    # Use Gemini API for quiz generation
    if not GEMINI_API_KEY:
        raise ValueError("Missing GEMINI_API_KEY")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=f"{system_prompt}\n\nGenerate a quiz for the topic: {prompt}",
    )

    # Extract quiz JSON text
    quiz_text = response.text.strip()
    
    # Remove markdown code blocks if present
    if quiz_text.startswith('```json'):
        quiz_text = quiz_text[7:]
    if quiz_text.startswith('```'):
        quiz_text = quiz_text[3:]
    if quiz_text.endswith('```'):
        quiz_text = quiz_text[:-3]
    quiz_text = quiz_text.strip()

    try:
        quiz_json = json.loads(quiz_text)
        # Ensure 'generated_at' is present for completeness
        if 'metadata' in quiz_json['quiz']:
            quiz_json['quiz']['metadata']['generated_at'] = datetime.datetime.now().isoformat()
    except json.JSONDecodeError:
        raise ValueError(f"Model returned invalid JSON: {quiz_text}")

    return quiz_json

# ----------------------------------------------------------------------
# NEW GRADING IMPLEMENTATION
# ----------------------------------------------------------------------

def semantically_grade_short_answer(
    question: str, 
    user_answer: str, 
    correct_answer: str, 
    explanation: str
) -> Dict[str, Any]:
    """
    Calls the Groq LLM to semantically grade a short answer.
    This is a synchronous, blocking function designed to be run in a thread.
    """
    if not GROQ_API_KEY:
        # In a real app, you might fall back to simple string matching here
        # or raise an error depending on your design.
        return {'is_correct': False, 'llm_explanation': "Grading failed: Missing API Key."}

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = f"""
    You are an impartial academic grader. Your task is to evaluate a student's answer based on the provided correct answer and question.

    # Grading Rules
    1. **Strictness:** Be lenient. If the student captures the core concept, structure, or main keywords of the correct answer, mark it as **True**. Spelling or minor grammatical errors should be ignored.
    2. **Output:** You MUST respond with ONLY a single JSON object.
    
    # Context
    Question: {question}
    Correct/Expected Answer: {correct_answer}
    Original Explanation: {explanation}
    
    # Output Schema
    {{
      "is_correct": boolean,
      "llm_explanation": string (A 1-2 sentence tailored feedback on why the student was correct/incorrect, referencing the core concept.)
    }}
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Student's Answer to Grade: {user_answer}"}
        ],
        "temperature": 0.3, # Use a low temp for reliable, deterministic grading
        "max_tokens": 500
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Extract and parse the LLM's JSON response
        llm_text = data["choices"][0]["message"]["content"].strip()
        
        # Groq often wraps the JSON in markdown blocks, so we clean it up
        if llm_text.startswith("```json"):
            llm_text = llm_text[7:-3].strip()
            
        llm_result = json.loads(llm_text)
        
        # Return the parsed result, ensuring the keys are present
        return {
            'is_correct': llm_result.get('is_correct', False),
            'llm_explanation': llm_result.get('llm_explanation', "LLM failed to provide specific feedback.")
        }
        
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, ValueError) as e:
        # Catch any errors (API down, timeout, invalid JSON) and fail safely
        print(f"Error during LLM grading: {e}")
        return {
            'is_correct': False,
            'llm_explanation': f"An error occurred during automated grading ({type(e).__name__}). The expected answer was: {correct_answer}."
        }

def grade_quiz(quiz_data: Dict[str, Any], user_answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Compares user answers against the correct answers and generates feedback.
    Uses concurrent threads for LLM-based semantic grading of short answers.
    """
    
    def grade_single_question_task(q: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
        """Handles the grading logic for a single question."""
        q_id = q['id']
        correct_answer = q['correct_answer'].strip()
        explanation = q['explanation']
        is_correct = False
        final_explanation = explanation
        
        user_answer_stripped = user_answer.strip() 

        if q['type'] == 'mcq':
            # Case-insensitive string comparison for MCQs
            is_correct = (user_answer_stripped.lower() == correct_answer.lower())
            
        elif q['type'] == 'short_answer':
            
            # === THE CRITICAL FIX IS HERE ===
            if not user_answer_stripped:
                is_correct = False # An empty answer is never correct for short answer.
                final_explanation = f"You did not provide an answer. The correct answer was: {correct_answer}. Please review the explanation."
            else:
                # Proceed to LLM grading only if an answer was provided
                llm_result = semantically_grade_short_answer(
                    q['question'], user_answer_stripped, correct_answer, explanation
                )
                is_correct = llm_result.get('is_correct', False)
                # Overwrite the simple explanation with the richer LLM feedback
                final_explanation = llm_result['llm_explanation'] 

        return {
            'id': q_id,
            'is_correct': is_correct,
            'user_answer': user_answer_stripped,
            'correct_answer': correct_answer,
            'explanation': final_explanation
        }

    # 1. Prepare data for concurrent execution
    grading_tasks = []
    for q in quiz_data['quiz']['questions']:
        q_id = q['id']
        # Pass the raw user answer from the dictionary
        user_answer = user_answers.get(f"answer-{q_id}", "") 
        # Add the function call arguments to a list for the executor
        grading_tasks.append((q, user_answer))

    # 2. Run grading tasks concurrently using a ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        graded_results: List[Dict[str, Any]] = list(executor.map(
            lambda args: grade_single_question_task(*args), grading_tasks
        ))
    
    # 3. Calculate final score
    total_questions = len(graded_results)
    correct_count = sum(1 for result in graded_results if result['is_correct'])

    # 4. Compile the final score and results
    return {
        'status': 'graded',
        'score': f"{correct_count}/{total_questions}",
        'percent': round((correct_count / total_questions) * 100) if total_questions > 0 else 0,
        'results': graded_results
    }
# ==================== TESTING ====================
if __name__ == "__main__":
    import json
    
    print("=" * 70)
    print("🎯 QUIZ GENERATOR TEST")
    print("=" * 70 + "\n")
    
    # Test quiz generation
    quiz = generate_quiz(
        prompt="generate quiz on computer networks and subnetting?",
        num_questions=5,
        difficulty="medium",
        mcq_percent=60,  # 60% MCQ, 40% short answer
        rag_context=None  # Will use unified search
    )
    
    print("\n" + "=" * 70)
    print("📝 GENERATED QUIZ")
    print("=" * 70)
    print(json.dumps(quiz, indent=2))
    
    print("\n" + "=" * 70)
    print(" Quiz generation complete!")
    print("=" * 70)
