"""
CLI Interface for Adaptive Learning Agent
Interactive command-line interface for testing
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.learning_agent import process_learning_query
from backend.history_manager import HistoryManager


def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 70)
    print("🎓 ADAPTIVE LEARNING AGENT - CLI")
    print("=" * 70)
    print("Commands:")
    print("  - Type your question to get help")
    print("  - 'upload <path>' to process an image")
    print("  - 'history' to view conversation history")
    print("  - 'new' to start a new session")
    print("  - 'sessions' to list all sessions")
    print("  - 'load <session_id>' to load a previous session")
    print("  - 'debug' to toggle debug mode")
    print("  - 'exit' or 'quit' to exit")
    print("=" * 70 + "\n")


def print_response(result):
    """Print formatted response"""
    print("\n" + "─" * 70)
    print("📚 LEARNING RESPONSE")
    print("─" * 70)
    print(f"\n{result['response']}\n")
    
    if result.get('test_snippet'):
        print("─" * 70)
        print("🧪 TEST YOUR UNDERSTANDING")
        print("─" * 70)
        print(f"\n{result['test_snippet']}\n")
    
    if result.get('key_concepts'):
        print("─" * 70)
        print("🔑 KEY CONCEPTS")
        print("─" * 70)
        for concept in result['key_concepts']:
            print(f"  • {concept}")
        print()
    
    if result.get('follow_up_suggestions'):
        print("─" * 70)
        print("💡 FOLLOW-UP SUGGESTIONS")
        print("─" * 70)
        for i, suggestion in enumerate(result['follow_up_suggestions'], 1):
            print(f"  {i}. {suggestion}")
        print()
    
    print("─" * 70)
    print(f"Confidence: {result.get('confidence', 0.0):.0%} | Session: {result.get('session_id', 'N/A')}")
    print("─" * 70 + "\n")


def print_debug_info(result):
    """Print debug information"""
    print("\n" + "🔧 DEBUG INFO " + "─" * 55)
    metadata = result.get('metadata', {})
    print(f"Tools used: {', '.join(metadata.get('tools_used', []))}")
    print(f"Search performed: {metadata.get('search_performed', False)}")
    print(f"Turn number: {metadata.get('turn_number', 0)}")
    
    if metadata.get('plan'):
        print(f"\nPhase 1 Plan:")
        plan = metadata['plan']
        print(f"  - Learning goal: {plan.get('learning_goal', 'N/A')}")
        print(f"  - Action plan: {plan.get('action_plan', 'N/A')}")
        print(f"  - Reasoning: {plan.get('reasoning', 'N/A')}")
    
    print("─" * 70 + "\n")


def show_history(session_id):
    """Show conversation history"""
    manager = HistoryManager.load_session(session_id)
    if not manager:
        print(" Session not found")
        return
    
    history = manager.get_full_history()
    turns = history.get('turns', [])
    
    if not turns:
        print("📝 No conversation history yet")
        return
    
    print("\n" + "=" * 70)
    print(f"📜 CONVERSATION HISTORY - {session_id}")
    print("=" * 70)
    
    for turn in turns:
        print(f"\n[Turn {turn['turn_id']}] {turn['timestamp']}")
        print(f"👤 User: {turn['user_input']}")
        print(f"🤖 Agent: {turn['agent_response'][:200]}...")
        if turn.get('metadata', {}).get('tools_used'):
            print(f"   Tools: {', '.join(turn['metadata']['tools_used'])}")
    
    print("\n" + "=" * 70 + "\n")


def list_sessions():
    """List all available sessions"""
    sessions = HistoryManager.list_sessions()
    
    if not sessions:
        print("📝 No previous sessions found")
        return
    
    print("\n" + "=" * 70)
    print("📋 AVAILABLE SESSIONS")
    print("=" * 70)
    
    for i, session_id in enumerate(sessions[:10], 1):  # Show last 10
        manager = HistoryManager.load_session(session_id)
        if manager:
            history = manager.get_full_history()
            num_turns = len(history.get('turns', []))
            created = history.get('created_at', 'Unknown')
            print(f"{i}. {session_id}")
            print(f"   Created: {created} | Turns: {num_turns}")
    
    print("=" * 70 + "\n")


def main():
    """Main CLI loop"""
    print_banner()
    
    # Initialize session
    current_session = None
    debug_mode = False
    
    print("🆕 Starting new session...")
    manager = HistoryManager()
    current_session = manager.session_id
    print(f"📝 Session ID: {current_session}\n")
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['exit', 'quit']:
                print("\nAsad Goodbye! Your session has been saved.")
                print(f"Session ID: {current_session}\n")
                break
            
            elif user_input.lower() == 'new':
                manager = HistoryManager()
                current_session = manager.session_id
                print(f"\n🆕 New session created: {current_session}\n")
                continue
            
            elif user_input.lower() == 'history':
                show_history(current_session)
                continue
            
            elif user_input.lower() == 'sessions':
                list_sessions()
                continue
            
            elif user_input.lower().startswith('load '):
                session_id = user_input[5:].strip()
                loaded = HistoryManager.load_session(session_id)
                if loaded:
                    current_session = session_id
                    print(f"\n Loaded session: {current_session}\n")
                else:
                    print(f"\n Session not found: {session_id}\n")
                continue
            
            elif user_input.lower() == 'debug':
                debug_mode = not debug_mode
                print(f"\n🔧 Debug mode: {'ON' if debug_mode else 'OFF'}\n")
                continue
            
            elif user_input.lower().startswith('upload '):
                image_path = user_input[7:].strip()
                
                # Remove quotes if present
                image_path = image_path.strip('"\'')
                
                if not os.path.exists(image_path):
                    print(f"\n Image not found: {image_path}\n")
                    continue
                
                print("\n🤖 Processing your image and question...")
                follow_up = input("What would you like to know about this image? ").strip()
                
                result = process_learning_query(
                    user_input=follow_up or "Explain what you see in this image",
                    image_path=image_path,
                    session_id=current_session
                )
                
                print_response(result)
                if debug_mode:
                    print_debug_info(result)
                
                continue
            
            # Process regular query
            print("\n🤖 Thinking...")
            result = process_learning_query(
                user_input=user_input,
                session_id=current_session
            )
            
            print_response(result)
            if debug_mode:
                print_debug_info(result)
        
        except KeyboardInterrupt:
            print("\n\nAsad Goodbye! Your session has been saved.")
            print(f"Session ID: {current_session}\n")
            break
        
        except Exception as e:
            print(f"\n Error: {e}\n")
            if debug_mode:
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
