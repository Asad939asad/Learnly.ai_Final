# Exam Reviewer System

An intelligent exam preparation system that uses RAG (Retrieval Augmented Generation) and multi-LLM pipeline for answering exam questions.

## Directory Structure

```
exam-prep/
├── study_materials/     # Place your study material PDFs here
├── exam_files/          # Place exam PDFs here
└── faiss_index/         # Auto-generated FAISS index (don't modify)
```

## Features

1. **RAG Indexing**: Automatically indexes study material PDFs
2. **Question Extraction**: Uses Gemini to extract questions from exam PDFs
3. **Answer Generation**: Uses GPT-4.1 with RAG context
4. **Critic Evaluation**: Uses Grok to evaluate answer relevancy
5. **Auto-Regeneration**: Regenerates answers if relevancy score ≤ 0.5

## Workflow

```
1. Upload study materials → exam-prep/study_materials/
2. Run indexing → Creates FAISS index
3. Upload exam PDF or ask question
4. System extracts questions (Gemini)
5. For each question:
   - Retrieve top 2 chunks from RAG
   - Generate answer (GPT-4.1)
   - Evaluate relevancy (Grok critic)
   - If score ≤ 0.5: Regenerate once
6. Return results
```

## Usage

### Step 1: Index Study Materials

```python
from backend.exam_reviewer import index_study_materials

# Place PDFs in exam-prep/study_materials/
index_study_materials()
```

### Step 2: Review Exam

**Option A: Review entire exam PDF**
```python
from backend.exam_reviewer import review_exam

exam_path = "exam-prep/exam_files/midterm.pdf"
results = review_exam(exam_path)
```

**Option B: Answer single question**
```python
from backend.exam_reviewer import review_exam

question = "What is quantum computing?"
results = review_exam(None, user_question=question)
```

## Response Format

```json
{
  "status": "success",
  "total_questions": 5,
  "results": [
    {
      "question_number": 1,
      "question": "What is quantum computing?",
      "answer": "Generated answer based on study materials...",
      "relevancy_score": 0.85,
      "feedback": "Answer directly addresses the question",
      "chunks_used": 2,
      "status": "success"
    }
  ]
}
```

## Relevancy Score Threshold

- **> 0.5**: Answer accepted
- **≤ 0.5**: Answer regenerated once (final attempt)

## LLM Pipeline

1. **Gemini** (Question Extraction)
   - Extracts questions from exam PDF
   - Returns structured JSON

2. **GPT-4.1** (Answer Generation)
   - Generates answers using RAG context
   - Top 2 chunks retrieved per question

3. **Grok** (Critic Evaluation)
   - Evaluates answer relevancy
   - Provides feedback and score (0.0-1.0)

## Example

```python
# Index materials
index_study_materials()

# Answer question
results = review_exam(None, user_question="Explain neural networks")

# Access results
for result in results['results']:
    print(f"Q: {result['question']}")
    print(f"A: {result['answer']}")
    print(f"Score: {result['relevancy_score']}")
```

## Notes

- Study materials must be in PDF format
- FAISS index is created automatically
- Duplicate files are skipped (hash-based)
- Maximum 2 chunks retrieved per question
- One re-generation attempt if score is low
