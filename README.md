# Learnly.AI - Intelligent Educational Platform

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![AgentEval](https://img.shields.io/badge/AgentEval-98.29%2F100-brightgreen.svg)](evaluation/)

An AI-powered educational platform featuring intelligent tutoring, content generation, and comprehensive evaluation systems. Built with Groq LLaMA 3.3 and Google Gemini 2.5.

## 🌟 Features

### Core Components

- **🎓 Learning Agent**: Adaptive tutoring system with two-phase processing (planning + execution)
- **🤖 Agentic Agent**: Task scheduling and calendar management with Google Calendar integration
- **📝 Quiz Generator**: Dynamic quiz creation with automated grading
- **📊 Slide Deck Generator**: Automated presentation creation with PDF export
- **🃏 Flashcard Generator**: Intelligent flashcard creation for effective memorization
- **📚 Exam Reviewer**: Comprehensive exam preparation with PDF processing

### Advanced Features

- **RAG System**: Retrieval-Augmented Generation with ChromaDB vector storage
- **Unified Search**: Combined web and Wikipedia search integration
- **OCR Support**: Image text extraction for visual learning materials
- **Session Management**: Persistent conversation history
- **Multi-API Support**: Groq and Gemini API integration

## 📊 Evaluation Results

Learnly.AI has been rigorously tested using Microsoft AgentEval standards:

| Framework | Score | Success Rate | Status |
|-----------|-------|--------------|--------|
| **Backend Components** | 100/100 | 100% (6/6) | ✅ Excellent |
| **Complete AgentEval** | 97/100 | 100% (10/10) | ✅ Excellent |
| **Structural Testing** | 97.86/100 | 97.22% (35/36) | ✅ Excellent |
| **Overall** | **98.29/100** | **98.08%** | ✅ **Production Ready** |

View detailed reports:
- [Backend Components Evaluation](evaluation/backend_components_report.json)
- [Complete AgentEval Report](evaluation/complete_agenteval_report.json)
- [Structural Testing Report](evaluation/structural_agenteval_report.json)
- [Complete Evaluation Documentation](evaluation/EVALUATION_COMPLETE.md)

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager
- API keys for Groq and Gemini

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Asad939asad/Learnly.ai_Final.git
cd Learnly.ai_Final
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
export GEMINI_API_KEY="your_gemini_api_key"
export GEMINI_LEARNING_API_KEY="your_gemini_learning_key"
export GROQ_API_KEY="your_groq_api_key"
export GOOGLE_API_KEY="your_google_api_key"
export GOOGLE_CSE_ID="your_custom_search_engine_id"
export GITHUB_TOKEN="your_github_token"  # Optional, for GPT-4.1
```

4. **Run the application**
```bash
python3 app.py
```

5. **Access the platform**
```
http://localhost:5000
```

## 📁 Project Structure

```
Learnly.AI/
├── backend/                    # Backend components
│   ├── learning_agent.py      # Adaptive learning system
│   ├── agentic_agent.py       # Task & calendar management
│   ├── quizes.py              # Quiz generation
│   ├── slide_decks.py         # Presentation creation
│   ├── flashcards.py          # Flashcard generation
│   ├── exam_reviewer.py       # Exam preparation
│   └── ...
├── tools/                      # Utility tools
│   ├── LLM_APIS.py            # API integrations
│   ├── unified_search.py      # Search functionality
│   ├── web_search.py          # Web scraping
│   ├── ocr_tool.py            # Image text extraction
│   └── ...
├── templates/                  # HTML templates
│   ├── dashboard.html         # Main dashboard
│   ├── ai_assistant.html      # Chat interface
│   ├── learning_agent.html    # Learning interface
│   └── ...
├── evaluation/                 # Evaluation scripts
│   ├── backend_components_eval.py
│   ├── complete_agenteval.py
│   ├── structural_agenteval.py
│   └── ...
├── app.py                      # Main Flask application
├── PROJECT_REPORT.md          # Comprehensive project documentation
└── README.md                   # This file
```

## 🎯 Usage

### Learning Agent
```python
from backend.learning_agent import process_learning_query

result = process_learning_query(
    user_input="Explain Python decorators",
    session_id="your_session_id"
)
```

### Quiz Generation
```python
from backend.quizes import generate_quiz

quiz = generate_quiz(
    prompt="Python basics",
    num_questions=5,
    difficulty="Medium",
    mcq_percent=70
)
```

### Slide Deck Creation
```python
from backend.slide_decks import generate_slide_deck

deck = generate_slide_deck(
    embeddings=embeddings,
    title="Python Basics",
    prompt="Introduction to Python programming",
    use_rag=False,
    book_name=None
)
```

## 🔌 API Endpoints

### Evaluation Endpoints
- `GET /backend-components-eval-ui` - Backend components evaluation UI
- `GET /complete-agenteval-ui` - Complete AgentEval UI
- `GET /structural-eval-ui` - Structural evaluation UI

### Core Endpoints
- `GET /` - Dashboard
- `GET /learning_agent` - Learning interface
- `POST /ask_learning_agent` - Submit learning query
- `GET /ai_assistant` - Chat interface
- `POST /ask_agent` - Submit chat message

### Content Generation
- `POST /generate_quiz` - Generate quiz
- `POST /generate_slide_deck` - Generate presentation
- `POST /generate_flashcards` - Generate flashcards

### Book Management
- `GET /manage_books` - Book management interface
- `POST /upload_and_index_book` - Upload and index book
- `POST /query_book` - Query book content

## 🧪 Running Evaluations

### Backend Components Evaluation
```bash
python3 evaluation/backend_components_eval.py
```

### Complete AgentEval
```bash
python3 evaluation/complete_agenteval.py
```

### Structural Testing
```bash
python3 evaluation/structural_agenteval.py
```

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 2.3+
- **AI Models**: Groq LLaMA 3.3 70B, Google Gemini 2.5 Flash
- **Database**: SQLite3
- **Vector Store**: ChromaDB
- **Embeddings**: HuggingFace Sentence Transformers

### Frontend
- **Templates**: Jinja2
- **Styling**: Custom CSS
- **JavaScript**: Vanilla JS

### Tools & APIs
- **Search**: Google Custom Search API
- **OCR**: Tesseract
- **Calendar**: Google Calendar API
- **PDF**: ReportLab
- **Web Scraping**: Playwright, BeautifulSoup4

## 📊 Performance Metrics

| Component | Average Time | Success Rate |
|-----------|-------------|--------------|
| Learning Agent | 4.54s | 100% |
| Agentic Agent | 9.35s | 100% |
| Quiz Generator | 12.54s | 100% |
| Slide Decks | 27.48s | 100% |
| Flashcards | 18.37s | 100% |
| Exam Reviewer | 25.30s | 100% |

## 🔒 Security

- All API keys are loaded from environment variables
- No hardcoded secrets in the codebase
- GitHub secret scanning enabled
- Secure session management
- Input validation and sanitization

## 📝 Documentation

- [Complete Project Report](PROJECT_REPORT.md) - Comprehensive documentation
- [Evaluation Complete](evaluation/EVALUATION_COMPLETE.md) - Detailed evaluation results
- [Environment Setup](ENV_SETUP.md) - Configuration guide

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Microsoft AgentEval framework for evaluation standards
- Groq for LLaMA 3.3 API access
- Google for Gemini API and Calendar integration
- HuggingFace for embeddings and transformers

## 📧 Contact

**Project Maintainer**: Asad Irfan  
**Repository**: [https://github.com/Asad939asad/Learnly.ai_Final](https://github.com/Asad939asad/Learnly.ai_Final)

## 🌟 Star History

If you find this project useful, please consider giving it a star ⭐

---

**Built with ❤️ using AI and modern web technologies**
