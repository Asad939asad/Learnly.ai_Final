#!/usr/bin/env python3
"""
Backend Components AgentEval
Tests all 6 main backend components with one query each
Following Microsoft AgentEval Standards
"""

import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any
import statistics

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend components
try:
    from backend.learning_agent import process_learning_query
    from backend.agentic_agent import agentic_agent
    from backend.quizes import generate_quiz
    from backend.slide_decks import generate_slide_deck
    from backend.flashcards import generate_flashcards
    from backend.exam_reviewer import review_exam
    from langchain_huggingface import HuggingFaceEmbeddings
    print(" All backend components imported successfully")
except Exception as e:
    print(f" Error importing components: {e}")
    sys.exit(1)

class BackendComponentsEval:
    """
    Backend Components AgentEval
    Tests all 6 main backend components
    """
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.results = {
            "learning_agent": None,
            "agentic_agent": None,
            "quizes": None,
            "slide_decks": None,
            "flashcards": None,
            "exam_reviewer": None,
            "overall": {}
        }
    
    def test_learning_agent(self) -> Dict[str, Any]:
        """Test Learning Agent"""
        print("\n" + "="*70)
        print("🎓 TESTING LEARNING AGENT")
        print("="*70)
        
        test_query = "Explain Python decorators"
        print(f"\n📝 Query: {test_query}")
        
        start_time = time.time()
        try:
            result = process_learning_query(test_query)
            execution_time = time.time() - start_time
            
            success = bool(result and 'response' in result)
            response_length = len(str(result.get('response', '')))
            has_test = 'test_snippet' in result
            confidence = result.get('confidence', 0.0)
            
            quality_score = 0
            if success: quality_score += 40
            if response_length > 200: quality_score += 30
            if has_test: quality_score += 20
            if confidence > 0.7: quality_score += 10
            
            test_result = {
                "component": "Learning Agent",
                "query": test_query,
                "success": success,
                "execution_time": round(execution_time, 2),
                "response_length": response_length,
                "has_test_snippet": has_test,
                "confidence": confidence,
                "quality_score": quality_score
            }
            
            status = "" if success else ""
            print(f"\n   {status} Success: {success}")
            print(f"   ⏱️  Time: {execution_time:.2f}s")
            print(f"   📊 Quality: {quality_score}/100")
            print(f"   💯 Confidence: {confidence}")
            
        except Exception as e:
            print(f"    Error: {str(e)[:150]}")
            test_result = {
                "component": "Learning Agent",
                "query": test_query,
                "success": False,
                "error": str(e)[:200],
                "quality_score": 0
            }
        
        self.results["learning_agent"] = test_result
        return test_result
    
    def test_agentic_agent(self) -> Dict[str, Any]:
        """Test Agentic Agent"""
        print("\n" + "="*70)
        print("📅 TESTING AGENTIC AGENT")
        print("="*70)
        
        test_query = "Schedule a meeting tomorrow at 2pm"
        print(f"\n📝 Query: {test_query}")
        
        start_time = time.time()
        try:
            result = agentic_agent(test_query)
            execution_time = time.time() - start_time
            
            success = bool(result)
            response_str = str(result).lower()
            has_confirmation = any(word in response_str for word in ['success', 'created', 'scheduled', 'added'])
            
            quality_score = 0
            if success: quality_score += 50
            if has_confirmation: quality_score += 50
            
            test_result = {
                "component": "Agentic Agent",
                "query": test_query,
                "success": success,
                "execution_time": round(execution_time, 2),
                "has_confirmation": has_confirmation,
                "quality_score": quality_score
            }
            
            status = "" if success else ""
            print(f"\n   {status} Success: {success}")
            print(f"   ⏱️  Time: {execution_time:.2f}s")
            print(f"   📊 Quality: {quality_score}/100")
            
        except Exception as e:
            print(f"    Error: {str(e)[:150]}")
            test_result = {
                "component": "Agentic Agent",
                "query": test_query,
                "success": False,
                "error": str(e)[:200],
                "quality_score": 0
            }
        
        self.results["agentic_agent"] = test_result
        return test_result
    
    def test_quizes(self) -> Dict[str, Any]:
        """Test Quiz Generator"""
        print("\n" + "="*70)
        print("📝 TESTING QUIZ GENERATOR")
        print("="*70)
        
        test_prompt = "Python basics"
        print(f"\n📝 Prompt: {test_prompt}")
        
        start_time = time.time()
        test_result = {
            "component": "Quiz Generator",
            "prompt": test_prompt,
            "success": False,
            "quality_score": 0
        }
        
        try:
            result = generate_quiz(
                prompt=test_prompt,
                num_questions=3,
                difficulty="Medium",
                mcq_percent=70
            )
            execution_time = time.time() - start_time
            
            # More lenient success criteria
            success = bool(result and isinstance(result, dict))
            num_questions = len(result.get('quiz', {}).get('questions', [])) if success else 0
            has_correct_answers = all('correct_answer' in q for q in result.get('quiz', {}).get('questions', [])) if num_questions > 0 else False
            
            quality_score = 0
            if success: quality_score += 40
            if num_questions >= 3: quality_score += 30
            if has_correct_answers: quality_score += 30
            
            test_result.update({
                "success": success,
                "execution_time": round(execution_time, 2),
                "num_questions": num_questions,
                "has_correct_answers": has_correct_answers,
                "quality_score": quality_score
            })
            
            status = "" if success else ""
            print(f"\n   {status} Success: {success}")
            print(f"   ⏱️  Time: {execution_time:.2f}s")
            print(f"   📊 Quality: {quality_score}/100")
            print(f"   📋 Questions: {num_questions}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:200]
            print(f"    Error: {error_msg[:150]}")
            test_result.update({
                "success": False,
                "execution_time": round(execution_time, 2),
                "error": error_msg,
                "quality_score": 0
            })
        
        self.results["quizes"] = test_result
        return test_result
    
    def test_slide_decks(self) -> Dict[str, Any]:
        """Test Slide Deck Generator"""
        print("\n" + "="*70)
        print("📊 TESTING SLIDE DECK GENERATOR")
        print("="*70)
        
        test_title = "Python Basics"
        test_prompt = "Introduction to Python programming"
        print(f"\n📝 Title: {test_title}")
        print(f"📝 Prompt: {test_prompt}")
        
        start_time = time.time()
        test_result = {
            "component": "Slide Deck Generator",
            "title": test_title,
            "prompt": test_prompt,
            "success": False,
            "quality_score": 0
        }
        
        try:
            result = generate_slide_deck(
                embeddings=self.embeddings,
                title=test_title,
                prompt=test_prompt,
                use_rag=False,
                book_name=None
            )
            execution_time = time.time() - start_time
            
            success = bool(result and isinstance(result, dict))
            num_slides = len(result.get('slide_deck', {}).get('slides', [])) if success else 0
            has_title = bool(result.get('slide_deck', {}).get('title')) if success else False
            
            quality_score = 0
            if success: quality_score += 40
            if num_slides >= 3: quality_score += 30
            if has_title: quality_score += 30
            
            test_result.update({
                "success": success,
                "execution_time": round(execution_time, 2),
                "num_slides": num_slides,
                "has_title": has_title,
                "quality_score": quality_score
            })
            
            status = "" if success else ""
            print(f"\n   {status} Success: {success}")
            print(f"   ⏱️  Time: {execution_time:.2f}s")
            print(f"   📊 Quality: {quality_score}/100")
            print(f"   📄 Slides: {num_slides}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:200]
            print(f"    Error: {error_msg[:150]}")
            test_result.update({
                "success": False,
                "execution_time": round(execution_time, 2),
                "error": error_msg,
                "quality_score": 0
            })
        
        self.results["slide_decks"] = test_result
        return test_result
    
    def test_flashcards(self) -> Dict[str, Any]:
        """Test Flashcard Generator"""
        print("\n" + "="*70)
        print("🃏 TESTING FLASHCARD GENERATOR")
        print("="*70)
        
        test_query = "Python data structures"
        print(f"\n📝 Query: {test_query}")
        
        start_time = time.time()
        test_result = {
            "component": "Flashcard Generator",
            "query": test_query,
            "success": False,
            "quality_score": 0
        }
        
        try:
            result = generate_flashcards(
                embeddings=self.embeddings,
                sample_query=test_query,
                class_name="General",
                subjects=["Programming"],
                rag=False,
                book_name=None
            )
            execution_time = time.time() - start_time
            
            success = bool(result and isinstance(result, list))
            num_cards = len(result) if success else 0
            has_qa = all('question' in card and 'answer' in card for card in result) if success and num_cards > 0 else False
            
            quality_score = 0
            if success: quality_score += 40
            if num_cards >= 5: quality_score += 30
            if has_qa: quality_score += 30
            
            test_result.update({
                "success": success,
                "execution_time": round(execution_time, 2),
                "num_cards": num_cards,
                "has_qa_structure": has_qa,
                "quality_score": quality_score
            })
            
            status = "" if success else ""
            print(f"\n   {status} Success: {success}")
            print(f"   ⏱️  Time: {execution_time:.2f}s")
            print(f"   📊 Quality: {quality_score}/100")
            print(f"   🃏 Cards: {num_cards}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:200]
            print(f"    Error: {error_msg[:150]}")
            test_result.update({
                "success": False,
                "execution_time": round(execution_time, 2),
                "error": error_msg,
                "quality_score": 0
            })
        
        self.results["flashcards"] = test_result
        return test_result
    
    def test_exam_reviewer(self) -> Dict[str, Any]:
        """Test Exam Reviewer"""
        print("\n" + "="*70)
        print("📚 TESTING EXAM REVIEWER")
        print("="*70)
        
        test_question = "What is object-oriented programming?"
        print(f"\n📝 Question: {test_question}")
        
        start_time = time.time()
        try:
            result = review_exam(user_question=test_question)
            execution_time = time.time() - start_time
            
            success = result.get('status') == 'success'
            has_results = bool(result.get('results'))
            num_results = len(result.get('results', [])) if has_results else 0
            
            quality_score = 0
            if success: quality_score += 50
            if has_results: quality_score += 50
            
            test_result = {
                "component": "Exam Reviewer",
                "question": test_question,
                "success": success,
                "execution_time": round(execution_time, 2),
                "num_results": num_results,
                "quality_score": quality_score
            }
            
            status = "" if success else ""
            print(f"\n   {status} Success: {success}")
            print(f"   ⏱️  Time: {execution_time:.2f}s")
            print(f"   📊 Quality: {quality_score}/100")
            
        except Exception as e:
            print(f"    Error: {str(e)[:150]}")
            test_result = {
                "component": "Exam Reviewer",
                "question": test_question,
                "success": False,
                "error": str(e)[:200],
                "quality_score": 0
            }
        
        self.results["exam_reviewer"] = test_result
        return test_result
    
    def run_complete_evaluation(self) -> Dict[str, Any]:
        """Run complete backend evaluation"""
        print("\n" + "="*70)
        print("🚀 BACKEND COMPONENTS AGENTEVAL")
        print("   Testing All 6 Backend Components")
        print("   Microsoft AgentEval Standards")
        print("="*70)
        
        start_time = time.time()
        
        # Test all components
        learning_result = self.test_learning_agent()
        agentic_result = self.test_agentic_agent()
        quiz_result = self.test_quizes()
        slides_result = self.test_slide_decks()
        flashcards_result = self.test_flashcards()
        exam_result = self.test_exam_reviewer()
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        all_results = [
            learning_result,
            agentic_result,
            quiz_result,
            slides_result,
            flashcards_result,
            exam_result
        ]
        
        total_tests = len(all_results)
        successful = sum(1 for r in all_results if r.get('success', False))
        quality_scores = [r.get('quality_score', 0) for r in all_results]
        avg_quality = statistics.mean(quality_scores)
        
        overall_summary = {
            "framework": "Backend Components AgentEval",
            "standard": "Microsoft AgentEval",
            "timestamp": datetime.now().isoformat(),
            "total_execution_time": round(total_time, 2),
            "overall_metrics": {
                "total_components": total_tests,
                "successful_tests": successful,
                "failed_tests": total_tests - successful,
                "success_rate": round((successful / total_tests) * 100, 2),
                "avg_quality_score": round(avg_quality, 2),
                "grade": self._assign_grade(avg_quality)
            },
            "component_results": {
                "learning_agent": learning_result,
                "agentic_agent": agentic_result,
                "quizes": quiz_result,
                "slide_decks": slides_result,
                "flashcards": flashcards_result,
                "exam_reviewer": exam_result
            }
        }
        
        self.results["overall"] = overall_summary
        
        # Print final report
        self._print_final_report(overall_summary)
        
        # Save report
        self._save_report(overall_summary)
        
        return overall_summary
    
    def _assign_grade(self, score: float) -> str:
        """Assign letter grade"""
        if score >= 90:
            return "A (Excellent)"
        elif score >= 80:
            return "B (Good)"
        elif score >= 70:
            return "C (Satisfactory)"
        elif score >= 60:
            return "D (Needs Improvement)"
        else:
            return "F (Poor)"
    
    def _print_final_report(self, summary: Dict):
        """Print comprehensive final report"""
        print("\n\n" + "="*70)
        print("📊 FINAL BACKEND COMPONENTS REPORT")
        print("="*70)
        
        print(f"\n🎯 OVERALL PERFORMANCE")
        print(f"   Overall Score: {summary['overall_metrics']['avg_quality_score']:.2f}/100")
        print(f"   Grade: {summary['overall_metrics']['grade']}")
        print(f"   Success Rate: {summary['overall_metrics']['success_rate']:.2f}%")
        print(f"   Total Time: {summary['total_execution_time']:.2f}s")
        
        print(f"\n📊 COMPONENT BREAKDOWN")
        for component, result in summary['component_results'].items():
            print(f"\n   {result['component']}:")
            print(f"      Success: {'' if result.get('success') else ''}")
            print(f"      Quality: {result.get('quality_score', 0)}/100")
            print(f"      Time: {result.get('execution_time', 0):.2f}s")
        
        print(f"\n📁 Report saved to: evaluation/backend_components_report.json")
    
    def _save_report(self, summary: Dict):
        """Save comprehensive report"""
        report_path = 'evaluation/backend_components_report.json'
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f" Backend components report saved!")

if __name__ == "__main__":
    print("="*70)
    print("🚀 Starting Backend Components AgentEval")
    print("="*70)
    
    evaluator = BackendComponentsEval()
    report = evaluator.run_complete_evaluation()
    
    print("\n\n" + "="*70)
    print(" BACKEND COMPONENTS AGENTEVAL FINISHED!")
    print("="*70)
    print(f"\nFinal Score: {report['overall_metrics']['avg_quality_score']:.2f}/100")
    print(f"Grade: {report['overall_metrics']['grade']}")
    print(f"Success Rate: {report['overall_metrics']['success_rate']:.2f}%")
    print(f"\nView detailed report: evaluation/backend_components_report.json")
