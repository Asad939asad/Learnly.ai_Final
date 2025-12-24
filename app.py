from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, make_response, session, send_file
from datetime import datetime
from langchain_core import embeddings
from werkzeug.utils import secure_filename
import os
import subprocess
import sys
import io
import json
# UPDATED IMPORT: Import both generate_quiz and the new grade_quiz function
from backend.quizes import generate_quiz, grade_quiz 
from backend.flashcards import generate_flashcards
from backend.query_rag import query_book_rag
from rag_com.indexer import indexer
from backend.slide_decks import generate_slide_deck, create_pdf_from_slides
from backend.manage_books import query_book_content
from backend.agentic_agent import agentic_agent
from backend.exam_reviewer import index_study_materials, review_exam, EXAM_FILES_DIR
from backend.learning_agent import process_learning_query
from langchain_huggingface import HuggingFaceEmbeddings

app = Flask(__name__)
app.config['BOOKS_FOLDER'] = 'books'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
from dotenv import load_dotenv
load_dotenv()
# app.secret_key = 'your-secret-key-here'  # Required for session

# Global variables to store dashboard inputs
global_class = None
global_subjects = []
global_study_topic = None

# Ensure required directories exist with proper permissions
os.makedirs(app.config['BOOKS_FOLDER'], exist_ok=True)
os.chmod(app.config['BOOKS_FOLDER'], 0o777)  # Full read/write permissions

# Ensure Chroma index directory exists with proper permissions
CHROMA_INDEX_DIR = os.path.join(os.getcwd(), 'chroma_index')
os.makedirs(CHROMA_INDEX_DIR, exist_ok=True)
os.chmod(CHROMA_INDEX_DIR, 0o777)  # Full read/write permissions

@app.route("/")
def dashboard():
    return render_template("dashboard.html", active_page='dashboard')

@app.route('/submit_user_info', methods=['POST'])
def submit_user_info():
    global global_class, global_subjects, global_study_topic
    
    data = request.get_json()
    global_class = data.get('class')
    global_subjects = data.get('subjects', [])
    global_study_topic = data.get('study_topic')
    
    return jsonify({"status": "success"})

@app.route('/quizes')
def quizes():
    books = get_available_books()
    return render_template('quizes.html', books=books, active_page='quizes')

# =========================================================
# QUIZ GENERATION ROUTE (Updated to accept parameters)
# =========================================================
@app.route("/generate_quiz", methods=["POST"])
def generate_quiz_route():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        num_questions = data.get('num_questions', 10)
        difficulty = data.get('difficulty', 'Medium')
        mcq_percent = data.get('mcq_percent', 70)
        book_name = data.get('book_name')  # Optional book selection
        
        # Get RAG context from book if selected
        rag_context = None
        if book_name:
            try:
                # Query the book for relevant context
                book_query_result = query_book_content(book_name, prompt)
                if book_query_result and book_query_result.get('status') == 'success':
                    rag_context = book_query_result.get('response', '')
                    print(f" Retrieved RAG context from book: {book_name}")
            except Exception as e:
                print(f" Could not get RAG context from book: {e}")
        
        quiz_json = generate_quiz(
            prompt=prompt,
            num_questions=num_questions,
            difficulty=difficulty,
            mcq_percent=mcq_percent,
            rag_context=rag_context
        )
        return jsonify(quiz_json)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =========================================================
# NEW GRADING ROUTE
# =========================================================
@app.route("/grade_quiz", methods=["POST"])
def grade_quiz_route():
    data = request.json
    quiz_data = data.get("quiz_data")
    user_answers = data.get("user_answers")
    
    if not quiz_data or not user_answers:
        return jsonify({"error": "Missing quiz data or user answers"}), 400

    try:
        # Call the new grading function
        graded_results = grade_quiz(quiz_data, user_answers)
        return jsonify(graded_results)
    except Exception as e:
        print(f"Grading Error: {str(e)}")
        return jsonify({"error": f"Failed to grade quiz: {str(e)}"}), 500
# =========================================================

@app.route("/flashcards")
def flashcards():
    books = get_available_books()
    return render_template("flash_cards.html", active_page='flashcards', books=books)

@app.route("/slidedecks")
def slidedecks():
    books = get_available_books()
    return render_template("slide_decks.html", active_page='slidedecks', books=books)

@app.route("/generate_slide_deck", methods=["POST"])
def generate_slide_deck_route():
    try:
        data = request.json
        title = data.get("title")
        prompt = data.get("prompt")
        use_rag = bool(data.get("use_rag", False))
        book_name = data.get("book_name") if use_rag else None

        if not title:
            return jsonify({"error": "Title is required"}), 400
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        if use_rag and not book_name:
            return jsonify({"error": "book_name is required when use_rag is True"}), 400

        print(f"Title: {title}, Prompt: {prompt}, Use RAG: {use_rag}, Book Name: {book_name}")

        # Generate slide deck using the original function
        slide_deck_json = generate_slide_deck(embeddings, title, prompt, use_rag, book_name)
        print(f"SLIDE GENERATION DONE")
        return jsonify(slide_deck_json)

    except Exception as e:
        print(f"Error generating slide deck: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/manage_books")
def manage_books():
    return render_template("manage_books.html", active_page='books')

@app.route("/evaluation")
def evaluation():
    """Display agent evaluation results"""
    try:
        with open('evaluation/evaluation_report.json', 'r') as f:
            evaluation_data = json.load(f)
        return render_template("evaluation.html", evaluation=evaluation_data)
    except FileNotFoundError:
        return render_template("evaluation.html", evaluation=None, error="Evaluation report not found. Run: python3 evaluation/simple_evaluator.py")
    except Exception as e:
        return render_template("evaluation.html", evaluation=None, error=str(e))

@app.route("/evaluation/download")
def download_evaluation():
    """Download evaluation report as JSON"""
    try:
        return send_file('evaluation/evaluation_report.json', 
                        as_attachment=True,
                        download_name='learnly_evaluation_report.json',
                        mimetype='application/json')
    except FileNotFoundError:
        return jsonify({"error": "Evaluation report not found"}), 404

@app.route("/agenteval")
def agenteval():
    """Display AgentEval-style evaluation results"""
    try:
        # Try production report first
        try:
            with open('evaluation/production_agenteval_report.json', 'r') as f:
                agenteval_data = json.load(f)
        except FileNotFoundError:
            # Fall back to simple report
            with open('evaluation/agenteval_report.json', 'r') as f:
                agenteval_data = json.load(f)
        
        return render_template("agenteval.html", evaluation=agenteval_data)
    except FileNotFoundError:
        return render_template("agenteval.html", evaluation=None, error="AgentEval report not found. Run: python3 evaluation/production_agenteval.py")
    except Exception as e:
        return render_template("agenteval.html", evaluation=None, error=str(e))

@app.route('/list_books')
def list_books():
    books = get_available_books()
    return jsonify({
        'status': 'success',
        'books': books
    })

@app.route('/upload_book', methods=['POST'])
def upload_book():
    if 'book' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['book']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['BOOKS_FOLDER'], filename)
        file.save(file_path)
        
        return jsonify({
            'status': 'success',
            'message': 'Book uploaded successfully'
        })

@app.route('/upload_and_index_book', methods=['POST'])
def upload_and_index_book():
    if 'book' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['book']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        try:
            # Save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['BOOKS_FOLDER'], filename)
            file.save(file_path)
            print(f"Book saved to: {file_path}")
            
            # Extract book name without extension for indexing
            book_name = os.path.splitext(filename)[0]
            print(f"Indexing book: {book_name}")
            
            # Call the indexer function directly
            success = indexer(embeddings, book_name)
            
            if success:
                print("Indexing done")
                return jsonify({
                    'status': 'success',
                    'message': 'Book uploaded and indexed successfully!'
                })
            else:
                print("Indexing failed")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to index the book'
                }), 500
                
        except Exception as e:
            print(f"Error during upload/indexing: {str(e)}")
            # If there was an error, try to clean up the uploaded file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            return jsonify({
                'status': 'error',
                'message': f'Error during upload/indexing: {str(e)}'
            }), 500
    else:
        return jsonify({'status': 'error', 'message': 'Only PDF files are supported'}), 400

@app.route('/delete_book', methods=['POST'])
def delete_book():
    data = request.get_json()
    book_name = data.get('name')
    
    if not book_name:
        return jsonify({'status': 'error', 'message': 'No book name provided'}), 400
    
    file_path = os.path.join(app.config['BOOKS_FOLDER'], secure_filename(book_name))
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'status': 'success', 'message': 'Book deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Book not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/generate_flashcards', methods=['POST'])
def create_flashcards():
    # Get parameters from request
    data = request.get_json()
    query = data.get('query')  # User's topic/question
    book_name = data.get('book_name')  # Optional book selection
    use_rag = data.get('use_rag', False)
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Please enter a topic or question"
        }), 400
    
    # Generate flashcards with query and optional book
    # The backend will use unified search + RAG if book is provided
    flashcards = generate_flashcards(
        embeddings=embeddings,
        sample_query=query,
        class_name="General",
        subjects=["General"],
        rag=use_rag,
        book_name=book_name
    )
    
    return jsonify({
        "status": "success",
        "flashcards": flashcards
    })
    

@app.route('/query_book', methods=['POST'])
def query_book():
    data = request.get_json()
    book_name = data.get('book_name')
    query = data.get('query')
    
    if not book_name or not query:
        return jsonify({'status': 'error', 'message': 'Book name and query are required'}), 400
    
    try:
        # Use the RAG query function
        response_text = query_book_content(embeddings, book_name, query)
        print(f"Query received - Book: {book_name}, Query: {query}")
        print(f"Response: {response_text}")
        
        return jsonify({
            'status': 'success',
            'response': response_text
        })
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing query: {str(e)}'
        }), 500

def get_available_books():
    books = []
    for filename in os.listdir(app.config['BOOKS_FOLDER']):
        file_path = os.path.join(app.config['BOOKS_FOLDER'], filename)
        if os.path.isfile(file_path):
            file_type = os.path.splitext(filename)[1][1:].upper()
            books.append({
                'name': filename,
                'type': file_type
            })
    return books

@app.route('/download_slide_deck_pdf', methods=['POST'])
def download_slide_deck_pdf():
    try:
        data = request.get_json()
        if not data or 'slide_deck' not in data:
            return jsonify({'error': 'No slide deck data provided'}), 400
            
        try:
            # Generate PDF
            pdf_data = create_pdf_from_slides(data)
            if not pdf_data:
                return jsonify({'error': 'Failed to generate PDF - empty data'}), 500
                
            # Create buffer with PDF data
            buffer = io.BytesIO(pdf_data)
            buffer.seek(0)  # Move to start of buffer
            
            # Get timestamp for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create sanitized title from slide deck title
            title = data['slide_deck']['title']
            safe_title = "".join(x for x in title if x.isalnum() or x in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_').lower()
            
            # Send file with custom filename
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'{safe_title}_{timestamp}.pdf'
            )
            
        except Exception as pdf_error:
            print(f"PDF Generation Error: {str(pdf_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'PDF Generation failed: {str(pdf_error)}'}), 500
            
    except Exception as e:
        print(f"Request Processing Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Request processing failed: {str(e)}'}), 500

# ==================== AI ASSISTANT ROUTES ====================

@app.route('/ai_assistant')
def ai_assistant_page():
    return render_template('ai_assistant.html', active_page='ai_assistant')

@app.route('/ask_agent', methods=['POST'])
def ask_agent():
    try:
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Call agentic agent
        result = agentic_agent(query)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in ask_agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/get_schedules', methods=['GET'])
def get_schedules():
    """Get list of all task schedules from personnel_schedules/"""
    try:
        schedule_dir = 'personnel_schedules'
        if not os.path.exists(schedule_dir):
            return jsonify({'schedules': []})
        
        schedules = []
        for filename in os.listdir(schedule_dir):
            if filename.endswith('.csv'):
                file_path = os.path.join(schedule_dir, filename)
                file_stat = os.stat(file_path)
                schedules.append({
                    'name': filename,
                    'path': file_path,
                    'created': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M'),
                    'size': file_stat.st_size
                })
        
        return jsonify({'schedules': schedules})
        
    except Exception as e:
        print(f"Error getting schedules: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_schedule/<filename>')
def download_schedule(filename):
    """Download a task schedule CSV file"""
    try:
        schedule_dir = 'personnel_schedules'
        return send_from_directory(schedule_dir, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_chat_history', methods=['POST'])
def save_chat_history():
    """Save chat history to JSON file"""
    try:
        import json as json_module
        data = request.json
        messages = data.get('messages', [])
        
        # Create chat_history directory if it doesn't exist
        os.makedirs('chat_history', exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'chat_history/chat_{timestamp}.json'
        
        # Save to file with proper JSON formatting
        with open(filename, 'w', encoding='utf-8') as f:
            json_module.dump({'messages': messages, 'timestamp': timestamp}, f, indent=2, ensure_ascii=False)
        
        print(f" Saved chat history to {filename} ({len(messages)} messages)")
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        print(f" Error saving chat history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/load_chat_history', methods=['GET'])
def load_chat_history():
    """Load most recent chat history"""
    try:
        chat_dir = 'chat_history'
        if not os.path.exists(chat_dir):
            return jsonify({'messages': []})
        
        # Get most recent chat file
        files = [f for f in os.listdir(chat_dir) if f.endswith('.json')]
        if not files:
            return jsonify({'messages': []})
        
        files.sort(reverse=True)
        latest_file = os.path.join(chat_dir, files[0])
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e), 'messages': []}), 500

@app.route('/get_chat_sessions', methods=['GET'])
def get_chat_sessions():
    """Get list of all chat history sessions"""
    try:
        chat_dir = 'chat_history'
        if not os.path.exists(chat_dir):
            return jsonify({'sessions': []})
        
        sessions = []
        for filename in os.listdir(chat_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(chat_dir, filename)
                file_stat = os.stat(file_path)
                
                # Try to read message count
                message_count = 0
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        messages = data.get('messages', [])
                        message_count = len(messages)
                        print(f"📊 {filename}: {message_count} messages")
                except Exception as e:
                    print(f" Error reading {filename}: {e}")
                    message_count = 0
                
                sessions.append({
                    'filename': filename,
                    'created': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'size': file_stat.st_size,
                    'message_count': message_count
                })
        
        # Sort by creation time (newest first)
        sessions.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({'sessions': sessions})
    except Exception as e:
        print(f" Error in get_chat_sessions: {e}")
        return jsonify({'error': str(e), 'sessions': []}), 500

@app.route('/load_chat_session/<filename>', methods=['GET'])
def load_chat_session(filename):
    """Load a specific chat session"""
    try:
        chat_dir = 'chat_history'
        file_path = os.path.join(chat_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Session not found'}), 404
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_chat_session/<filename>', methods=['DELETE'])
def delete_chat_session(filename):
    """Delete a specific chat session"""
    try:
        chat_dir = 'chat_history'
        file_path = os.path.join(chat_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Session not found'}), 404
        
        os.remove(file_path)
        print(f"🗑️ Deleted chat session: {filename}")
        
        return jsonify({'success': True, 'message': 'Session deleted'})
    except Exception as e:
        print(f" Error deleting session: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== END AI ASSISTANT ROUTES ====================

# ==================== EXAM REVIEWER ROUTES ====================

@app.route('/exam_reviewer')
def exam_reviewer_page():
    return render_template('exam_reviewer.html', active_page='exam_reviewer')

@app.route('/upload_study_materials', methods=['POST'])
def upload_study_materials():
    """Upload study material PDF files"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'message': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'success': False, 'message': 'No files selected'}), 400
        
        # Create study materials directory
        study_dir = 'exam-prep/study_materials'
        os.makedirs(study_dir, exist_ok=True)
        
        uploaded_count = 0
        for file in files:
            if file.filename and file.filename.lower().endswith('.pdf'):
                filename = secure_filename(file.filename)
                file_path = os.path.join(study_dir, filename)
                file.save(file_path)
                uploaded_count += 1
        
        if uploaded_count > 0:
            return jsonify({
                'success': True,
                'message': f'Successfully uploaded {uploaded_count} file(s)'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No valid PDF files found'
            }), 400
            
    except Exception as e:
        print(f"Error uploading files: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/index_exam_materials', methods=['POST'])
def index_exam_materials():
    """Index uploaded study materials"""
    try:
        files_indexed = index_study_materials()
        
        if files_indexed > 0:
            return jsonify({
                'success': True,
                'message': f'Successfully indexed {files_indexed} file(s)'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No new files to index. Materials are up to date.'
            })
            
    except Exception as e:
        print(f"Error indexing materials: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/ask_exam_question', methods=['POST'])
def ask_exam_question():
    """Answer a question using indexed study materials"""
    try:
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({'status': 'error', 'message': 'No question provided'}), 400
        
        # Call review_exam with user question
        result = review_exam(None, user_question=question)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error answering question: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/review_uploaded_exam', methods=['POST'])
def review_uploaded_exam():
    """Handle exam PDF upload and trigger review"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'}), 400
        
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(EXAM_FILES_DIR, filename)
            file.save(filepath)
            
            # Trigger review pipeline
            result = review_exam(exam_pdf_path=filepath)
            return jsonify(result)
            
        return jsonify({'status': 'error', 'message': 'Invalid file type. Please upload a PDF.'}), 400
        
    except Exception as e:
        print(f"Error reviewing exam: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== END EXAM REVIEWER ROUTES ====================

# ==================== LEARNING AGENT ROUTES ====================

@app.route('/learning_agent')
def learning_agent_page():
    return render_template('learning_agent.html', active_page='learning_agent')

@app.route('/ask_learning_agent', methods=['POST'])
def ask_learning_agent():
    """Process learning agent query with optional image upload"""
    try:
        question = request.form.get('question', '')
        session_id = request.form.get('session_id')
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Save image temporarily
                filename = secure_filename(file.filename)
                upload_dir = 'temp_uploads'
                os.makedirs(upload_dir, exist_ok=True)
                image_path = os.path.join(upload_dir, filename)
                file.save(image_path)
        
        # Process query with learning agent
        result = process_learning_query(
            user_input=question,
            image_path=image_path,
            session_id=session_id
        )
        
        # Clean up temporary image
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in ask_learning_agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/get_learning_agent_history/<session_id>', methods=['GET'])
def get_learning_agent_history(session_id):
    """Get conversation history for a specific session"""
    try:
        from backend.history_manager import HistoryManager
        
        manager = HistoryManager.load_session(session_id)
        if not manager:
            return jsonify({'error': 'Session not found', 'turns': []}), 404
        
        history = manager.get_full_history()
        return jsonify({
            'session_id': session_id,
            'turns': history.get('turns', []),
            'metadata': history.get('metadata', {})
        })
        
    except Exception as e:
        print(f"Error loading history: {str(e)}")
        return jsonify({'error': str(e), 'turns': []}), 500

@app.route('/list_learning_agent_sessions', methods=['GET'])
def list_learning_agent_sessions():
    """List all learning agent sessions"""
    try:
        from backend.history_manager import HistoryManager
        import os
        
        sessions = []
        history_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history', 'learning_agent')
        
        if os.path.exists(history_dir):
            for filename in os.listdir(history_dir):
                if filename.endswith('.json'):
                    session_id = filename[:-5]
                    manager = HistoryManager.load_session(session_id)
                    if manager:
                        history = manager.get_full_history()
                        sessions.append({
                            'session_id': session_id,
                            'created_at': history.get('created_at', ''),
                            'last_updated': history.get('last_updated', ''),
                            'message_count': len(history.get('turns', [])),
                            'first_message': history['turns'][0]['user_input'][:50] if history.get('turns') else 'New Chat'
                        })
        
        # Sort by last_updated (newest first)
        sessions.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
        
        return jsonify({'sessions': sessions})
        
    except Exception as e:
        print(f"Error listing sessions: {str(e)}")
        return jsonify({'error': str(e), 'sessions': []}), 500

# ==================== END LEARNING AGENT ROUTES ====================

# ==================== STRUCTURAL EVALUATION ROUTE ====================

@app.route('/structural-eval')
def structural_eval():
    """Display structural evaluation results"""
    try:
        with open('evaluation/structural_agenteval_report.json', 'r') as f:
            eval_data = json.load(f)
        return jsonify(eval_data)
    except FileNotFoundError:
        return jsonify({
            "error": "Structural evaluation report not found",
            "message": "Run: python3 evaluation/structural_agenteval.py"
        }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/structural-eval-ui')
def structural_eval_ui():
    """Display structural evaluation UI"""
    return render_template('structural_agenteval.html')

@app.route('/backend-components-eval')
def backend_components_eval():
    """Display backend components evaluation results"""
    try:
        with open('evaluation/backend_components_report.json', 'r') as f:
            eval_data = json.load(f)
        return jsonify(eval_data)
    except FileNotFoundError:
        return jsonify({
            "error": "Backend components evaluation report not found",
            "message": "Run: python3 evaluation/backend_components_eval.py"
        }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/backend-components-eval-ui')
def backend_components_eval_ui():
    """Display backend components evaluation UI"""
    return render_template('backend_components_eval.html')

@app.route('/complete-agenteval')
def complete_agenteval():
    """Display complete agenteval results"""
    try:
        with open('evaluation/complete_agenteval_report.json', 'r') as f:
            eval_data = json.load(f)
        return jsonify(eval_data)
    except FileNotFoundError:
        return jsonify({
            "error": "Complete AgentEval report not found",
            "message": "Run: python3 evaluation/complete_agenteval.py"
        }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/complete-agenteval-ui')
def complete_agenteval_ui():
    """Display complete agenteval UI"""
    return render_template('complete_agenteval.html')

# ==================== END STRUCTURAL EVALUATION ROUTE ====================

@app.route('/logout')
def logout():
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)