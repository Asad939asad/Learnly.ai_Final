"""
History Manager for Adaptive Learning Agent
Handles conversation persistence and context management
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

# History storage directory
HISTORY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "chat_history",
    "learning_agent"
)

# Ensure directory exists
os.makedirs(HISTORY_DIR, exist_ok=True)


class HistoryManager:
    """Manages conversation history for the learning agent"""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize history manager
        
        Args:
            session_id: Optional existing session ID, creates new if None
        """
        self.session_id = session_id or self.create_session()
        self.session_file = os.path.join(HISTORY_DIR, f"{self.session_id}.json")
        self.history = self._load_session()
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new session
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            str: New session ID
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "turns": [],
            "metadata": {
                "total_turns": 0,
                "tools_used": [],
                "topics_discussed": []
            }
        }
        
        session_file = os.path.join(HISTORY_DIR, f"{session_id}.json")
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return session_id
    
    def _load_session(self) -> Dict:
        """Load session data from file"""
        if os.path.exists(self.session_file):
            with open(self.session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create new session if file doesn't exist
            return {
                "session_id": self.session_id,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "turns": [],
                "metadata": {
                    "total_turns": 0,
                    "tools_used": [],
                    "topics_discussed": []
                }
            }
    
    def _save_session(self):
        """Save session data to file"""
        self.history["last_updated"] = datetime.now().isoformat()
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def save_turn(
        self,
        user_input: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save a conversation turn
        
        Args:
            user_input: User's input text
            agent_response: Agent's response
            metadata: Optional metadata (tools used, confidence, etc.)
        """
        turn = {
            "turn_id": len(self.history["turns"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "agent_response": agent_response,
            "metadata": metadata or {}
        }
        
        self.history["turns"].append(turn)
        self.history["metadata"]["total_turns"] = len(self.history["turns"])
        
        # Update tools used
        if metadata and "tools_used" in metadata:
            for tool in metadata["tools_used"]:
                if tool not in self.history["metadata"]["tools_used"]:
                    self.history["metadata"]["tools_used"].append(tool)
        
        self._save_session()
    
    def get_recent_context(self, num_turns: int = 5) -> List[Dict]:
        """
        Get recent conversation turns for context
        
        Args:
            num_turns: Number of recent turns to retrieve
            
        Returns:
            List of recent conversation turns
        """
        return self.history["turns"][-num_turns:] if self.history["turns"] else []
    
    def get_full_history(self) -> Dict:
        """Get complete session history"""
        return self.history
    
    def summarize_history(self, max_chars: int = 500) -> str:
        """
        Create a summary of conversation history
        
        Args:
            max_chars: Maximum characters for summary
            
        Returns:
            str: Summary of conversation
        """
        if not self.history["turns"]:
            return "No previous conversation."
        
        recent_turns = self.get_recent_context(3)
        
        summary_parts = []
        for turn in recent_turns:
            user_text = turn["user_input"][:100]
            agent_text = turn["agent_response"][:100]
            summary_parts.append(f"User: {user_text}...")
            summary_parts.append(f"Agent: {agent_text}...")
        
        summary = "\n".join(summary_parts)
        return summary[:max_chars]
    
    def get_conversation_for_llm(self, num_turns: int = 3) -> List[Dict[str, str]]:
        """
        Format conversation history for LLM context
        
        Args:
            num_turns: Number of recent turns to include
            
        Returns:
            List of dicts with 'role' and 'content' for LLM
        """
        recent_turns = self.get_recent_context(num_turns)
        
        formatted = []
        for turn in recent_turns:
            formatted.append({
                "role": "user",
                "content": turn["user_input"]
            })
            formatted.append({
                "role": "model",
                "content": turn["agent_response"]
            })
        
        return formatted
    
    @staticmethod
    def list_sessions() -> List[str]:
        """List all available session IDs"""
        if not os.path.exists(HISTORY_DIR):
            return []
        
        sessions = []
        for filename in os.listdir(HISTORY_DIR):
            if filename.endswith('.json'):
                sessions.append(filename[:-5])  # Remove .json extension
        
        return sorted(sessions, reverse=True)  # Most recent first
    
    @staticmethod
    def load_session(session_id: str) -> Optional['HistoryManager']:
        """
        Load an existing session
        
        Args:
            session_id: Session ID to load
            
        Returns:
            HistoryManager instance or None if not found
        """
        session_file = os.path.join(HISTORY_DIR, f"{session_id}.json")
        if os.path.exists(session_file):
            return HistoryManager(session_id=session_id)
        return None
    
    def clear_history(self):
        """Clear all turns from current session"""
        self.history["turns"] = []
        self.history["metadata"]["total_turns"] = 0
        self._save_session()


# ==================== CONVENIENCE FUNCTIONS ====================

def create_new_session(user_id: Optional[str] = None) -> HistoryManager:
    """Create a new session and return manager"""
    return HistoryManager()

def load_existing_session(session_id: str) -> Optional[HistoryManager]:
    """Load an existing session"""
    return HistoryManager.load_session(session_id)


# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Test the history manager
    print("=" * 70)
    print("🧪 Testing History Manager")
    print("=" * 70)
    
    # Create new session
    print("\n1. Creating new session...")
    manager = create_new_session()
    print(f"   Session ID: {manager.session_id}")
    
    # Save some turns
    print("\n2. Saving conversation turns...")
    manager.save_turn(
        user_input="What is photosynthesis?",
        agent_response="Photosynthesis is the process by which plants convert light energy into chemical energy...",
        metadata={"tools_used": ["unified_search"], "confidence": 0.95}
    )
    
    manager.save_turn(
        user_input="How does it work in C4 plants?",
        agent_response="C4 plants have a specialized mechanism to concentrate CO2...",
        metadata={"tools_used": ["unified_search"], "confidence": 0.92}
    )
    
    print(f"   Saved {len(manager.history['turns'])} turns")
    
    # Get recent context
    print("\n3. Retrieving recent context...")
    context = manager.get_recent_context(2)
    for i, turn in enumerate(context, 1):
        print(f"   Turn {i}: {turn['user_input'][:50]}...")
    
    # Get summary
    print("\n4. Generating summary...")
    summary = manager.summarize_history()
    print(f"   {summary[:100]}...")
    
    # List all sessions
    print("\n5. Listing all sessions...")
    sessions = HistoryManager.list_sessions()
    print(f"   Found {len(sessions)} session(s)")
    for session in sessions[:3]:
        print(f"   - {session}")
    
    print("\n" + "=" * 70)
    print(" History Manager Test Complete!")
    print("=" * 70)
