# def generate_flashcards(use_rag=False):
#     """
#     Generate sample flashcards. This function will be enhanced later with actual RAG implementation.
#     """
#     sample_cards = [
#         {
#             "question": "What is the capital of France?",
#             "answer": "Paris"
#         },
#         {
#             "question": "What is the largest planet in our solar system?",
#             "answer": "Jupiter"
#         },
#         {
#             "question": "Who wrote 'Romeo and Juliet'?",
#             "answer": "William Shakespeare"
#         }
#     ]
    
#     return {
#         "status": "success",
#         "flashcards": sample_cards
#     }



# def generate_flashcards(use_rag=False):
#     """
#     Generate sample flashcards. This function will be enhanced later with actual RAG implementation.
#     """
#     sample_cards = [
#         {
#             "question": "What is the capital of France?",
#             "answer": "Paris"
#         },
#         {
#             "question": "What is the largest planet in our solar system?",
#             "answer": "Jupiter"
#         },
#         {
#             "question": "Who wrote 'Romeo and Juliet'?",
#             "answer": "William Shakespeare"
#         }
#     ]
    
#     return {
#         "status": "success",
#         "flashcards": sample_cards
#     }



import os
import sys
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from dotenv import load_dotenv

# Import unified search and Gemini
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.unified_search import unified_search
from sentence_transformers import SentenceTransformer
from google import genai
from tools.LLM_APIS import GEMINI_API_KEY

# Load variables from .env
load_dotenv()

# ============= SETTINGS ============
INDEX_FOLDER = "./chroma_index"  # root folder for embeddings
# ==================================


# ============= WRAPPER FOR SENTENCE TRANSFORMER ============
class SentenceTransformerWrapper:
    """Wrapper to make SentenceTransformer compatible with Chroma."""
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
    
    def embed_documents(self, texts):
        """Embed a list of documents."""
        return self.model.encode(texts, convert_to_numpy=True).tolist()
    
    def embed_query(self, text):
        """Embed a single query."""
        return self.model.encode([text], convert_to_numpy=True)[0].tolist()
# ===========================================================



def normalize_book_name(book_name: str) -> str:
    """Remove .pdf extension (if present) and normalize spaces/underscores."""
    if book_name.lower().endswith(".pdf"):
        book_name = book_name[:-4]
    return book_name.replace(" ", "_")


def load_index(book_name: str, embeddings):
    """Load an existing Chroma index for a book, error if not found."""
    normalized_name = normalize_book_name(book_name)
    book_index_folder = os.path.join(INDEX_FOLDER, normalized_name)

    if not os.path.exists(book_index_folder) or not os.listdir(book_index_folder):
        raise FileNotFoundError(
            f"No Chroma index found for '{book_name}' in {book_index_folder}. "
            "Please create the index first."
        )

    print(f"Loading existing index for '{book_name}'...")
    return Chroma(
        persist_directory=book_index_folder,
        embedding_function=embeddings
    )


def generate_flashcards(embeddings, sample_query: str, class_name: str, subjects: list, rag: bool, book_name: str = None):
    """
    Generate 10 flashcards in JSON format.
    - ALWAYS uses unified search for each question
    - Additionally uses RAG if available or provided
    - Uses SINGLE Gemini API call for all flashcards
    - Flash cards should be logical questions on which the student should apply his critical thinking skills to answer it
    """
    try:
        if not GEMINI_API_KEY:
            raise ValueError("Missing GEMINI_API_KEY")
        
        # Use Gemini API
        client = genai.Client(api_key=GEMINI_API_KEY)

        # ALWAYS use unified search (compulsory)
        print(f"Using unified search for topic: {sample_query}")
        search_result = unified_search(sample_query)
        
        context = []
        if search_result.get('status') == 'success':
            web_content = search_result.get('web_search', {})
            wiki_content = search_result.get('wikipedia_search', {})
            
            if web_content:
                context.append(f"Web: {web_content.get('content', '')[:1000]}")
            if wiki_content:
                context.append(f"Wikipedia: {wiki_content.get('content', '')[:1000]}")
        
        # Additionally use RAG if available
        if rag and book_name:
            db = load_index(book_name, embeddings)
            results = db.similarity_search(sample_query, k=5)
            rag_context = [res.page_content[:500] for res in results]
            context.extend(rag_context)

        # SINGLE API CALL: Generate all 10 flashcards at once
        flashcard_prompt = f"""
        You are a teacher creating flashcards for students in {class_name}.
        Topic: "{sample_query}"
        Subjects: {", ".join(subjects)}

        Context:
        {chr(10).join(context) if context else "Use your general knowledge."}

        Generate exactly 10 flashcards with questions and answers.
        Each answer should be 1-2 lines only.

        Return ONLY a JSON array in this exact format:
        [
          {{"question": "Question 1?", "answer": "Answer 1"}},
          {{"question": "Question 2?", "answer": "Answer 2"}},
          ...
        ]
        """
        
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=flashcard_prompt,
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
        import json
        flashcards = json.loads(response_text)
        
        return flashcards[:10]  # Ensure max 10

    except Exception as e:
        return {"status": "error", "message": str(e)}


# Run standalone (for testing)
# if __name__ == "__main__":
#     # Use SentenceTransformer with wrapper for Chroma compatibility
#     embeddings = SentenceTransformerWrapper("all-MiniLM-L6-v2")
    
#     result = generate_flashcards(
#         embeddings=embeddings,
#         sample_query="Photosynthesis basics",
#         class_name="Grade 6",
#         subjects=["Biology", "Science"],
#         rag=True,  # set to False to skip RAG
#         book_name="ec2.pdf"
#     )
#     import json
#     print(json.dumps(result, indent=2))
