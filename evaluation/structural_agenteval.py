#!/usr/bin/env python3
"""
Structural AgentEval for Learnly.AI
Non-LLM testing of project structure, components, and configurations
Following Microsoft AgentEval Standards
"""

import os
import sys
import json
import importlib
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Tuple
import traceback

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class StructuralAgentEval:
    """
    Comprehensive structural testing framework
    Tests project architecture without LLM calls
    """
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results = {
            "backend_components": [],
            "tools": [],
            "frontend": [],
            "database": [],
            "configuration": [],
            "file_structure": [],
            "overall": {}
        }
    
    # ==================== BACKEND COMPONENT TESTS ====================
    
    def test_backend_components(self) -> Dict[str, Any]:
        """Test all backend Python modules"""
        print("\n" + "="*70)
        print("🔧 TESTING BACKEND COMPONENTS")
        print("="*70)
        
        backend_modules = [
            "backend.learning_agent",
            "backend.agentic_agent",
            "backend.flashcards",
            "backend.quizes",
            "backend.slide_decks",
            "backend.manage_books",
            "backend.exam_reviewer",
            "backend.history_manager",
            "backend.database",
            "backend.query_rag"
        ]
        
        results = []
        for module_name in backend_modules:
            print(f"\n📦 Testing: {module_name}")
            result = self._test_import(module_name)
            results.append(result)
            
            status = "" if result["success"] else ""
            print(f"   {status} Import: {result['success']}")
            if not result["success"]:
                print(f"   Error: {result.get('error', 'Unknown')[:100]}")
        
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        
        summary = {
            "category": "Backend Components",
            "total_tests": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 2),
            "detailed_results": results
        }
        
        self.results["backend_components"] = summary
        
        print(f"\n📈 Backend Summary: {successful}/{total} passed ({summary['success_rate']}%)")
        return summary
    
    # ==================== TOOLS TESTS ====================
    
    def test_tools(self) -> Dict[str, Any]:
        """Test all tool modules"""
        print("\n" + "="*70)
        print("🛠️  TESTING TOOLS")
        print("="*70)
        
        tool_modules = [
            "tools.LLM_APIS",
            "tools.unified_search",
            "tools.web_search",
            "tools.ocr_tool",
            "tools.Googlecalender",
            "tools.task_scheduler",
            "tools.chunking_indexing",
            "tools.retrieve_chunks"
        ]
        
        results = []
        for module_name in tool_modules:
            print(f"\n🔨 Testing: {module_name}")
            result = self._test_import(module_name)
            results.append(result)
            
            status = "" if result["success"] else ""
            print(f"   {status} Import: {result['success']}")
            if not result["success"]:
                print(f"   Error: {result.get('error', 'Unknown')[:100]}")
        
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        
        summary = {
            "category": "Tools",
            "total_tests": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 2),
            "detailed_results": results
        }
        
        self.results["tools"] = summary
        
        print(f"\n📈 Tools Summary: {successful}/{total} passed ({summary['success_rate']}%)")
        return summary
    
    # ==================== FRONTEND TESTS ====================
    
    def test_frontend(self) -> Dict[str, Any]:
        """Test frontend templates and static files"""
        print("\n" + "="*70)
        print("🎨 TESTING FRONTEND")
        print("="*70)
        
        results = []
        
        # Test template files
        templates = [
            "templates/dashboard.html",
            "templates/ai_assistant.html",
            "templates/flashcards.html",
            "templates/quizes.html",
            "templates/slide_decks.html",
            "templates/manage_books.html",
            "templates/exam_reviewer.html"
        ]
        
        for template in templates:
            print(f"\n📄 Testing: {template}")
            result = self._test_file_exists(template)
            
            if result["success"]:
                # Check for basic HTML structure
                file_path = os.path.join(self.project_root, template)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        has_html = '<html' in content.lower() or '<!doctype' in content.lower()
                        has_body = '<body' in content.lower()
                        result["has_html_structure"] = has_html
                        result["has_body"] = has_body
                        result["file_size"] = len(content)
                        
                        print(f"    File exists")
                        print(f"   {'' if has_html else ''} HTML structure: {has_html}")
                        print(f"   {'' if has_body else ''} Body tag: {has_body}")
                        print(f"   📏 Size: {len(content)} bytes")
                except Exception as e:
                    result["error"] = str(e)
                    print(f"    Read error: {str(e)[:100]}")
            else:
                print(f"    File not found")
            
            results.append(result)
        
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        
        summary = {
            "category": "Frontend",
            "total_tests": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 2),
            "detailed_results": results
        }
        
        self.results["frontend"] = summary
        
        print(f"\n📈 Frontend Summary: {successful}/{total} passed ({summary['success_rate']}%)")
        return summary
    
    # ==================== DATABASE TESTS ====================
    
    def test_database(self) -> Dict[str, Any]:
        """Test database integrity"""
        print("\n" + "="*70)
        print("🗄️  TESTING DATABASE")
        print("="*70)
        
        results = []
        
        # Test books.db
        print(f"\n💾 Testing: books.db")
        db_path = os.path.join(self.project_root, "books.db")
        result = {
            "test": "books.db",
            "success": False,
            "exists": False,
            "readable": False,
            "has_tables": False,
            "tables": []
        }
        
        if os.path.exists(db_path):
            result["exists"] = True
            print(f"    Database file exists")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                result["tables"] = tables
                result["has_tables"] = len(tables) > 0
                result["readable"] = True
                result["success"] = True
                
                conn.close()
                
                print(f"    Database readable")
                print(f"    Tables found: {len(tables)}")
                for table in tables:
                    print(f"      - {table}")
                    
            except Exception as e:
                result["error"] = str(e)
                print(f"    Database error: {str(e)[:100]}")
        else:
            print(f"    Database file not found")
        
        results.append(result)
        
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        
        summary = {
            "category": "Database",
            "total_tests": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 2),
            "detailed_results": results
        }
        
        self.results["database"] = summary
        
        print(f"\n📈 Database Summary: {successful}/{total} passed ({summary['success_rate']}%)")
        return summary
    
    # ==================== CONFIGURATION TESTS ====================
    
    def test_configuration(self) -> Dict[str, Any]:
        """Test configuration and API keys"""
        print("\n" + "="*70)
        print("⚙️  TESTING CONFIGURATION")
        print("="*70)
        
        results = []
        
        # Test API keys configuration
        print(f"\n🔑 Testing: API Keys Configuration")
        try:
            from tools.LLM_APIS import GROQ_API_KEY, GEMINI_API_KEY
            
            result = {
                "test": "API Keys",
                "success": True,
                "groq_configured": bool(GROQ_API_KEY and len(GROQ_API_KEY) > 10),
                "gemini_configured": bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 10)
            }
            
            print(f"   {'' if result['groq_configured'] else ''} Groq API Key: {'Configured' if result['groq_configured'] else 'Missing'}")
            print(f"   {'' if result['gemini_configured'] else ''} Gemini API Key: {'Configured' if result['gemini_configured'] else 'Missing'}")
            
        except Exception as e:
            result = {
                "test": "API Keys",
                "success": False,
                "error": str(e)
            }
            print(f"    Error: {str(e)[:100]}")
        
        results.append(result)
        
        # Test required files
        print(f"\n📋 Testing: Required Files")
        required_files = [
            "app.py",
            "requirements.txt",
            "README.md"
        ]
        
        for file in required_files:
            file_result = self._test_file_exists(file)
            file_result["test"] = f"Required File: {file}"
            results.append(file_result)
            
            status = "" if file_result["success"] else ""
            print(f"   {status} {file}: {'Found' if file_result['success'] else 'Missing'}")
        
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        
        summary = {
            "category": "Configuration",
            "total_tests": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 2),
            "detailed_results": results
        }
        
        self.results["configuration"] = summary
        
        print(f"\n📈 Configuration Summary: {successful}/{total} passed ({summary['success_rate']}%)")
        return summary
    
    # ==================== FILE STRUCTURE TESTS ====================
    
    def test_file_structure(self) -> Dict[str, Any]:
        """Test project file structure"""
        print("\n" + "="*70)
        print("📁 TESTING FILE STRUCTURE")
        print("="*70)
        
        results = []
        
        # Test required directories
        required_dirs = [
            "backend",
            "tools",
            "templates",
            "evaluation",
            "chat_history",
            "books"
        ]
        
        for directory in required_dirs:
            print(f"\n📂 Testing: {directory}/")
            dir_path = os.path.join(self.project_root, directory)
            result = {
                "test": f"Directory: {directory}",
                "path": directory,
                "success": os.path.isdir(dir_path),
                "exists": os.path.exists(dir_path)
            }
            
            if result["success"]:
                # Count files in directory
                try:
                    files = os.listdir(dir_path)
                    result["file_count"] = len(files)
                    print(f"    Directory exists ({len(files)} items)")
                except Exception as e:
                    result["error"] = str(e)
                    print(f"    Cannot read directory: {str(e)[:100]}")
            else:
                print(f"    Directory not found")
            
            results.append(result)
        
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        
        summary = {
            "category": "File Structure",
            "total_tests": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 2),
            "detailed_results": results
        }
        
        self.results["file_structure"] = summary
        
        print(f"\n📈 File Structure Summary: {successful}/{total} passed ({summary['success_rate']}%)")
        return summary
    
    # ==================== HELPER METHODS ====================
    
    def _test_import(self, module_name: str) -> Dict[str, Any]:
        """Test if a module can be imported"""
        result = {
            "module": module_name,
            "success": False
        }
        
        try:
            importlib.import_module(module_name)
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
        
        return result
    
    def _test_file_exists(self, file_path: str) -> Dict[str, Any]:
        """Test if a file exists"""
        full_path = os.path.join(self.project_root, file_path)
        return {
            "file": file_path,
            "success": os.path.isfile(full_path),
            "exists": os.path.exists(full_path)
        }
    
    # ==================== MAIN ORCHESTRATOR ====================
    
    def run_complete_evaluation(self) -> Dict[str, Any]:
        """Run complete structural evaluation"""
        print("\n" + "="*70)
        print("🚀 STRUCTURAL AGENTEVAL PIPELINE")
        print("   Non-LLM Component Testing")
        print("   Microsoft AgentEval Standards")
        print("="*70)
        
        start_time = datetime.now()
        
        # Run all test categories
        backend_summary = self.test_backend_components()
        tools_summary = self.test_tools()
        frontend_summary = self.test_frontend()
        database_summary = self.test_database()
        config_summary = self.test_configuration()
        structure_summary = self.test_file_structure()
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Calculate overall metrics
        all_tests = (
            backend_summary['total_tests'] +
            tools_summary['total_tests'] +
            frontend_summary['total_tests'] +
            database_summary['total_tests'] +
            config_summary['total_tests'] +
            structure_summary['total_tests']
        )
        
        all_successful = (
            backend_summary['successful'] +
            tools_summary['successful'] +
            frontend_summary['successful'] +
            database_summary['successful'] +
            config_summary['successful'] +
            structure_summary['successful']
        )
        
        overall_success_rate = (all_successful / all_tests) * 100
        
        # Calculate weighted score
        overall_score = (
            backend_summary['success_rate'] * 0.30 +  # 30% weight
            tools_summary['success_rate'] * 0.25 +     # 25% weight
            frontend_summary['success_rate'] * 0.15 +  # 15% weight
            database_summary['success_rate'] * 0.10 +  # 10% weight
            config_summary['success_rate'] * 0.10 +    # 10% weight
            structure_summary['success_rate'] * 0.10   # 10% weight
        )
        
        overall_summary = {
            "framework": "Structural AgentEval Pipeline",
            "type": "Non-LLM Component Testing",
            "standard": "Microsoft AgentEval",
            "timestamp": datetime.now().isoformat(),
            "execution_time": round(execution_time, 2),
            "overall_metrics": {
                "total_tests": all_tests,
                "successful_tests": all_successful,
                "failed_tests": all_tests - all_successful,
                "overall_success_rate": round(overall_success_rate, 2),
                "overall_score": round(overall_score, 2),
                "grade": self._assign_grade(overall_score)
            },
            "category_results": {
                "backend_components": backend_summary,
                "tools": tools_summary,
                "frontend": frontend_summary,
                "database": database_summary,
                "configuration": config_summary,
                "file_structure": structure_summary
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
        print("📊 FINAL STRUCTURAL EVALUATION REPORT")
        print("="*70)
        
        print(f"\n🎯 OVERALL PERFORMANCE")
        print(f"   Overall Score: {summary['overall_metrics']['overall_score']:.2f}/100")
        print(f"   Grade: {summary['overall_metrics']['grade']}")
        print(f"   Success Rate: {summary['overall_metrics']['overall_success_rate']:.2f}%")
        print(f"   Execution Time: {summary['execution_time']:.2f}s")
        
        print(f"\n📊 CATEGORY BREAKDOWN")
        for category, results in summary['category_results'].items():
            print(f"\n   {results['category']}:")
            print(f"      Success Rate: {results['success_rate']}%")
            print(f"      Tests: {results['successful']}/{results['total_tests']}")
        
        print(f"\n📁 Report saved to: evaluation/structural_agenteval_report.json")
    
    def _save_report(self, summary: Dict):
        """Save comprehensive report"""
        report_path = os.path.join(self.project_root, 'evaluation/structural_agenteval_report.json')
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f" Structural evaluation report saved!")

if __name__ == "__main__":
    print("="*70)
    print("🚀 Starting Structural AgentEval Pipeline")
    print("="*70)
    
    evaluator = StructuralAgentEval()
    report = evaluator.run_complete_evaluation()
    
    print("\n\n" + "="*70)
    print(" STRUCTURAL AGENTEVAL PIPELINE FINISHED!")
    print("="*70)
    print(f"\nFinal Score: {report['overall_metrics']['overall_score']:.2f}/100")
    print(f"Grade: {report['overall_metrics']['grade']}")
    print(f"Success Rate: {report['overall_metrics']['overall_success_rate']:.2f}%")
    print(f"\nView detailed report: evaluation/structural_agenteval_report.json")
    print(f"View in browser: http://localhost:5000/structural-eval")
