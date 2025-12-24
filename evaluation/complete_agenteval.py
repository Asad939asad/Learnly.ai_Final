#!/usr/bin/env python3
"""
Complete AgentEval Pipeline for Learnly.AI
Following Microsoft AgentEval Standards for Educational Agents
Tests ALL backend components with comprehensive metrics
"""

import json
import time
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import statistics

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ALL backend components
try:
    from backend.learning_agent import process_learning_query
    from backend.agentic_agent import agentic_agent  # It's a function, not a class
    from tools.unified_search import unified_search
    print(" All backend components imported successfully")
except Exception as e:
    print(f" Error importing components: {e}")
    sys.exit(1)

class ComprehensiveAgentEval:
    """
    Complete AgentEval Pipeline
    Microsoft Standard for Educational Agents
    """
    
    def __init__(self):
        self.results = {
            "learning_agent": [],
            "agentic_agent": [],
            "unified_search": [],
            "overall": {}
        }
    
    def get_comprehensive_test_suite(self) -> Dict[str, List[Dict]]:
        """
        Comprehensive test suite for all components
        Following Microsoft AgentEval standards
        """
        return {
            "learning_agent": [
                {"id": "LA-001", "query": "Explain machine learning", "expected": "educational_content"},
                {"id": "LA-002", "query": "How do neural networks work?", "expected": "technical_explanation"},
                {"id": "LA-003", "query": "Teach me Python list comprehensions", "expected": "code_examples"},
                {"id": "LA-004", "query": "What is quantum computing?", "expected": "concept_explanation"},
                {"id": "LA-005", "query": "Explain supervised vs unsupervised learning", "expected": "comparison"},
            ],
            "agentic_agent": [
                {"id": "AA-001", "query": "Schedule meeting tomorrow at 3pm", "expected": "calendar_event"},
                {"id": "AA-002", "query": "Create task to review Python docs", "expected": "task_created"},
                {"id": "AA-003", "query": "Remind me to study tomorrow", "expected": "reminder_set"},
            ],
            "unified_search": [
                {"id": "US-001", "query": "latest AI developments", "expected": "web_results"},
                {"id": "US-002", "query": "machine learning algorithms", "expected": "wiki_results"},
            ]
        }
    
    def evaluate_learning_agent(self) -> Dict[str, Any]:
        """Test Learning Agent Component"""
        print("\n" + "="*70)
        print("🎓 EVALUATING LEARNING AGENT")
        print("="*70)
        
        tests = self.get_comprehensive_test_suite()["learning_agent"]
        results = []
        
        for test in tests:
            print(f"\n📝 Test {test['id']}: {test['query']}")
            start_time = time.time()
            
            try:
                result = process_learning_query(test['query'])
                execution_time = time.time() - start_time
                
                # Evaluate response quality
                success = bool(result and 'response' in result)
                response_length = len(str(result.get('response', '')))
                has_test = 'test_snippet' in result
                
                quality_score = 0
                if success: quality_score += 40
                if response_length > 200: quality_score += 30
                if has_test: quality_score += 30
                
                test_result = {
                    "test_id": test['id'],
                    "query": test['query'],
                    "success": success,
                    "execution_time": round(execution_time, 2),
                    "response_length": response_length,
                    "has_test_snippet": has_test,
                    "quality_score": quality_score
                }
                
                results.append(test_result)
                
                status = "" if success else ""
                print(f"   {status} Success: {success}")
                print(f"   ⏱️  Time: {execution_time:.2f}s")
                print(f"   📊 Quality: {quality_score}/100")
                
            except Exception as e:
                print(f"    Error: {str(e)[:100]}")
                results.append({
                    "test_id": test['id'],
                    "query": test['query'],
                    "success": False,
                    "error": str(e)
                })
        
        # Calculate metrics
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        avg_time = statistics.mean([r.get('execution_time', 0) for r in results if 'execution_time' in r])
        avg_quality = statistics.mean([r.get('quality_score', 0) for r in results if 'quality_score' in r])
        
        summary = {
            "component": "Learning Agent",
            "total_tests": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 2),
            "avg_execution_time": round(avg_time, 2),
            "avg_quality_score": round(avg_quality, 2),
            "detailed_results": results
        }
        
        self.results["learning_agent"] = summary
        
        print(f"\n📈 Learning Agent Summary:")
        print(f"   Success Rate: {summary['success_rate']}%")
        print(f"   Avg Quality: {summary['avg_quality_score']}/100")
        print(f"   Avg Time: {summary['avg_execution_time']}s")
        
        return summary
    
    def evaluate_agentic_agent(self) -> Dict[str, Any]:
        """Test Agentic Agent Component"""
        print("\n" + "="*70)
        print("📅 EVALUATING AGENTIC AGENT")
        print("="*70)
        
        tests = self.get_comprehensive_test_suite()["agentic_agent"]
        results = []
        
        for test in tests:
            print(f"\n📝 Test {test['id']}: {test['query']}")
            start_time = time.time()
            
            try:
                result = agentic_agent(test['query'])  # Call function directly
                execution_time = time.time() - start_time
                
                # Evaluate response
                success = bool(result)
                response_str = str(result).lower()
                has_confirmation = any(word in response_str for word in ['success', 'created', 'scheduled', 'added'])
                
                quality_score = 0
                if success: quality_score += 50
                if has_confirmation: quality_score += 50
                
                test_result = {
                    "test_id": test['id'],
                    "query": test['query'],
                    "success": success,
                    "execution_time": round(execution_time, 2),
                    "has_confirmation": has_confirmation,
                    "quality_score": quality_score
                }
                
                results.append(test_result)
                
                status = "" if success else ""
                print(f"   {status} Success: {success}")
                print(f"   ⏱️  Time: {execution_time:.2f}s")
                print(f"   📊 Quality: {quality_score}/100")
                
            except Exception as e:
                print(f"    Error: {str(e)[:100]}")
                results.append({
                    "test_id": test['id'],
                    "query": test['query'],
                    "success": False,
                    "error": str(e)
                })
        
        # Calculate metrics
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        avg_time = statistics.mean([r.get('execution_time', 0) for r in results if 'execution_time' in r])
        avg_quality = statistics.mean([r.get('quality_score', 0) for r in results if 'quality_score' in r])
        
        summary = {
            "component": "Agentic Agent",
            "total_tests": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 2),
            "avg_execution_time": round(avg_time, 2),
            "avg_quality_score": round(avg_quality, 2),
            "detailed_results": results
        }
        
        self.results["agentic_agent"] = summary
        
        print(f"\n📈 Agentic Agent Summary:")
        print(f"   Success Rate: {summary['success_rate']}%")
        print(f"   Avg Quality: {summary['avg_quality_score']}/100")
        print(f"   Avg Time: {summary['avg_execution_time']}s")
        
        return summary
    
    def evaluate_unified_search(self) -> Dict[str, Any]:
        """Test Unified Search Component"""
        print("\n" + "="*70)
        print("🔍 EVALUATING UNIFIED SEARCH")
        print("="*70)
        
        tests = self.get_comprehensive_test_suite()["unified_search"]
        results = []
        
        for test in tests:
            print(f"\n📝 Test {test['id']}: {test['query']}")
            start_time = time.time()
            
            try:
                result = unified_search(test['query'], max_chars_per_source=500)
                execution_time = time.time() - start_time
                
                # Evaluate response
                success = result.get('status') == 'success'
                has_web = bool(result.get('web_search'))
                has_wiki = bool(result.get('wikipedia_search'))
                total_chars = result.get('total_chars', 0)
                
                quality_score = 0
                if success: quality_score += 40
                if has_web: quality_score += 30
                if has_wiki: quality_score += 30
                
                test_result = {
                    "test_id": test['id'],
                    "query": test['query'],
                    "success": success,
                    "execution_time": round(execution_time, 2),
                    "has_web_results": has_web,
                    "has_wiki_results": has_wiki,
                    "total_chars": total_chars,
                    "quality_score": quality_score
                }
                
                results.append(test_result)
                
                status = "" if success else ""
                print(f"   {status} Success: {success}")
                print(f"   ⏱️  Time: {execution_time:.2f}s")
                print(f"   📊 Quality: {quality_score}/100")
                print(f"   📝 Retrieved: {total_chars} chars")
                
            except Exception as e:
                print(f"    Error: {str(e)[:100]}")
                results.append({
                    "test_id": test['id'],
                    "query": test['query'],
                    "success": False,
                    "error": str(e)
                })
        
        # Calculate metrics
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        avg_time = statistics.mean([r.get('execution_time', 0) for r in results if 'execution_time' in r])
        avg_quality = statistics.mean([r.get('quality_score', 0) for r in results if 'quality_score' in r])
        
        summary = {
            "component": "Unified Search",
            "total_tests": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 2),
            "avg_execution_time": round(avg_time, 2),
            "avg_quality_score": round(avg_quality, 2),
            "detailed_results": results
        }
        
        self.results["unified_search"] = summary
        
        print(f"\n📈 Unified Search Summary:")
        print(f"   Success Rate: {summary['success_rate']}%")
        print(f"   Avg Quality: {summary['avg_quality_score']}/100")
        print(f"   Avg Time: {summary['avg_execution_time']}s")
        
        return summary
    
    def run_complete_evaluation(self):
        """Run complete evaluation pipeline"""
        print("\n" + "="*70)
        print("🚀 COMPLETE AGENTEVAL PIPELINE")
        print("   Microsoft Standard for Educational Agents")
        print("   Testing ALL Backend Components")
        print("="*70)
        
        start_time = time.time()
        
        # Test all components
        learning_summary = self.evaluate_learning_agent()
        agentic_summary = self.evaluate_agentic_agent()
        search_summary = self.evaluate_unified_search()
        
        total_time = time.time() - start_time
        
        # Calculate overall metrics
        all_tests = (
            learning_summary['total_tests'] +
            agentic_summary['total_tests'] +
            search_summary['total_tests']
        )
        all_successful = (
            learning_summary['successful'] +
            agentic_summary['successful'] +
            search_summary['successful']
        )
        
        overall_success_rate = (all_successful / all_tests) * 100
        
        # Weighted overall score
        overall_score = (
            learning_summary['avg_quality_score'] * 0.50 +  # 50% weight
            agentic_summary['avg_quality_score'] * 0.30 +   # 30% weight
            search_summary['avg_quality_score'] * 0.20      # 20% weight
        )
        
        overall_summary = {
            "framework": "Complete AgentEval Pipeline",
            "standard": "Microsoft Educational Agents",
            "timestamp": datetime.now().isoformat(),
            "total_execution_time": round(total_time, 2),
            "overall_metrics": {
                "total_tests": all_tests,
                "successful_tests": all_successful,
                "failed_tests": all_tests - all_successful,
                "overall_success_rate": round(overall_success_rate, 2),
                "overall_quality_score": round(overall_score, 2),
                "grade": self._assign_grade(overall_score)
            },
            "component_results": {
                "learning_agent": learning_summary,
                "agentic_agent": agentic_summary,
                "unified_search": search_summary
            }
        }
        
        self.results["overall"] = overall_summary
        
        # Print final summary
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
        print("📊 FINAL AGENTEVAL REPORT")
        print("="*70)
        
        print(f"\n🎯 OVERALL PERFORMANCE")
        print(f"   Overall Score: {summary['overall_metrics']['overall_quality_score']:.2f}/100")
        print(f"   Grade: {summary['overall_metrics']['grade']}")
        print(f"   Success Rate: {summary['overall_metrics']['overall_success_rate']:.2f}%")
        print(f"   Total Time: {summary['total_execution_time']:.2f}s")
        
        print(f"\n📊 COMPONENT BREAKDOWN")
        for component, results in summary['component_results'].items():
            print(f"\n   {results['component']}:")
            print(f"      Success Rate: {results['success_rate']}%")
            print(f"      Quality Score: {results['avg_quality_score']}/100")
            print(f"      Avg Time: {results['avg_execution_time']}s")
            print(f"      Tests: {results['successful']}/{results['total_tests']}")
        
        print(f"\n📁 Report saved to: evaluation/complete_agenteval_report.json")
    
    def _save_report(self, summary: Dict):
        """Save comprehensive report"""
        report_path = 'evaluation/complete_agenteval_report.json'
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f" Complete report saved!")

if __name__ == "__main__":
    print("="*70)
    print("🚀 Starting Complete AgentEval Pipeline")
    print("="*70)
    
    evaluator = ComprehensiveAgentEval()
    report = evaluator.run_complete_evaluation()
    
    print("\n\n" + "="*70)
    print(" COMPLETE AGENTEVAL PIPELINE FINISHED!")
    print("="*70)
    print(f"\nFinal Score: {report['overall_metrics']['overall_quality_score']:.2f}/100")
    print(f"Grade: {report['overall_metrics']['grade']}")
    print(f"Success Rate: {report['overall_metrics']['overall_success_rate']:.2f}%")
    print(f"\nView detailed report: evaluation/complete_agenteval_report.json")
    print(f"View in browser: http://localhost:5000/agenteval")
