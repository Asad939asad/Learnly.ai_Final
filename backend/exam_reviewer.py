import os
import sys
import json
import pickle
import hashlib
import shutil
import uuid

import fitz  # PyMuPDF
import faiss
from sentence_transformers import SentenceTransformer

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from tools.LLM_APIS import GEMINI_API_KEY, GROQ_API_KEY, ask_groq
from backend.agentic_agent import ask_gpt4
from tools.unified_search import unified_search
from tools.unified_search import unified_search

# ==================== CONFIGURATION ====================

EXAM_PREP_DIR = "exam-prep"
STUDY_MATERIALS_DIR = os.path.join(EXAM_PREP_DIR, "study_materials")
EXAM_FILES_DIR = os.path.join(EXAM_PREP_DIR, "exam_files")
FAISS_DIR = os.path.join(EXAM_PREP_DIR, "faiss_index")

MAX_TOKENS = 300
OVERLAP = 100
EMBED_DIM = 384  # all-MiniLM-L6-v2

# Create directories
os.makedirs(STUDY_MATERIALS_DIR, exist_ok=True)
os.makedirs(EXAM_FILES_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")


# ==================== RAG INDEXING ====================

def compute_hash(path):
    """Compute MD5 hash of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    doc = fitz.open(pdf_path)
    pages = [page.get_text("text") for page in doc]
    return "\n".join(pages)


def chunk_text(text):
    """Chunk text into smaller pieces with overlap."""
    chunks = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    for para in paragraphs:
        tokens = para.split()

        if len(tokens) <= MAX_TOKENS:
            chunks.append(" ".join(tokens))
            continue

        start = 0
        while start < len(tokens):
            end = start + MAX_TOKENS
            chunks.append(" ".join(tokens[start:end]))
            start += MAX_TOKENS - OVERLAP

    return chunks


def index_study_materials():
    """
    Index all PDF files in study_materials and exam_files directories.
    Files are deleted after successful indexing to prevent re-indexing.
    
    Returns:
        Number of files indexed
    """
    print("=" * 70)
    print("📚 INDEXING STUDY MATERIALS")
    print("=" * 70 + "\n")
    
    # Check both directories for PDF files
    study_pdfs = [(STUDY_MATERIALS_DIR, f) for f in os.listdir(STUDY_MATERIALS_DIR) if f.lower().endswith(".pdf")]
    exam_pdfs = [(EXAM_FILES_DIR, f) for f in os.listdir(EXAM_FILES_DIR) if f.lower().endswith(".pdf")]
    
    all_pdfs = study_pdfs + exam_pdfs
    
    if not all_pdfs:
        print("ℹ️  No new files to index")
        print("   To add materials, place PDF files in:")
        print("   - exam-prep/study_materials/ (for study materials)")
        print("   - exam-prep/exam_files/ (for exam PDFs)\n")
        return 0
    
    print(f"📁 Found {len(all_pdfs)} PDF file(s) to index")
    if study_pdfs:
        print(f"   - {len(study_pdfs)} from study_materials/")
    if exam_pdfs:
        print(f"   - {len(exam_pdfs)} from exam_files/")
    print()
    
    index_path = os.path.join(FAISS_DIR, "index.faiss")
    meta_path = os.path.join(FAISS_DIR, "metadata.pkl")
    
    # Load or create index
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
        metadata = pickle.load(open(meta_path, "rb"))
        print(f"📊 Loaded existing index with {len(metadata)} chunks\n")
    else:
        index = faiss.IndexFlatL2(EMBED_DIM)
        metadata = []
        print("🆕 Creating new FAISS index\n")
    
    files_indexed = 0
    
    for directory, filename in all_pdfs:
        file_path = os.path.join(directory, filename)
        source = "study_materials" if directory == STUDY_MATERIALS_DIR else "exam_files"
        print(f"📄 Processing: {filename} (from {source})")
        
        try:
            # Extract and chunk
            text = extract_text_from_pdf(file_path)
            chunks = chunk_text(text)
            
            if not chunks:
                print("     No text found — skipping\n")
                # Delete file even if no text found
                os.remove(file_path)
                continue
            
            # Embed and store
            embeddings = embedder.encode(chunks, convert_to_numpy=True)
            index.add(embeddings)
            
            file_hash = compute_hash(file_path)
            
            for i, chunk in enumerate(chunks):
                metadata.append({
                    "id": str(uuid.uuid4()),
                    "file": filename,
                    "chunk_id": i,
                    "file_hash": file_hash,
                    "text": chunk,
                    "source": source
                })
            
            files_indexed += 1
            print(f"    Indexed {len(chunks)} chunks")
            
            # Delete file after successful indexing
            os.remove(file_path)
            print(f"   🗑️  Removed file from {source} folder\n")
            
        except Exception as e:
            print(f"    Error processing file: {e}")
            print(f"   File will remain in folder for retry\n")
            continue
    
    # Save index only if files were indexed
    if files_indexed > 0:
        faiss.write_index(index, index_path)
        pickle.dump(metadata, open(meta_path, "wb"))
        print(f"💾 Index saved successfully")
    
    print(f" Indexing complete! Files indexed: {files_indexed}")
    print(f"📊 Total chunks in index: {len(metadata)}\n")
    
    return files_indexed


def retrieve_top_chunks(query, k=2):
    """
    Retrieve top-k most similar chunks for a query.
    
    Args:
        query: Search query
        k: Number of chunks to retrieve
    
    Returns:
        List of chunk dictionaries with similarity scores
    """
    index_path = os.path.join(FAISS_DIR, "index.faiss")
    meta_path = os.path.join(FAISS_DIR, "metadata.pkl")
    
    if not os.path.exists(index_path):
        return []
    
    index = faiss.read_index(index_path)
    metadata = pickle.load(open(meta_path, "rb"))
    
    # Embed query
    query_embedding = embedder.encode([query], convert_to_numpy=True)
    
    # Search
    distances, indices = index.search(query_embedding, k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(metadata):
            similarity_score = 1 / (1 + distances[0][i])
            results.append({
                'rank': i + 1,
                'distance': float(distances[0][i]),
                'similarity_score': similarity_score,
                'file': metadata[idx]['file'],
                'chunk_id': metadata[idx]['chunk_id'],
                'text': metadata[idx]['text']
            })
    
    return results


# ==================== QUESTION EXTRACTION ====================

def extract_questions_from_exam(exam_pdf_path):
    """
    Extract questions from exam PDF using Gemini.
    
    Args:
        exam_pdf_path: Path to exam PDF file
    
    Returns:
        List of question dictionaries
    """
    print("📝 Extracting questions from exam PDF...\n")
    
    # Extract text from exam
    exam_text = extract_text_from_pdf(exam_pdf_path)
    
    prompt = f"""
Extract all questions from the following exam text.

Exam Text:
{exam_text}

Return ONLY a valid JSON array with this structure:
[
    {{"question_number": 1, "question_text": "question here"}},
    {{"question_number": 2, "question_text": "question here"}},
    ...
]

Rules:
- Extract each question exactly as written
- Number questions sequentially
- Return ONLY the JSON array, no additional text
"""
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt,
        )
        
        response_text = response.text.strip()
        
        # Remove markdown code blocks
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        questions = json.loads(response_text)
        
        print(f" Extracted {len(questions)} questions\n")
        return questions
        
    except Exception as e:
        print(f" Error extracting questions: {e}\n")
        return []


# ==================== ANSWER GENERATION ====================

def extract_questions_from_text(text):
    """
    Extracts questions from raw exam text using GPT-4.
    
    Args:
        text: Raw text from exam PDF
        
    Returns:
        List of question strings
    """
    print("🤖 Extracting questions from text with GPT-4...")
    
    prompt = f"""
    You are an expert exam parser. Your task is to extract all the questions from the provided exam text.
    
    EXAM TEXT:
    {text[:15000]}  # Limit to avoid token limits if text is massive
    
    INSTRUCTIONS:
    1. Identify all questions in the text.
    2. Ignore instructions, headers, footers, or extraneous text.
    3. Return ONLY a JSON object containing a list of strings, where each string is a question.
    4. The format must be: {{ "questions": ["Question 1 text", "Question 2 text", ...] }}
    5. Clean up the question text (remove question numbers like "1.", "Q1:", etc.).
    """
    
    try:
        response = ask_gpt4(prompt)
        
        # Robust extraction
        json_str = extract_json_from_text(response)
            
        data = json.loads(json_str)
        questions = data.get("questions", [])
        
        print(f" Extracted {len(questions)} questions")
        return questions
        
    except Exception as e:
        print(f" Error extracting questions: {e}")
        # Log failed string
        print(f"DEBUG: Failed questions JSON: {response[:500] if 'response' in locals() else 'None'}")
        return []


import re

def extract_json_from_text(text):
    """
    Robustly extract JSON object or array from text using regex.
    """
    text = text.strip()
    
    # Try to find JSON block enclosed in ```json ... ```
    match = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1)
    
    # Try to find JSON object {...}
    elif '{' in text and '}' in text:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            text = match.group(1)
            
    return text.strip()

def batch_generate_answers(questions_with_context):
    """
    Generates answers for a batch of questions to minimize LLM calls.
    
    Args:
        questions_with_context: List of dicts with 'question', 'rag_context', 'web_context'
        
    Returns:
        List of answer strings matching the order
    """
    if not questions_with_context:
        return []

    print(f"🤖 Batch generating answers for {len(questions_with_context)} questions...")
    
    prompt = """
    You are an expert academic tutor. Answering the following questions based *strictly* on the provided context.
    
    INSTRUCTIONS:
    1. You will be given multiple questions, each with its own "Context" (Study Notes + Web Search).
    2. For each question, generate a comprehensive, accurate, and helpful answer.
    3. If the context is empty or insufficient, use your own knowledge but state that "Context was insufficient, answering from general knowledge."
    4. Return valid JSON with a list of answers corresponding exactly to the input order.
    5. Format: { "answers": ["Answer 1", "Answer 2", ...] }
    
    QUESTIONS AND CONTEXT:
    """
    
    for i, item in enumerate(questions_with_context):
        prompt += f"""
        ---
        QUESTION {i+1}: {item['question']}
        
        STUDY NOTES CONTEXT:
        {item['rag_context']}
        
        WEB SEARCH CONTEXT:
        {item['web_context']}
        ---
        """
        
    try:
        response = ask_gpt4(prompt)
        print(f"DEBUG: Raw response: {response[:500]}...")
        
        # Robust extraction
        json_str = extract_json_from_text(response)
            
        data = json.loads(json_str)
        answers = data.get("answers", [])
        
        if len(answers) != len(questions_with_context):
            print(f" Warning: Generated {len(answers)} answers for {len(questions_with_context)} questions. Padding/Truncating.")
            if len(answers) < len(questions_with_context):
                answers += ["Error generating answer found."] * (len(questions_with_context) - len(answers))
            else:
                answers = answers[:len(questions_with_context)]
                
        return answers

    except Exception as e:
        print(f" Error in batch generation: {e}")
        print(f"DEBUG: Failed JSON string: {json_str[:500] if 'json_str' in locals() else 'Not created'}")
        return ["Error generating answer"] * len(questions_with_context)


def generate_answer_with_context(question, rag_context, web_context):
    """
    Generate answer using GPT-4.1 with combined RAG and Web context.
    """
    prompt = f"""
    You are an expert academic tutor. Answer the questions minimally based on the provided study notes and web search results if provided.
    
    QUESTION: {question}
    
    STUDY NOTES CONTEXT:
    {rag_context if rag_context else "No relevant study notes found."}
    
    WEB SEARCH CONTEXT:
    {web_context if web_context else "No relevant web search results found."}
    
    INSTRUCTIONS:
    - Synthesize information from both sources.
    - Prioritize Study Notes if they are directly relevant.
    - Use Web Search to fill gaps or provide latest info.
    - If neither source has the answer, answer from your general knowledge but mention it.
    """
    
    # Simple system prompt
    system_prompt = "You are an exam preparation assistant. Provide accurate answers based on the given context."
    
    return ask_gpt4(prompt, system_prompt)


# ==================== CRITIC EVALUATION ====================

def evaluate_with_critic(question, answer, chunks):
    """
    Evaluate answer relevancy using Grok as critic.
    
    Args:
        question: Question text
        answer: Generated answer
        chunks: Retrieved chunks used for context
    
    Returns:
        Dictionary with relevancy score and feedback
    """
    context = "\n\n".join([chunk['text'] for chunk in chunks])
    
    prompt = f"""
Evaluate the relevancy between the question, answer, and source context.

Question: {question}

Answer: {answer}

Source Context:
{context}

Return ONLY a valid JSON object:
{{
    "relevancy_score": 0.0 to 1.0,
    "feedback": "brief explanation of the score"
}}

Rules:
- Score 1.0 if answer directly addresses question using context
- Score 0.5 if answer is partially relevant
- Score 0.0 if answer is irrelevant or incorrect
- Return ONLY the JSON object
"""
    
    try:
        response = ask_groq(prompt, stream=True)
        
        # Remove markdown if present
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        
        response = response.strip()
        
        evaluation = json.loads(response)
        return evaluation
        
    except Exception as e:
        print(f" Critic evaluation error: {e}")
        return {"relevancy_score": 0.5, "feedback": "Error in evaluation"}


# ==================== MAIN EXAM REVIEWER ====================

def review_exam(exam_pdf_path=None, user_question=None):
    """
    Main exam reviewer function.
    
    Args:
        exam_pdf_path: Path to exam PDF (optional if user_question provided)
        user_question: Direct question from user (optional)
    
    Returns:
        Dictionary with results
    """
    print("=" * 70)
    print("🎓 EXAM REVIEWER (Enhanced Pipeline)")
    print("=" * 70 + "\n")
    
    results = []
    
    # --- Step 1: Get Questions ---
    questions = []
    if user_question:
        print(f"👤 Processing single user question: {user_question}\n")
        questions = [{"question_number": 1, "question_text": user_question}]
    elif exam_pdf_path:
        print(f"📄 Processing exam file: {exam_pdf_path}\n")
        try:
            exam_text = extract_text_from_pdf(exam_pdf_path)
            raw_questions = extract_questions_from_text(exam_text)
            questions = [{"question_number": i+1, "question_text": q} for i, q in enumerate(raw_questions)]
        except Exception as e:
            return {"status": "error", "message": f"Failed to process exam file: {str(e)}"}
    
    if not questions:
        return {"status": "error", "message": "No questions found"}
    
    # --- Step 2: Retrieve Context (RAG + Web) ---
    questions_to_answer = []
    
    for q in questions:
        print(f"\n{'='*50}")
        print(f"Processing Q{q['question_number']}: {q['question_text']}")
        print(f"{'='*50}\n")
        
        # A. RAG Retrieval
        print("🔍 Retrieving study materials (RAG)...")
        chunks = retrieve_top_chunks(q['question_text'], k=3)
        rag_chunks = [c for c in chunks if c['similarity_score'] >= 0.3]
        
        rag_context = ""
        chunks_used = 0
        if rag_chunks:
            rag_context = "\n\n".join([f"Source ({c['file']}): {c['text']}" for c in rag_chunks])
            chunks_used = len(rag_chunks)
            print(f" RAG found {chunks_used} chunks")
        else:
            print(" No relevant study materials found")
            
        # B. Unified Search (Web)
        # Enable for all questions to ensure comprehensive answers
        print("🌐 Performing Unified Search...")
        web_result = unified_search(q['question_text'])
        
        web_context = ""
        web_used = False
        if web_result and web_result.get('status') == 'success':
            web_data = web_result.get('web_search')
            wiki_data = web_result.get('wikipedia_search')
            
            web_text = web_data.get('content', '') if web_data else ''
            wiki_text = wiki_data.get('content', '') if wiki_data else ''
            
            # Truncate to user specified limits (2500 chars each)
            web_text = web_text[:2500] if web_text else ""
            wiki_text = wiki_text[:2500] if wiki_text else ""
            
            web_context = f"Web Search:\n{web_text}\n\nWikipedia:\n{wiki_text}"
            web_used = True
            print(" Unified Search provided context")
        else:
            print(" Unified Search turned up nothing")
            
        # Store for generation
        q['rag_context'] = rag_context
        q['web_context'] = web_context
        q['chunks_used'] = chunks_used
        q['web_used'] = web_used
        
        questions_to_answer.append(q)

    # --- Step 3: Generates Answers ---
    
    answers = []
    if len(questions_to_answer) == 1:
        # Single Question Mode
        q_item = questions_to_answer[0]
        print("\n🤖 Generating single answer with enhanced context...")
        ans = generate_answer_with_context(q_item['question_text'], q_item['rag_context'], q_item['web_context'])
        answers = [ans]
    else:
        # Batch Mode for Exam Files
        print(f"\n🤖 Batch generating answers for {len(questions_to_answer)} questions...")
        batch_input = []
        for q in questions_to_answer:
            # Truncate context to avoid token limits (approx 4000 chars total context per Q)
            # RAG context: 2000 chars
            rag_truncated = q['rag_context'][:2000] if q['rag_context'] else ""
            # Web context: 5000 chars (2500 web + 2500 wiki)
            web_truncated = q['web_context'][:5000] if q['web_context'] else ""
            
            batch_input.append({
                'question': q['question_text'],
                'rag_context': rag_truncated,
                'web_context': web_truncated
            })
        
        # Process in smaller batches of 2 questions
        answers = []
        batch_size = 2
        for i in range(0, len(batch_input), batch_size):
            batch_chunk = batch_input[i:i + batch_size]
            print(f"   Processing batch {i//batch_size + 1} ({len(batch_chunk)} questions)...")
            batch_answers = batch_generate_answers(batch_chunk)
            answers.extend(batch_answers)

    # --- Step 4: Format Results ---
    for i, q in enumerate(questions_to_answer):
        answer_text = answers[i] if i < len(answers) else "Error generating answer"
        
        # Calculate status
        status = "success"
        if q['chunks_used'] == 0 and not q['web_used']:
            status = "low_confidence"
            
        results.append({
            "question_number": q['question_number'],
            "question": q['question_text'],
            "answer": answer_text,
            "relevancy_score": 1.0 if status == "success" else 0.0, # Simplified for now
            "chunks_used": q['chunks_used'],
            "web_used": q['web_used'],
            "status": status
        })

    print("=" * 70)
    print(" EXAM REVIEW COMPLETE")
    print("=" * 70)
    
    return {
        "status": "success",
        "total_questions": len(questions),
        "results": results
    }


# ==================== MAIN EXECUTION ====================

# if __name__ == "__main__":
#     # Example usage
    
#     # # Step 1: Index study materials
#     # print("Step 1: Indexing study materials...")
#     # index_study_materials()
    
#     # # Step 2: Review exam or answer question
#     # # Option A: Review entire exam
#     # # exam_path = os.path.join(EXAM_FILES_DIR, "exam.pdf")
#     # # results = review_exam(exam_path)
    
#     # # Option B: Answer single question
#     # question = "What is computer vision?"
#     # results = review_exam(None, user_question=question)
    
#     # # Print results
#     # print("\n" + "=" * 70)
#     # print("📄 RESULTS")
#     # print("=" * 70)
#     # print(json.dumps(results, indent=2, ensure_ascii=False))
